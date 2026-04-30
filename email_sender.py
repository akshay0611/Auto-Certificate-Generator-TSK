from __future__ import annotations

import base64
from typing import Any

from pdf_generator import safe_certificate_filename


def send_certificate_email(registration: dict[str, Any], pdf_bytes: bytes, settings: dict[str, Any]) -> bool:
    try:
        import resend

        api_key = settings["RESEND_API_KEY"]
        from_email = settings["RESEND_FROM_EMAIL"]
        from_name = settings["RESEND_FROM_NAME"]
        strings = settings["STRINGS"]

        recipient_email = str(registration.get("email") or "").strip()
        if not recipient_email:
            return False

        workshop_name = str(
            registration.get("workshop_title")
            or registration.get("workshop_id")
            or "Workshop"
        )
        full_name = str(registration.get("full_name") or "Participant")
        workshop_id = str(registration.get("workshop_id") or "workshop")

        resend.api_key = api_key
        subject = strings["email_subject"].format(workshop_name=workshop_name)
        html = (
            f"<p>Hi {full_name},</p>"
            f"<p>Congratulations on completing <strong>{workshop_name}</strong>.</p>"
            "<p>Your certificate is attached as a PDF.</p>"
            "<p>Regards,<br/>Tensorik Technologies</p>"
        )

        resend.Emails.send(
            {
                "from": f"{from_name} <{from_email}>",
                "to": [recipient_email],
                "subject": subject,
                "html": html,
                "attachments": [
                    {
                        "filename": safe_certificate_filename(full_name, workshop_id),
                        "content": base64.b64encode(pdf_bytes).decode("utf-8"),
                    }
                ],
            }
        )
        return True
    except Exception:
        return False
