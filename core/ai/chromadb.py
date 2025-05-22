import chromadb
import chromadb.errors
import os
import sys
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

# Skip ChromaDB initialization during Django commands
SKIP_COMMANDS = ['makemigrations', 'migrate', 'createsuperuser', 'shell', 'dbshell', 'check']
if any(cmd in sys.argv for cmd in SKIP_COMMANDS) or 'manage.py' in sys.argv[0]:
    print("Skipping ChromaDB initialization during Django management command")
    chroma_client = None
    collection = None
    job_collection = None
    embedding_function = None
else:
    try:
        chroma_client = chromadb.HttpClient(host='localhost', port=8010)
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables")
            collection = chroma_client.get_or_create_collection("cv_collection")
            embedding_function = None
        else:
            embedding_function = OpenAIEmbeddingFunction(
                api_key=openai_api_key,
                model_name="text-embedding-3-small"
            )
            
            collection = chroma_client.get_or_create_collection(
                name="cv_collection",
                embedding_function=embedding_function
            )

            job_collection = chroma_client.get_or_create_collection(
                name="job_collection",
                embedding_function=embedding_function
            )

    except chromadb.errors.ChromaError as e:
        print(f"Warning: ChromaDB initialization error: {e}")
        print("Continuing without ChromaDB functionality")
        chroma_client = None
        collection = None
        job_collection = None
        embedding_function = None
    except Exception as e:
        print(f"Error: {e}")
        chroma_client = None
        collection = None
        job_collection = None
        embedding_function = None