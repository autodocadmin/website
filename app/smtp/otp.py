# import random
# import smtplib
# from email.message import EmailMessage
# def otp_verification(to_mail=None):
#     if to_mail is None:
#         return
#     email = "theautodoc.in@gmail.com"


#     otp =random.randint(100000,999999)

#     server = smtplib.SMTP('smtp.gmail.com',587)
#     server.starttls()

#     server.login("theautodoc.in@gmail.com","aeow jigb peuj fczn")
#     # to_mail = "pranitkalebere7266@gmail.com"
#     msg = EmailMessage()
#     msg['Subject'] = "OTP"
#     msg['From'] = email
#     msg['To'] = to_mail
#     msg.set_content(f"Your OTP is {otp}")
#     server.send_message(msg)
#     server.quit()
#     return otp

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
            print("sent mail")

        return otp

    except Exception as e:
        return None
    
# create a greeting message with same smpt for autodoc and send license key
def send_license_key(email, license_key,name,phone,shop_name,location):
    smtp_server = "smtp.titan.email"
    smtp_port = 465
    username = "support@theautodoc.in"
    password = "AutoDoc@2024"
    sender_email = "support@theautodoc.in"
    receiver_email = email
    subject = " Your License Key for AutoDoc"
    body = f"""
Dear {email},
    
Thank you for choosing AutoDoc. We're thrilled to have you on board!
Below, you'll find your license key. Please keep it safe, as you'll need it to activate your product.

Your License Key: {license_key}

Customer Information
Name:{name}
Email: {email}
Phone: {phone}
Shop Name:{shop_name}({location})

How to Activate
1. Open AutoDoc Software.
2. Navigate to the activation screen.
3. Enter your license key in the required field.

If you need assistance with activation or have any questions, please don't hesitate to reach out.

Support Information
Email: support@theautodoc.in
Phone: +917821895115
Help Center: https://www.theautodoc.in/help-center
Once again, thank you for choosing AutoDoc. We look forward to supporting you every step of the way!
"""

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

    except Exception as e:
        return None
if __name__ == "__main__":
    #send_license_key("pranitkalebere7266@gmail.com","123456789")
    otp_verification("pranitkalebere7266@gmail.com")