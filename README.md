# Auto Certificate Generator (No-Email v1)

Streamlit app for generating workshop certificates from Supabase registrations using a fixed PDF template.

## Features
- Supabase (service key) powered workshop dropdown + registration table.
- In-app certificate calibration (X/Y, font size, color) for name/workshop/date.
- Single-certificate preview and per-participant download.
- Bulk generation with progress and ZIP download.
- Optional `certificate_sent_at` column display (read-only).

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill values.
3. Ensure your template file path is valid (`PDF_TEMPLATE_PATH`).

## Run
```bash
streamlit run app.py
```

## Environment Variables
- `SUPABASE_URL` (required)
- `SUPABASE_SERVICE_KEY` (required, service role key)
- `PDF_TEMPLATE_PATH` (required)
- `CERT_OUTPUT_DIR` (optional, default `./output`)

## Notes
- Generate an App Password at `myaccount.google.com` → Security → 2-Step Verification → App Passwords. Use this as `SMTP_PASS`.
- `pdf2image` requires Poppler:
  - macOS (Homebrew): `brew install poppler`
  - Ubuntu: `sudo apt-get install poppler-utils`
  - Windows: install Poppler and add its `bin` folder to `PATH`.
