import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import traceback
from utils.logging_config import logger
from config.settings import EMAIL_ADDRESS, EMAIL_APP_PASSWORD

class SharingService:
    def send_chat_history(self, chat_history, recipient_email):
        """Send chat history to the specified email."""
        sender_email = EMAIL_ADDRESS
        password = EMAIL_APP_PASSWORD

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = "Chat History from AI Learning Assistant"

        body = "Here's the chat history:\n\n"
        for chat in chat_history:
            body += f"{chat['role'].capitalize()}: {chat['content']}\n\n"

        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.send_message(message)
            return f"Chat history shared successfully with {recipient_email}"
        except Exception as e:
            logger.error(f"Error sharing chat history: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error sharing chat history: {str(e)}"

    def send_document(self, pdf_docs, recipient_email):
        """Share PDF documents with another user via email."""
        sender_email = EMAIL_ADDRESS
        password = EMAIL_APP_PASSWORD

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = "Shared Documents from AI Learning Assistant"

        # Add body text
        body = "Here are the documents shared with you from the AI Learning Assistant."
        message.attach(MIMEText(body, "plain"))

        # Attach PDF files
        for pdf in pdf_docs:
            pdf.seek(0)  # Reset file pointer to beginning
            part = MIMEBase("application", "octet-stream")
            part.set_payload(pdf.read())
            encoders.encode_base64(part)
            
            # Add header with PDF filename
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {pdf.name}",
            )
            message.attach(part)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.send_message(message)
            return f"Documents shared successfully with {recipient_email}"
        except Exception as e:
            logger.error(f"Error sharing documents: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error sharing documents: {str(e)}"

# Create singleton instance
sharing_service = SharingService()
