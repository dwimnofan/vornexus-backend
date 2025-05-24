import asyncio
import time
import hashlib
import re
from crawl4ai import AsyncWebCrawler
from core.ai.crawl import client, JobList, Jobs
from huey.contrib.djhuey import periodic_task
from huey import crontab
from asgiref.sync import sync_to_async
from datetime import datetime
from core.ai.chromadb import  chroma_client, embedding_function
from jobs.utils import save_job, get_jobs_not_uploaded

print(time.tzname)        # Nama timezone lokal (misal: ('WIB', 'WIB'))
print(time.timezone)      # Offset dalam detik dari UTC (negatif kalau di depan UTC)

# @periodic_task(crontab(minute="*/1"), ) # Waktu server utc-7, jadi perlu kita ubah ke utc+7 dengan menambah 7 jam
# def five_minute_task():
#     collections = chroma_client.list_collections()

#     print("Daftar Collections:")
#     for col in collections:
        # print(f"- Collection Name: {col.name}")
        
        # # Ambil collection berdasarkan nama
        # collection = chroma_client.get_collection(name=col.name)
        
        # # Ambil sebagian isi collection (misalnya 3 item pertama)
        # results = collection.get(limit=10)

        # for i in range(len(results["ids"])):
        #     print(f"  ID         : {results['ids'][i]}")
        #     print(f"  Document   : {results['documents'][i]}")
        #     print(f"  Metadata   : {results['metadatas'][i]}")
        #     print("  ---")
        # print()

def sanitize_collection_name(name: str) -> str:
    """
    Sanitize category name to be a valid ChromaDB collection name:
    - Replace all non-alphanumeric characters with underscores
    - Strip leading/trailing underscores
    - Ensure length between 3 and 512
    """
    # Lowercase and replace non-alphanumeric characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', name.lower())
    sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with single
    sanitized = sanitized.strip('_')

    # Ensure name starts and ends with alphanumeric character
    if not re.match(r'^[a-zA-Z0-9].*[a-zA-Z0-9]$', sanitized):
        raise ValueError(f"Invalid sanitized name: {sanitized}")

    # Validate length
    if len(sanitized) < 3 or len(sanitized) > 512:
        raise ValueError(f"Collection name must be 3-512 characters: {sanitized}")

    return sanitized

def get_collection_by_category(category_name: str):
    collection_name = sanitize_collection_name(f"jobs_{category_name}")
    return chroma_client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)

MAX_JOBS_PER_CATEGORY = 15  # max job per kategori

CATEGORY_KEYWORDS = {
    # "Teknologi ": [
        # "software engineer", 
        # "software engineer", "devops engineer", "data scientist",
        # "cybersecurity analyst", "qa engineer", "ui/ux designer", "cloud engineer",
        # "backend", "frontend", "full stack", "mobile developer", "machine learning", "data analyst", "qa tester"
    # ],
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


@periodic_task(crontab(hour=16, minute=3), name="crawl_jobs")
def crawl_jobs():
    try:
        asyncio.run(crawl_jobs_async())
    except Exception as e:
        print(f"Error running crawl_jobs: {e}")


def generate_md5_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


async def crawl_jobs_by_keywords(crawler, category, keywords, max_jobs_per_keyword):
    print(f"\n📁 Crawling category: {category.upper()}")
    collected_jobs = []

    for keyword in keywords:
        keyword_jobs = []
        print(f"🔍 Crawling keyword: {keyword}")

        base_url = f"https://www.linkedin.com/jobs/search?keywords={keyword.replace(' ', '%20')}&location=Indonesia&start={{start}}"
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

        # ⬇️ Proses dan simpan ke DB langsung setelah selesai 1 keyword
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
                job_json['category'] = category
                print("  ✅ Job data parsed successfully.")
                print("  Job JSON: ", job_json)

                await sync_to_async(save_job)(job_json, job_hash)
                print(f"  ✅ Job '{job.job_title}' saved to DB.")
                collected_jobs.append(job_json)
                print(f"  ✅ Job '{job.job_title}' processed successfully.")

            except Exception as e:
                print(f"❌ Error processing job '{job.job_title}': {e}")
    return collected_jobs




async def crawl_jobs_async():
    start_time = time.time()
    print(f"[{datetime.now()}] crawl_jobs running...")

    all_jobs = []

    async with AsyncWebCrawler() as crawler:
        # buat list task crawling per kategori secara paralel
        tasks = [
            crawl_jobs_by_keywords(crawler, category, keywords, MAX_JOBS_PER_CATEGORY)
            for category, keywords in CATEGORY_KEYWORDS.items()
        ]

        # jalankan semua task crawling kategori secara paralel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        print("Results: ", results)

        try:
            print("\n🔍 Collecting jobs from all categories...")
            # kumpulkan semua job dari tiap kategori
            for result in results:
                if isinstance(result, Exception):
                    print(f"❌ Error during crawling category: {result}")
                else:
                    all_jobs.extend(result)
        except Exception as e:
            print(f"❌ Error collecting jobs: {e}")

        print(f"\n🔍 Total jobs collected across all categories: {len(all_jobs)}")
        print("Jobs: ", all_jobs)

        jobs_to_upload = await sync_to_async(get_jobs_not_uploaded)()
        print(f"Starting to upload {len(jobs_to_upload)} jobs to vector DB...")
        print(f"jobs to upload: {jobs_to_upload}")
        


        for job in jobs_to_upload:
            try:
                collection = get_collection_by_category(job.category)
                document = {
                    "category": job.category,
                    "job_hash": job.job_hash,
                    "job_description": job.job_description,
                    "job_title": job.job_title,
                    "education_level": job.education_level,
                    "experience_level": job.experience_level,
                    "skills_required": job.skills_required,
                }

                metadata = {
                    "job_hash": job.job_hash,
                    "job_title": job.job_title,
                    "company_name": job.company_name,
                }

                # 1. Cek apakah ID sudah ada di vector DB
                existing_data = collection.get(ids=[job.job_hash])

                # 2. Jika sudah ada, hapus dulu
                if existing_data and existing_data.get("ids"):
                    collection.delete(ids=[job.job_hash])

                collection.add(
                    ids=[str(job.job_hash)],
                    metadatas=[metadata],
                    documents=[str(document)],
                )

                print(f"✅ Uploaded job {job.job_title} to vector DB.")

            except Exception as e:
                print(f"❌ Failed to upload job {job.job_title}: {e}")

        end_time = time.time()
        elapsed = end_time - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print(f"\n⏱️ Total waktu crawling: {minutes} menit {seconds} detik")
