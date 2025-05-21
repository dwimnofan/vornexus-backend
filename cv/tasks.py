import os
from huey.contrib.djhuey import task
from core.ai.mistral import mistral_client
from core.ai.chromadb import collection
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from django.contrib.auth import get_user_model
from matching.task import job_matching



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
            
            # Split text
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = text_splitter.split_text(parsed_text)
            print(chunks)
            print(len(chunks))
            
            # Store in ChromaDB if available
            if collection:
                # Store chunks
                for i, chunk in enumerate(chunks):
                    collection.add(
                        documents=[chunk],
                        ids=[f"{str(cv.id)}_{i}"]
                    )
            
            User = get_user_model()
            user = User.objects.get(id=cv.user_id)

            job_matching(user, cv.id)
            
            return True
            
        except Exception as e:
            print(f"Error processing CV {cv_id}: {str(e)}")
            raise  
            
    except CV.DoesNotExist:
        print(f"CV with ID {cv_id} not found.")
    except Exception as e:
        print(f"Unexpected error in process_cv_in_background: {str(e)}")
        raise