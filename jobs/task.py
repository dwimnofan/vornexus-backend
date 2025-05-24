import asyncio
import time
import hashlib
from urllib.parse import quote_plus
from crawl4ai import AsyncWebCrawler
from core.ai.crawl import client, JobList, Jobs
from huey.contrib.djhuey import periodic_task
from huey import crontab
from asgiref.sync import sync_to_async
from datetime import datetime
from core.ai.chromadb import chroma_client, embedding_function
from jobs.utils import save_job, sanitize_collection_name

print(time.tzname)        # Nama timezone lokal (misal: ('WIB', 'WIB'))
print(time.timezone)      # Offset dalam detik dari UTC (negatif kalau di depan UTC)




MAX_JOBS_PER_KEYWORD = 15  # max job per kategori

CATEGORY_KEYWORDS = {
    "Teknologi ": [
        "software engineer", 
        # "software engineer", "devops engineer", "data scientist",
        # "cybersecurity analyst", "qa engineer", "ui/ux designer", "cloud engineer",
        # "backend", "frontend", "full stack", "mobile developer", "machine learning", "data analyst", "qa tester"
    ],
    "Bisnis dan Manajemen": [
        "digital marketing",
    #     "business analyst", "project manager", "product manager",
    #     "hr specialist", "recruiter", "marketing specialist", "digital marketing",
    #     "finance analyst", "accountant"
    ],
    # "Kreatif": [
    #     "graphic designer", "ui designer", "content writer", "copywriter",
    #     "video editor", "social media specialist", "brand strategist"
    # ],
    # "Manufaktur": [
    #     "mechanical engineer", "industrial engineer", "supply chain analyst",
    #     "procurement specialist", "quality assurance engineer", "qa manufaktur", "qa logistik"
    # ]
}


@periodic_task(crontab(hour=10, minute=30), name="crawl_jobs") # 17-30 dikurangi 7 jam
def crawl_jobs():
    try:
        asyncio.run(crawl_jobs_async())
    except Exception as e:
        print(f"Error running crawl_jobs: {e}")


def generate_md5_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

async def fetch_with_retry(crawler, url, retries=2):
    for attempt in range(retries + 1):
        try:
            return await crawler.arun(url)
        except Exception as e:
            if attempt == retries:
                raise
            print(f"🔁 Retry {attempt+1} for {url} due to error: {e}")
            await asyncio.sleep(2)  # jeda sebelum retry


async def crawl_jobs_by_keywords(crawler, category, keywords, max_jobs_per_keyword):
    print(f"\n📁 Crawling category: {category.upper()}")
    collected_jobs = []

    for keyword in keywords:
        keyword_jobs = []
        print(f"🔍 Crawling keyword: {keyword}")

        base_url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(keyword)}&location=Indonesia&start={{start}}"
        urls = [base_url.format(start=i) for i in range(0, 25, 25)]  # hanya 1 halaman

        for idx, url in enumerate(urls):
            if len(keyword_jobs) >= max_jobs_per_keyword:
                break

            print(f"🌐 Crawling '{keyword}' - Page {idx + 1}")
            try:
                result = await crawler.arun(url)

                if not result.markdown.strip():
                    print(f"🛑 No content on page {idx + 1}, skipping.")
                    continue

                res = client.beta.chat.completions.parse(
                    model='gpt-4o-mini',
                    messages=[
                        {"role": "system", "content": "Extract job list from the given text"},
                        {"role": "user", "content": result.markdown},
                    ],
                    response_format=JobList,
                )

                parsed = res.choices[0].message.parsed
                print(f"  ✅ Found {len(parsed.jobs)} jobs on page {idx + 1}")

                remaining = max_jobs_per_keyword - len(keyword_jobs)
                keyword_jobs.extend(parsed.jobs[:remaining])

            except Exception as e:
                print(f"  ❌ Failed to crawl page {idx + 1}: {e}")

        print(f"  ✅ Collected {len(keyword_jobs)} jobs for keyword '{keyword}'")

        collection_name = sanitize_collection_name(f"jobs_{category}")
        existing_collections = [col.name for col in chroma_client.list_collections()]
        if collection_name not in existing_collections:
            collection = chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function
            )
        else:
            collection = chroma_client.get_collection(name=collection_name)

        for idx, job in enumerate(keyword_jobs, start=1):
            try:
                job_hash = generate_md5_hash(job.url)
                print(f"\n➡️ Processing job {idx}: {job.job_title} at {job.company_name}")

                result = await crawler.arun(job.url)

                res = client.beta.chat.completions.parse(
                    model='gpt-4o-mini',
                    messages=[
                        {"role": "system", "content": "Extract job detail from the given text"},
                        {"role": "user", "content": result.markdown},
                    ],
                    response_format=Jobs,
                )

                job_data = res.choices[0].message.parsed
                job_json = job_data.model_dump()
                job_json['job_hash'] = job_hash
                job_json['category'] = category
                print("  ✅ Job data parsed successfully.")
                print("  Job JSON: ", job_json)

                await sync_to_async(save_job)(job_json, job_hash)
                print(f"  ✅ Job '{job.job_title}' saved to DB.")

                # ⬇️ Tambahkan ke Chroma langsung
                try:
                    document = {
                        "category": job_json["category"],
                        "job_hash": job_json["job_hash"],
                        "job_description": job_json["job_description"],
                        "job_title": job_json["job_title"],
                        "education_level": job_json["education_level"],
                        "experience_level": job_json["experience_level"],
                        "skills_required": job_json["skills_required"],
                    }

                    metadata = {
                        "job_hash": job_json["job_hash"],
                        "job_title": job_json["job_title"],
                        "company_name": job_json["company_name"],
                    }

                    existing_data = collection.get(ids=[job_json["job_hash"]])
                    if existing_data and existing_data.get("ids"):
                        collection.delete(ids=[job_json["job_hash"]])

                    collection.add(
                        ids=[str(job_json["job_hash"])],
                        metadatas=[metadata],
                        documents=[str(document)],
                    )
                    print(f"  ✅ Uploaded job '{job.job_title}' to ChromaDB.")
                except Exception as e:
                    print(f"  ❌ Failed to upload job '{job.job_title}' to ChromaDB: {e}")

            except Exception as e:
                print(f"❌ Error processing job '{job.job_title}': {e}")
    return collected_jobs

async def crawl_and_upload_category(crawler, category, keywords):
    try:
        await crawl_jobs_by_keywords(crawler, category, keywords, MAX_JOBS_PER_KEYWORD)
    except Exception as e:
        print(f"❌ Error during crawling/uploading category {category}: {e}")



async def crawl_jobs_async():
    start_time = time.time()
    print(f"[{datetime.now()}] crawl_jobs_async running...")

    async with AsyncWebCrawler() as crawler:
        tasks = [
            crawl_and_upload_category(crawler, category, keywords)
            for category, keywords in CATEGORY_KEYWORDS.items()
        ]
        await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    print(f"\n⏱️ Total waktu crawling dan upload: {int(elapsed // 60)} menit {int(elapsed % 60)} detik")

