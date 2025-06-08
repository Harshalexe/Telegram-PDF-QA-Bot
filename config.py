import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './data/vectordb')
    PDF_STORAGE_PATH = os.getenv('PDF_STORAGE_PATH', './data/pdfs')
    
    os.environ['HF_TOKEN']=os.getenv("HF_TOKEN")
    EMBEDDING_MODEL=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    
    GROQ_MODEL = "Gemma2-9b-It"
    CHUNK_SIZE = 700
    CHUNK_OVERLAP = 200
    MAX_TOKENS = 4000