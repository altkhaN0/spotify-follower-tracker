import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

class GmailSender:
    def __init__(self, configs) -> None:
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = configs["mail_from"]
        self.sender_password = configs["mail_password"]
        self.receiver_email = configs["mail_to"]
        self.last_email_sent_at = None

    def send_message(self, message_subject, message):
        if self.last_email_sent_at and time.time() - self.last_email_sent_at < 15:
            message_subject = "Spotify - ERROR"
            err_message = f"An error occurred: Too many emails sent in a short period of time.\nOriginal message:\n{message}"
            message = err_message
        
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.receiver_email
        msg["Subject"] = message_subject
        msg.attach(MIMEText(message, "plain"))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, self.receiver_email, text)
            print("Email sent successfully!")
            self.last_email_sent_at = time.time()
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            server.quit()
