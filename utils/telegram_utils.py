import os
import uuid
from telegram import Update
from telegram.ext import ContextTypes
from config import Config

class TelegramUtils:
    def __init__(self):
        self.config = Config()
    
    async def download_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Download PDF file from Telegram"""
        try:
            document = update.message.document
            
            # Check if it's a PDF
            if not document.mime_type == 'application/pdf':
                raise ValueError("File is not a PDF")
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{document.file_name}"
            file_path = os.path.join(self.config.PDF_STORAGE_PATH, filename)
            
            # Download file
            file = await context.bot.get_file(document.file_id)
            await file.download_to_drive(file_path)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Error downloading PDF: {str(e)}")
    
    def format_answer_message(self, result: dict) -> str:
        """Format the answer for Telegram message"""
        if not result["success"]:
            return f"❌ Error formating answer: {result['error']}"
        
        message = f"🤖 **Answer:**\n{result['answer']}\n"
        
        # if result.get("sources"):
        #     message += "\n📚 **Sources:**\n"
        #     for source in result["sources"]:
        #         message += f"• {source['source']} (chunk {source['chunk_id']})\n"
        
        return message