import chromadb
import chromadb.errors

try:
    chroma_client = chromadb.HttpClient(host='localhost', port=8000)
    cv_collection = chroma_client.get_or_create_collection("cv_collection")
except chromadb.errors.ChromaError as e:
    print(f"Error initializing ChromaDB: {e}")
    chroma_client = None
    cv_collection = None