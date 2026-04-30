from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE_PATH = str(ROOT_DIR / "TENSORIK WORKSHOP CERTIFICATE.pdf")
DEFAULT_VERIFY_BASE_URL = "https://www.tensorik.in/verify"

STRINGS = {
    "app_title": "Auto Certificate Generator",
    "app_caption": "Generate workshop certificates from Supabase registrations.",
    "sidebar_title": "Filters",
    "workshop_select": "Select Workshop",
    "search_name": "Search by participant name",
    "metrics_total": "Total Registrations",
    "metrics_sent": "Sent",
    "metrics_pending": "Pending",
    "preview_header": "Certificate Preview",
    "preview_help": "Pick one participant to preview and calibrate text placement.",
    "single_download_header": "Single Certificate Download",
    "bulk_header": "Bulk Generation",
    "generate_all": "Generate All Certificates",
    "download_zip": "Download ZIP",
    "template_missing": "PDF template not found at configured path.",
    "email_subject": "Your Certificate — {workshop_name}",
    "email_already_sent": "Already sent on {date}",
    "email_send_success": "Certificate sent to {email}",
    "email_send_failed": "Failed to send to {email}",
}

DEFAULT_CERT_SETTINGS = {
    "date_mode": "generation_date",
    "VERIFY_BASE_URL": DEFAULT_VERIFY_BASE_URL,
    "cleanup": {
        "hide_left_logo_line": False,
        "left_logo_line_boxes": [],
    },
    "name": {
        "x": 165,
        "y": 480,
        "font_name": "Helvetica",
        "font_size": 36,
        "color_hex": "#3A3A3A",
        "align": "left",
    },
    "workshop": {
        "x": 165,
        "y": 328,
        "font_name": "Helvetica",
        "font_size": 28,
        "color_hex": "#3A3A3A",
        "align": "left",
    },
    "date": {
        "x": 165,
        "y": 608,
        "font_name": "Helvetica",
        "font_size": 16,
        "color_hex": "#6F6F6F",
        "format": "%d %b %Y",
        "align": "left",
    },
    "verify_text": {
        "x": 840,
        "y": 132,
        "font_name": "Helvetica",
        "font_size": 11,
        "color_hex": "#1A73E8",
        "align": "center",
    },
}


def _get_secret_or_env(key: str, default: str | None = None) -> str | None:
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


def get_app_config() -> dict[str, Any]:
    config = {
        "SUPABASE_URL": _get_secret_or_env("SUPABASE_URL"),
        "SUPABASE_SERVICE_KEY": _get_secret_or_env("SUPABASE_SERVICE_KEY"),
        "PDF_TEMPLATE_PATH": _get_secret_or_env("PDF_TEMPLATE_PATH", DEFAULT_TEMPLATE_PATH),
        "CERT_OUTPUT_DIR": _get_secret_or_env("CERT_OUTPUT_DIR", str(ROOT_DIR / "output")),
        "VERIFY_BASE_URL": _get_secret_or_env("VERIFY_BASE_URL", DEFAULT_VERIFY_BASE_URL),
        "SMTP_HOST": _get_secret_or_env("SMTP_HOST", "smtp.gmail.com"),
        "SMTP_PORT": _get_secret_or_env("SMTP_PORT", "587"),
        "SMTP_USER": _get_secret_or_env("SMTP_USER"),
        "SMTP_PASS": _get_secret_or_env("SMTP_PASS"),
        "EMAIL_FROM_NAME": _get_secret_or_env("EMAIL_FROM_NAME", "Tensorik Technologies"),
    }
    config["RESEND_API_KEY"] = config["SMTP_PASS"]
    config["RESEND_FROM_EMAIL"] = config["SMTP_USER"]
    config["RESEND_FROM_NAME"] = config["EMAIL_FROM_NAME"]
    return config


def get_certificate_settings() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_CERT_SETTINGS)


def validate_required_config(config: dict[str, Any]) -> list[str]:
    missing = [
        key
        for key in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "PDF_TEMPLATE_PATH")
        if not config.get(key)
    ]
    template_path = config.get("PDF_TEMPLATE_PATH")
    if template_path and not Path(template_path).exists():
        missing.append("PDF_TEMPLATE_PATH (file does not exist)")
    return missing
