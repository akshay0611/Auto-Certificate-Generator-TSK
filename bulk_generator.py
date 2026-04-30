from __future__ import annotations

import io
import zipfile
from typing import Any, Callable

from pdf_generator import generate_certificate, safe_certificate_filename


ProgressCallback = Callable[[int, int, str], None]


def generate_zip(
    registrations: list[dict[str, Any]],
    settings: dict[str, Any],
    template_path: str,
    progress_cb: ProgressCallback | None = None,
) -> tuple[bytes, list[dict[str, str]]]:
    zip_buffer = io.BytesIO()
    failures: list[dict[str, str]] = []
    total = len(registrations)

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for index, registration in enumerate(registrations, start=1):
            full_name = str(registration.get("full_name") or "Participant")
            workshop_id = str(registration.get("workshop_id") or "Workshop")
            try:
                pdf_bytes = generate_certificate(registration, settings, template_path)
                filename = safe_certificate_filename(full_name, workshop_id)
                bundle.writestr(filename, pdf_bytes)
                if progress_cb:
                    progress_cb(index, total, f"Generated: {full_name}")
            except Exception as exc:
                failures.append({"name": full_name, "error": str(exc)})
                if progress_cb:
                    progress_cb(index, total, f"Failed: {full_name}")

    zip_buffer.seek(0)
    return zip_buffer.getvalue(), failures
