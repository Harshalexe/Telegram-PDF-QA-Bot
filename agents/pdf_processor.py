import PyPDF2
import os
import hashlib
from typing import List
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.vector_store import VectorStoreManager
from config import Config

class PDFProcessorAgent:
    def __init__(self):
        self.config= Config()
        self.vector_store_manager = VectorStoreManager()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            length_function=len,
        )

    def process_pdf(self, pdf_path:str, user_id:str) -> dict:
        try:

            pdf_hash = self._generate_pdf_hash(pdf_path)
            text_content = self._extract_text_from_pdf(pdf_path)

            if not text_content.strip():
                return {"status": "error", "message": "PDF is empty or could not be read."}
            chunks = self.text_splitter.split_text(text_content)
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": os.path.basename(pdf_path),
                        "pdf_hash": pdf_hash,
                        "chunk_id": i,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc)
            
            # ADD THIS LINE to store chunks in the vector store
            self.vector_store_manager.add_documents(documents)
            
            return {
                "success": True,
                "chunks_count": len(chunks),
                "documents": documents,  # Include documents if needed elsewhere
                "pdf_hash": pdf_hash
            }
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text
                        
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        
        return text
    
    def _generate_pdf_hash(self, pdf_path: str) -> str:
        """Generate unique hash for PDF file"""
        hash_md5 = hashlib.md5()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()[:16]
