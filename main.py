import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agents.pdf_processor import PDFProcessorAgent
from agents.qa_agent import QAAgent
from utils.telegram_utils import TelegramUtils
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramPDFBot:
    def __init__(self):
        self.config = Config()
        self.pdf_processor = PDFProcessorAgent()
        self.qa_agent = QAAgent()
        self.telegram_utils = TelegramUtils()
        
        # Create data directories
        os.makedirs(self.config.PDF_STORAGE_PATH, exist_ok=True)
        os.makedirs(self.config.VECTOR_DB_PATH, exist_ok=True)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **Welcome to PDF AI Assistant!**

I can help you analyze PDF documents and answer questions about them.

**How to use:**
1. Send me a PDF file
2. Wait for processing confirmation
3. Ask questions about the PDF content

**Commands:**
/start - Show this message
/help - Get help information

Send me a PDF to get started! 📄
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🆘 **How to use PDF AI Assistant:**

**Step 1:** Send a PDF file
- The bot will process and analyze your PDF
- Wait for the "✅ PDF processed successfully" message

**Step 2:** Ask questions
- Type any question about the PDF content
- The AI will search through the document and provide answers

**Examples:**
- "What is the main topic of this document?"
- "Summarize the key points"
- "What does it say about [specific topic]?"

**Supported formats:** PDF files only
**File size limit:** Up to 20MB
        """
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF document uploads"""
        try:
            await update.message.reply_text("📄 PDF received! Processing...")
      
            # Download PDF
            pdf_path = await self.telegram_utils.download_pdf(update, context)
            update.message.reply_text("pdf downloaded successfully!")
            # Process PDF
            user_id = str(update.effective_user.id)
            result = self.pdf_processor.process_pdf(pdf_path, user_id)
            update.message.reply_text("Got some result from pdf processor!")
            if result["success"]:
                message = f"✅ PDF processed successfully!\n"
                message += f"📊 Created {result['chunks_count']} text chunks\n"
                message += f"💡 You can now ask questions about the document!"
            else:
                message = f"❌ Error processing PDF: {result['error']}"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error handling document: {str(e)}")
            await update.message.reply_text(f"❌ Error handling document: {str(e)}")
    
    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user questions"""
        try:
            question = update.message.text
            
            await update.message.reply_text("🤔 Thinking...")
            
            # Get answer from QA agent
            result = self.qa_agent.answer_question(question)
            
            # Format and send response
            response = self.telegram_utils.format_answer_message(result)
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Error handling question: {str(e)}")
            await update.message.reply_text(f"❌ Error handling question: {str(e)}")
    
    def run(self):
        """Start the bot"""
        application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_question))
        
        # Start the bot
        print("🤖 Bot is starting...")
        application.run_polling()

if __name__ == "__main__":
    bot = TelegramPDFBot()
    bot.run()