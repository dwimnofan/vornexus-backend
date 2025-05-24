
from .models import Job
from datetime import datetime


def save_job(job_json: dict, job_hash: str) -> Job:
    # Parse tanggal (contoh asumsi format 'YYYY-MM-DD', sesuaikan jika beda)
    date_posted = None
    if 'date_posted' in job_json and job_json['date_posted']:
        try:
            date_posted = datetime.strptime(job_json['date_posted'], "%Y-%m-%d").date()
        except Exception:
            pass

    # Jika ada job dengan job_title dan company_name yang sama, hapus yang lama untuk menghindari duplikasi
    Job.objects.filter(
        job_title=job_json.get("job_title"),
        company_name=job_json.get("company_name")
    ).delete()

    job, created = Job.objects.update_or_create(
        job_hash=job_hash,
        defaults={
            "category": job_json.get("category"),
            "job_title": job_json.get("job_title"),
            "company_name": job_json.get("company_name"),
            "company_industry": job_json.get("industry"),
            "company_employee_size": job_json.get("company_size"),
            "company_desc": job_json.get("company_desc"),
            "location": job_json.get("location"),
            "url": job_json.get("url"),
            "job_type": job_json.get("job_type"),
            "experience_level": job_json.get("experience_level"),
            "education_level": job_json.get("education_level"),
            "skills_required": job_json.get("skills_required"),
            "salary": job_json.get("salary"),
            "date_posted": date_posted,
            "job_description": job_json.get("job_description"),
            "uploaded_to_vector_db": False,
        }
    )
    return job

def get_jobs_not_uploaded():
    return list(Job.objects.filter(uploaded_to_vector_db=False))


def mark_job_uploaded(job_id: int):
    Job.objects.filter(id=job_id).update(uploaded_to_vector_db=True)
