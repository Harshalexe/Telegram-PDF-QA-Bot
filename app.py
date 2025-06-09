from flask import Flask, request, jsonify
import logging
import os
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agents.pdf_processor import PDFProcessorAgent
from agents.qa_agent import QAAgent
from utils.telegram_utils import TelegramUtils
from config import Config
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class TelegramPDFBot:
    def __init__(self):
        self.config = Config()
        self.pdf_processor = PDFProcessorAgent()
        self.qa_agent = QAAgent()
        self.telegram_utils = TelegramUtils()
        
        # Create data directories
        os.makedirs(self.config.PDF_STORAGE_PATH, exist_ok=True)
        os.makedirs(self.config.VECTOR_DB_PATH, exist_ok=True)
        
        # Initialize bot and application
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
        self.application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_question))
    
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
            await update.message.reply_text("pdf downloaded successfully!")
            
            # Process PDF
            user_id = str(update.effective_user.id)
            result = self.pdf_processor.process_pdf(pdf_path, user_id)
            await update.message.reply_text("Got some result from pdf processor!")
            
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
    
    async def process_update(self, update_data):
        """Process incoming webhook update"""
        try:
            update = Update.de_json(update_data, self.bot)
            await self.application.process_update(update)
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            raise

# Initialize bot instance
bot_instance = TelegramPDFBot()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Bot is running"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        update_data = request.get_json()
        
        if not update_data:
            return jsonify({"error": "No data received"}), 400
        
        # Process the update asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_instance.process_update(update_data))
        loop.close()
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Set webhook URL for Telegram bot"""
    try:
        webhook_url = request.json.get('webhook_url')
        if not webhook_url:
            return jsonify({"error": "webhook_url is required"}), 400
        
        # Set webhook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot_instance.bot.set_webhook(url=webhook_url))
        loop.close()
        
        if result:
            return jsonify({"status": "success", "message": "Webhook set successfully"}), 200
        else:
            return jsonify({"error": "Failed to set webhook"}), 500
            
    except Exception as e:
        logger.error(f"Set webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_webhook_info', methods=['GET'])
def get_webhook_info():
    """Get current webhook information"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        webhook_info = loop.run_until_complete(bot_instance.bot.get_webhook_info())
        loop.close()
        
        return jsonify({
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates
        }), 200
        
    except Exception as e:
        logger.error(f"Get webhook info error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/delete_webhook', methods=['POST'])
def delete_webhook():
    """Delete current webhook"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot_instance.bot.delete_webhook())
        loop.close()
        
        if result:
            return jsonify({"status": "success", "message": "Webhook deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete webhook"}), 500
            
    except Exception as e:
        logger.error(f"Delete webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "message": "Telegram PDF Bot API is running",
        "endpoints": {
            "/health": "Health check",
            "/webhook": "Telegram webhook endpoint",
            "/set_webhook": "Set webhook URL",
            "/get_webhook_info": "Get webhook information",
            "/delete_webhook": "Delete webhook"
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
