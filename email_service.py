import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from config import SMTP_USER, SMTP_PASS

def send_email_yandex(to_email: str, subject: str, html_body: str):
    msg = MIMEText(html_body, "html", "utf-8")
    msg["From"] = formataddr((str(Header("Магазин", "utf-8")), SMTP_USER))
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")

    with smtplib.SMTP_SSL("smtp.yandex.ru", 465) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
