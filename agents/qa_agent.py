from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from utils.vector_store import VectorStoreManager
from config import Config

class QAAgent:
    def __init__(self):
        self.config=Config()
        self.vector_store_manager = VectorStoreManager()
        self.llm = ChatGroq(
            groq_api_key=self.config.GROQ_API_KEY,
            model_name=self.config.GROQ_MODEL,
            temperature=0.1,
            max_tokens=self.config.MAX_TOKENS,
            max_retries=3
        )
        self.qa_chain = self._create_qa_chain()

    def _create_qa_chain(self):
        """Create the QA chain with custom prompt"""
        
        prompt_template = """
        You are an AI assistant that answers questions based on PDF documents. 
        Use the following pieces of context to answer the question at the end. 
        If you don't know the answer based on the context, say "I don't have enough information in the provided documents to answer this question."
        
        Be concise but comprehensive in your answers. If the context contains specific details, include them in your response.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer: """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        retriever = self.vector_store_manager.get_retriever(k=5)
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
    
    def answer_question(self, question: str) -> dict:
        """Answer a question based on stored PDF content"""
        try:
            result = self.qa_chain({"query": question})
            
            # Extract source information
            sources = []
            for doc in result.get("source_documents", []):
                sources.append({
                    "source": doc.metadata.get("source", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", 0)
                })
            
            return {
                "success": True,
                "answer": result["result"],
                "sources": sources
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating answer: {str(e)}"
            }
    
