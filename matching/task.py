import os
import json
import re
from huey.contrib.djhuey import task
from core.ai.chromadb import job_collection, chroma_client, embedding_function
from dotenv import load_dotenv
from cv.models import CV
from core.ai.pm import PromptManager
from matching.models import JobRecommendation 


from pydantic import BaseModel, Field
from typing import List


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class MatchedJob(BaseModel):
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Job location")
    match_score: float = Field(description="total requirements that match this job on a scale of 0-100%")
    matched_skills: list[str] = Field(description="List of matched skills")
    required_skills: list[str] = Field(description="List of required skills")
    job_description: str = Field(description="Job description")
    apply_link: str = Field(description="Link to apply for the job")
    reason: str = Field(description="Reason for the match score and match jobs, reason why you give that score and why you choose that job")

class MatchingJob(BaseModel):
    jobs: List[MatchedJob] = Field(description="List of matched jobs")

@task()
def job_matching(user, cv_id):
    pm = PromptManager()

    # Ambil objek CV, bukan langsung field parsed_text
    cv = CV.objects.filter(id=cv_id).first()

    parsed_cv = cv.parsed_text

    # Baca file job list
    with open("job_list3.txt", "r", encoding="utf-8") as file:
        job_list = file.read()

    job_entries = re.split(r'\[\d+\]', job_list)
    job_entries = [entry.strip() for entry in job_entries if entry.strip()]

    job_collection.add(
        documents=job_entries,
        ids=[str(i) for i in range(len(job_entries))]
    )

    job_vacancies = chroma_client.get_collection("job_collection", embedding_function=embedding_function)

    result = job_vacancies.query(
        query_texts=[parsed_cv],
        n_results=10,
        include=["documents", "distances"],
    )

    documents = result.get("documents", [[]])[0]
    formatted_jobs = ""
    for i, doc in enumerate(documents, 1):
        formatted_jobs += f"Lowongan {i}:\n{doc.strip()}\n\n"

    pm.add_message("system", f"Your job is to answer only based on the provided context. This is the context: {formatted_jobs}")
    pm.add_message("user", f"Pilih 10 pekerjaan yang paling cocok berdasarkan CV berikut:\n{parsed_cv}\n"
                            "Urutkan pekerjaan berdasarkan match score dari yang tertinggi ke terendah.\n")

    result = pm.generate_structure(MatchingJob)
    matched_jobs = result.get('jobs')
    for idx, job in enumerate(matched_jobs, 1):
        JobRecommendation.objects.create(
            user = user,
            job_id = f"job{idx}",
            title = job["title"],
            company = job["company"],
            company_logo = job.get("company_logo", ""),
            company_desc = job.get("company_desc", ""),
            company_industry = job.get("company_industry", ""),
            company_employee_size = job.get("company_employee_size", ""),
            location = job["location"],
            match_score = job["match_score"],
            required_skills = job.get("required_skills", []),
            matched_skills = job.get("matched_skills", []),
            job_description = job["job_description"],
            apply_link = job["apply_link"]
        )
        print(f"✅ Job #{idx} berhasil disimpan ke database.")

    


