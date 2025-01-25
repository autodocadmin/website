import smtplib,random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def otp_verification(receiver_email=None):

    otp =random.randint(100000,999999)

    smtp_server = "smtp.titan.email"
    smtp_port = 465
    username = "support@theautodoc.in"
    password = "AutoDoc@2024"
 
    sender_email = "support@theautodoc.in"
    receiver_email = "sahilkalebere0.7@gmail.com"
    subject = "OTP"
    body = f"Your OTP is {otp}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Establish secure connection with the server
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:  # For STARTTLS, use smtplib.SMTP
            server.login(username, password)
            server.sendmail(sender_email, receiver_email, message.as_string())

        return otp

    except Exception as e:
        return None

if __name__ == "__main__":
    otp = otp_verification("sahilkalebere0.7@gmail.com")
    print(otp)
