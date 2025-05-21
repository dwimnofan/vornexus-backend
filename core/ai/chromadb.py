import chromadb
import chromadb.errors
import os
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

try:
    chroma_client = chromadb.HttpClient(host='localhost', port=8000)
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Warning: OPENAI_API_KEY not found in environment variables")
        collection = chroma_client.get_or_create_collection("cv_collection")
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
    print(f"Error initializing ChromaDB: {e}")
    chroma_client = None
    collection = None