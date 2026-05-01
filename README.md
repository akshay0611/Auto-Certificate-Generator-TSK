# 🎓 Tensorik Auto-Certificate Generator

> [!IMPORTANT]
> This is an **internal tool** used by the Admins at **Tensorik Technologies Private Limited** for generating workshop certificates and sending them to participants via email.

---

## 🚀 Admin Setup Guide (Non-Technical)

If you are an admin who hasn't used this tool before, follow these steps to get it running on your computer.

### 1. Install Python
- Download and install Python from [python.org](https://www.python.org/downloads/).
- During installation, **make sure to check the box** that says "Add Python to PATH".

### 2. Install Poppler (Required for Preview)
This tool needs a helper called "Poppler" to show you previews of the certificates.
- **Windows**: 
  1. Download the latest `poppler-...-setup.exe` from [this link](https://github.com/oschwartz10612/poppler-windows/releases/).
  2. Install it and copy the path to the `bin` folder (e.g., `C:\Program Files\poppler\bin`).
  3. Search for "Edit the system environment variables" in your Windows search bar, click "Environment Variables", find "Path", click "Edit", and add that `bin` folder path.
- **macOS**: Open your Terminal and type: `brew install poppler`.

### 3. Setup the Folder
1. Download or clone this repository to your computer.
2. Open the folder in a terminal or command prompt.
3. Create your configuration file:
   - Find the file named `.env.example`.
   - Right-click and **Rename** it to `.env` (remove the `.example`).
   - Open `.env` with Notepad or TextEdit.
   - **Note**: Ensure the `PDF_TEMPLATE_PATH` points to the correct location of the PDF file in your folder.

### 4. Configuration (The Secret Keys)
You need to fill in the values in the `.env` file. Ask your technical lead for the `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.

**Email Settings:**
- `SMTP_HOST`: The address of your email server (e.g., `smtp.gmail.com` or `smtp.hostinger.com`).
- `SMTP_PORT`: Usually `587`.
- `SMTP_USER`: Your work email (e.g., `employee@tensorik.in`).
- `SMTP_PASS`: 
  - **For Gmail**: Create an [App Password](https://myaccount.google.com/apppasswords).
  - **For Hostinger/Others**: Use your regular email password or specific SMTP password.
- `EMAIL_FROM`: The email address participants will see as the sender (e.g., `certificates@tensorik.in`).
- `EMAIL_FROM_NAME`: The name participants will see (e.g., `Tensorik Technologies`).
- `VERIFY_BASE_URL`: The link used for certificate verification (usually `https://www.tensorik.in/verify`).

### 5. Start the Tool
Open your terminal in the project folder and run:
```bash
# First time only: Install the requirements
pip install -r requirements.txt

# To start the tool:
streamlit run app.py
```
A new tab will open in your browser where you can manage the certificates.

---

## 🛠 Features
- **Workshop Selection**: Automatically fetches data from the database.
- **Real-time Calibration**: Move the name, date, and workshop title around to fit the PDF perfectly.
- **Bulk Generation**: Generate and ZIP all certificates at once.
- **Email Delivery**: Send certificates directly to participants' registered emails.

---

## 💻 Developer Setup

### Environment Variables
| Variable | Description | Default |
| :--- | :--- | :--- |
| `SUPABASE_URL` | Your Supabase project URL | (Required) |
| `SUPABASE_SERVICE_KEY` | Supabase Service Role Key (for admin access) | (Required) |
| `PDF_TEMPLATE_PATH` | Full path to the `.pdf` certificate template | (Required) |
| `CERT_OUTPUT_DIR` | Folder where generated certificates are saved | `./output` |
| `VERIFY_BASE_URL` | Base URL for the verification QR code/link | `https://www.tensorik.in/verify` |
| `SMTP_HOST` | SMTP server address (e.g., `smtp.gmail.com`) | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (usually `587` for TLS) | `587` |
| `SMTP_USER` | Email account used for authentication | (Required) |
| `SMTP_PASS` | Email password or App Password | (Required) |
| `RESEND_API_KEY` | Alias for `SMTP_PASS` (required by app logic) | (`SMTP_PASS`) |
| `EMAIL_FROM` | The actual 'From' email address | (SMTP_USER) |
| `EMAIL_FROM_NAME` | The sender name displayed in the inbox | `Tensorik Technologies` |

### Running Locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---
© 2026 **Tensorik Technologies Private Limited**. All rights reserved.
