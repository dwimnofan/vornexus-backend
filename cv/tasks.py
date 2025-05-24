import os
from huey.contrib.djhuey import task
from core.ai.mistral import mistral_client
from dotenv import load_dotenv
from django.contrib.auth import get_user_model
from matching.task import job_matching
from cv.utils import clean_cv_text
from notifications.methods import send_notification

load_dotenv()

@task()
def process_cv(cv_id):
    cv = None
    try:
        from cv.models import CV  # avoid circular imports
        cv = CV.objects.get(id=cv_id)
        
        cv.status = "processing"
        cv.save()
        send_notification("Processing CV")
        file_path = cv.file_url
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, "rb") as file_content:
            uploaded_file = mistral_client.files.upload(
                file={
                    "file_name": os.path.basename(file_path),
                    "content": file_content,
                },
                purpose="ocr"
            )
        
        signed_url = mistral_client.files.get_signed_url(file_id=uploaded_file.id)
        
        # process the document with OCR
        ocr_response = mistral_client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url
            }
        )
        
        # extract OCR
        parsed_text = ""
        for page in ocr_response.pages:
            parsed_text += page.markdown + "\n\n"
        
        # clean parsed text
        cleaned_text = clean_cv_text(parsed_text)
        
        cv.parsed_text = cleaned_text
        cv.status = "completed"
        cv.save()
        send_notification("Processing completed")
        User = get_user_model()
        user = User.objects.get(id=cv.user_id)

        # call job matching
        job_matching(user, cv.id)
        
        return True
        
    except CV.DoesNotExist:
        print(f"CV with ID {cv_id} not found.")
        return False
    except Exception as e:
        print(f"Error processing CV {cv_id}: {str(e)}")
        
        if cv:
            try:
                cv.status = "failed"
                cv.save()
                send_notification("Failed to process CV. Please try again")
            except Exception as save_error:
                print(f"Failed to update CV status to failed: {str(save_error)}")
        
        raise e