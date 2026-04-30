from __future__ import annotations

import io
import zipfile

import bulk_generator
from pdf_generator import safe_certificate_filename


def test_safe_filename() -> None:
    result = safe_certificate_filename("Ava Sharma / Lead", "AI Workshop #1")
    assert result == "Ava_Sharma__Lead_AI_Workshop_1.pdf"


def test_bulk_zip_generation() -> None:
    original_generator = bulk_generator.generate_certificate

    def fake_generator(registration, settings, template_path):  # noqa: ANN001
        if registration["full_name"] == "Fail User":
            raise ValueError("Intentional failure for smoke test")
        return f"PDF::{registration['full_name']}".encode("utf-8")

    bulk_generator.generate_certificate = fake_generator
    try:
        rows = [
            {"full_name": "Alice Doe", "workshop_id": "WK-101"},
            {"full_name": "Fail User", "workshop_id": "WK-101"},
            {"full_name": "Bob Roe", "workshop_id": "WK-101"},
        ]
        zip_bytes, failures = bulk_generator.generate_zip(
            registrations=rows,
            settings={},
            template_path="unused.pdf",
        )

        assert len(failures) == 1
        assert failures[0]["name"] == "Fail User"

        bundle = zipfile.ZipFile(io.BytesIO(zip_bytes))
        names = sorted(bundle.namelist())
        assert names == ["Alice_Doe_WK-101.pdf", "Bob_Roe_WK-101.pdf"]
    finally:
        bulk_generator.generate_certificate = original_generator


if __name__ == "__main__":
    test_safe_filename()
    test_bulk_zip_generation()
    print("Smoke tests passed.")
