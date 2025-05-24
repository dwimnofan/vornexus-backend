import os
import re
from huey.contrib.djhuey import task
from dotenv import load_dotenv
from cv.models import CV
from core.ai.pm import PromptManager
from matching.models import JobRecommendation 
from jobs.models import Job  # import model Job
from core.ai.chromadb import chroma_client, embedding_function

from pydantic import BaseModel, Field
from typing import List
from django.utils import timezone
from datetime import date

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class MatchedJob(BaseModel):
    job_id : str = Field(..., description="Unique identifier for the job")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    match_score: float = Field(..., description="Total requirements that match this job on a scale of 0-100%")
    matched_skills: List[str] = Field(..., description="List of matched skills between CV and job") 
    required_skills: List[str] = Field(..., description="List of required skills")
    job_description: str = Field(..., description="Job description")
    apply_link: str = Field(..., description="Link to apply for the job")
    reason: str = Field(..., description="Reason for the match score and job match")
    url: str = Field(..., description="Unique job URL")
    job_type: str = Field(..., description="Type of job, e.g. full-time, part-time")
    industry: str = Field(..., description="Industry the job belongs to")
    experience_level: str = Field(..., description="Experience level required for the job")
    education_level: str = Field(..., description="Education level required for the job")
    skills_required: str = Field(..., description="All required skills in string format")
    date_posted: date = Field(..., description="Date the job was posted")

class MatchingJob(BaseModel):
    jobs: List[MatchedJob] = Field(description="List of matched jobs")



def sanitize_collection_name(name: str) -> str:
    """
    Membersihkan nama koleksi agar sesuai aturan ChromaDB.
    - Mengganti karakter ilegal dengan underscore (_)
    - Menjaga agar nama diawali dan diakhiri huruf/angka
    """
    # Ubah menjadi lowercase dan ganti karakter tidak valid
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', name.lower())
    sanitized = re.sub(r'_+', '_', sanitized)  # Gabungkan underscore ganda
    sanitized = sanitized.strip('_')  # Hapus _ di awal/akhir

    # Pastikan diawali dan diakhiri huruf/angka
    if not re.match(r'^[a-zA-Z0-9].*[a-zA-Z0-9]$', sanitized):
        raise ValueError(f"Invalid sanitized name: {sanitized}")

    # Panjang antara 3-512 karakter
    if len(sanitized) < 3 or len(sanitized) > 512:
        raise ValueError(f"Collection name must be 3-512 characters: {sanitized}")

    return sanitized

def get_collection_by_category(category_name: str):
    sanitized_name = sanitize_collection_name(f"jobs_{category_name}")
    return chroma_client.get_or_create_collection(name=sanitized_name)


CATEGORY_KEYWORDS = {
    "Teknologi": [
        "software engineer", "devops engineer", "data scientist",
        "cybersecurity analyst", "qa engineer", "ui/ux designer", "cloud engineer",
        "backend", "frontend", "full stack", "mobile developer", "machine learning", "data analyst", "qa tester"
    ],
    "Bisnis dan Manajemen": [
        "business analyst", "project manager", "product manager",
        "hr specialist", "recruiter", "marketing specialist", "digital marketing",
        "finance analyst", "accountant"
    ],
    "Kreatif": [
        "graphic designer", "ui designer", "content writer", "copywriter",
        "video editor", "social media specialist", "brand strategist"
    ],
    "Industri dan Manufaktur": [
        "mechanical engineer", "industrial engineer", "supply chain analyst",
        "procurement specialist", "quality assurance engineer", "qa manufaktur", "qa logistik"
    ]
}

@task()
def job_matching(user, cv_id):
    pm = PromptManager()
    cv = CV.objects.filter(id=cv_id).first()
    if not cv:
        print(f"CV dengan id {cv_id} tidak ditemukan.")
        return

    parsed_cv = cv.parsed_text
    list_collections = chroma_client.list_collections()
    for col in list_collections:
        print(f"- Collection Name: {col.name}")
    collection = get_collection_by_category("bisnis_dan_manajemen")
    print("Total jobs in collection:", collection.count())

    result = collection.query(
        query_texts=[parsed_cv],
        n_results=10,
        include=["documents", "distances", "metadatas"],
    )


    documents = result.get("documents", [[]])[0]
    print("Result:", result)
    formatted_jobs = ""
    for i, doc in enumerate(documents, 1):
        formatted_jobs += f"Lowongan {i}:\n{doc.strip()}\n\n"

    pm.add_message("system", f"Your job is to answer only based on the provided context. This is the context: {formatted_jobs}")
    pm.add_message("user", f"Pilih 10 pekerjaan yang paling cocok berdasarkan CV berikut:\n{parsed_cv}\n"
                            "Urutkan pekerjaan berdasarkan match score dari yang tertinggi ke terendah.\n")

    result = pm.generate_structure(MatchingJob)
    matched_jobs = result.get('jobs')
    print("Matched Jobs:", matched_jobs)

    for idx, job in enumerate(matched_jobs, 1):
        job_instance = Job.objects.filter(job_hash=job['job_id']).first()
        if job_instance:
            # Buat JobRecommendation, jika sudah ada, skip
            recommendation, created_rec = JobRecommendation.objects.get_or_create(
                user=user,
                job=job_instance,
                defaults={
                    "score": job["match_score"],
                    "recommended_at": timezone.now()
                },
                matched_skills=job["matched_skills"]
            )

            if created_rec:
                print(f"✅ JobRecommendation #{idx} berhasil disimpan untuk user {user.username}.")
            else:
                print(f"⚠️ JobRecommendation #{idx} sudah ada untuk user {user.username}, dilewati.")
        else:
            print(f"❌ Job {job['title']} di {job['company']} tidak ditemukan di database.")
