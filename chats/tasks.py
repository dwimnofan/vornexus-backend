from huey.contrib.djhuey import task
from core.ai.pm import PromptManager
from .methods import send_chat_message
from chats.models import Conversation
from core.ai.chromadb import chroma_client, embedding_function
from cv.models import CV
from jobs.models import Job 

@task()
def process_chat(message, document_id, cv_id):
    # Simpan pesan user ke database
    Conversation.objects.create(message=message, role="user")

    # Ambil parsed_text dari CV user
    try:
        cv = CV.objects.get(id=cv_id)
        cv_text = cv.parsed_text
    except CV.DoesNotExist:
        cv_text = "CV tidak ditemukan."

    # Ambil informasi lowongan berdasarkan document_id
    try:
        job = Job.objects.get(job_hash=document_id)
        job_text = (
    f"Judul Pekerjaan: {job.job_title or '-'}\n"
    f"Nama Perusahaan: {job.company_name or '-'}\n"
    f"Industri Perusahaan: {job.company_industry or '-'}\n"
    f"Deskripsi Perusahaan: {job.company_desc or '-'}\n"
    f"Ukuran Perusahaan: {job.company_employee_size or '-'}\n"
    f"Industri Pekerjaan: {job.industry or '-'}\n"
    f"Lokasi: {job.location or '-'}\n"
    f"Tipe Pekerjaan: {job.job_type or '-'}\n"
    f"Level Pengalaman: {job.experience_level or '-'}\n"
    f"Tingkat Pendidikan: {job.education_level or '-'}\n"
    f"Gaji: {job.salary or '-'}\n"
    f"Tanggal Diposting: {job.date_posted or '-'}\n"
    f"Keahlian yang Dibutuhkan: {job.skills_required or '-'}\n"
    f"Deskripsi Pekerjaan:\n{job.job_description or '-'}\n"
    f"Link Lowongan: {job.url}\n"
)
    except Job.DoesNotExist:
        job_text = "Informasi lowongan tidak ditemukan."

    # Ambil semua chat sebelumnya
    chats = Conversation.objects.all()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. "
                "User might ask about their CV, the job posting, or compare both. "
                "Provide clear and helpful responses.\n\n"
                f"User CV:\n{cv_text}\n\n"
                f"Job Posting:\n{job_text}"
            ),
        }
    ]

    for chat in chats:
        messages.append({"role": chat.role, "content": chat.message})

    # Generate response
    prompt = PromptManager()
    prompt.set_messages(messages)
    response = prompt.generate()

    Conversation.objects.create(message=response, role="assistant")
    send_chat_message(response)

    print("=== Response ===")
    print(response)
