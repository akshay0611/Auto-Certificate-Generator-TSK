from __future__ import annotations

import smtplib
from typing import Any

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import get_app_config
from pdf_generator import safe_certificate_filename


def send_certificate_email(registration: dict[str, Any], pdf_bytes: bytes, settings: dict[str, Any]) -> bool:
    try:
        cfg = get_app_config()
        smtp_host = cfg.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(cfg.get("SMTP_PORT", "587"))
        smtp_user = cfg.get("SMTP_USER")
        smtp_pass = cfg.get("SMTP_PASS")
        email_from = cfg.get("EMAIL_FROM") or smtp_user
        email_from_name = cfg.get("EMAIL_FROM_NAME", "Tensorik Technologies")
        email_bcc = cfg.get("EMAIL_BCC")
        strings = settings["STRINGS"]

        recipient_email = str(registration.get("email") or "").strip()
        if not recipient_email or not smtp_user or not smtp_pass:
            return False

        workshop_name = str(
            registration.get("workshop_title")
            or registration.get("workshop_id")
            or "Workshop"
        )
        full_name = str(registration.get("full_name") or "Participant")
        workshop_id = str(registration.get("workshop_id") or "workshop")

        msg = MIMEMultipart()
        msg["From"] = f"{email_from_name} <{email_from}>"
        msg["To"] = recipient_email
        if email_bcc:
            msg["Bcc"] = email_bcc
        msg["Subject"] = strings["email_subject"].format(workshop_name=workshop_name)

        body = (
            f"<p>Hi {full_name},</p>"
            f"<p>Congratulations on completing <strong>{workshop_name}</strong>.</p>"
            "<p>Your certificate is attached as a PDF.</p>"
            "<p>Regards,<br/>Tensorik Technologies</p>"
        )
        msg.attach(MIMEText(body, "html"))

        filename = safe_certificate_filename(full_name, workshop_id)
        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(attachment)

        recipients = [recipient_email]
        if email_bcc:
            recipients.append(email_bcc)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, recipients, msg.as_string())

        return True
    except Exception as exc:
        print(f"Email failed for {registration.get('email')}: {exc}")
        return False
