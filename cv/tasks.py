import os
from huey.contrib.djhuey import task
from core.ai.mistral import mistral_client
from core.ai.chromadb import cv_collection
from dotenv import load_dotenv


load_dotenv()

@task()
def process_cv_in_background(cv_id):
    """Process the CV file in a background task with retries."""
    try:
        from cv.models import CV  # avoid circular imports
        cv = CV.objects.get(id=cv_id)
        
        file_path = cv.file_url
        
        try:
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
            
            # Process the document with OCR
            ocr_response = mistral_client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url
                }
            )
            
            # Extract OCR
            parsed_text = ""
            for page in ocr_response.pages:
                parsed_text += page.markdown + "\n\n"
            
            # Store the parsed text
            cv.parsed_text = parsed_text
            cv.save()
            
            # Store in ChromaDB if available
            if cv_collection:
                cv_collection.add(
                    documents=[parsed_text],
                    metadatas=[{"cv_id": str(cv.id), "user_id": cv.user_id}],
                    ids=[str(cv.id)]
                )
            
            return True
            
        except Exception as e:
            print(f"Error processing CV {cv_id}: {str(e)}")
            raise  
            
    except CV.DoesNotExist:
        print(f"CV with ID {cv_id} not found.")
    except Exception as e:
        print(f"Unexpected error in process_cv_in_background: {str(e)}")
        raise