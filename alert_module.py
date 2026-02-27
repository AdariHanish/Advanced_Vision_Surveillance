import smtplib
from email.message import EmailMessage
import ssl
import os
import mimetypes

SENDER_EMAIL = "yourgmail@gmail.com"
SENDER_PASSWORD = "your_16_character_app_password"
RECEIVER_EMAIL = "receivergmail@gmail.com"


def send_email_alert(subject, body, image_path=None):
    try:
        msg = EmailMessage()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject
        msg.set_content(body)

        # ===============================
        # ATTACH IMAGE SAFELY
        # ===============================
        if image_path and os.path.exists(image_path):

            with open(image_path, "rb") as f:
                file_data = f.read()

            mime_type, _ = mimetypes.guess_type(image_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            maintype, subtype = mime_type.split("/")

            msg.add_attachment(
                file_data,
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(image_path)
            )

            print("Image attached:", image_path)
        else:
            print("Image path not found:", image_path)

        # ===============================
        # SEND EMAIL
        # ===============================
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print("✅ Email alert sent successfully.")

    except Exception as e:
        print("❌ Email failed:", e)