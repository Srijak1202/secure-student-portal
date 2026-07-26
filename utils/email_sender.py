import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configuration (Ideally move to app.config or .env)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "srijak1202@gmail.com" 
SENDER_PASSWORD = "ecvavuuxrgdkfanm"

def send_otp_email(recipient_email, otp, sender_email=None, sender_password=None):
    """
    Sends an OTP to the specified email address using SMTP.
    allows dynamic sender credentials.
    """
    try:
        if not recipient_email:
            print("[EMAIL SERVICE] Error: Recipient email is missing.")
            return False, "Recipient email is missing."
        
        # Use provided credentials or fall back to config
        email_user = sender_email if sender_email else SENDER_EMAIL
        email_pass = sender_password if sender_password else SENDER_PASSWORD
        
        if "your_email" in email_user or "your_app_password" in email_pass:
             print("[EMAIL SERVICE] Mock Send (Credentials not set): OTP is", otp)
             return False, "Email credentials not configured. Please enter them in Login page or config."

        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = recipient_email
        msg['Subject'] = "Your SecurePortal Login OTP"

        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #4f46e5;">SecurePortal Login</h2>
                    <p>Hello,</p>
                    <p>Your One-Time Password (OTP) for login is:</p>
                    <div style="font-size: 24px; font-weight: bold; color: #4f46e5; margin: 20px 0;">
                        {otp}
                    </div>
                    <p>This code expires in 5 minutes. Do not share this code with anyone.</p>
                    <p>Regards,<br>SecurePortal Team</p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, recipient_email, msg.as_string())
        server.quit()
        
        print(f"[EMAIL SERVICE] Email sent to {recipient_email} from {email_user}")
        return True, "Email sent successfully"
        
    except Exception as e:
        print(f"[EMAIL SERVICE] Error: {str(e)}")
        return False, str(e)
