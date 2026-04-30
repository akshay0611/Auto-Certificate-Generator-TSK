from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from bulk_generator import generate_zip
from config import (
    STRINGS,
    get_app_config,
    get_certificate_settings,
    validate_required_config,
)
from db import get_client, get_registrations, get_workshop_ids, has_certificate_sent_column
from db import get_workshop_titles
from db import mark_certificate_sent
from email_sender import send_certificate_email
from pdf_generator import generate_certificate, render_preview_image, safe_certificate_filename


st.set_page_config(page_title=STRINGS["app_title"], layout="wide")
st.title(STRINGS["app_title"])
st.caption(STRINGS["app_caption"])

config = get_app_config()
missing_config = validate_required_config(config)
if missing_config:
    st.error(
        "Missing/invalid configuration: "
        + ", ".join(missing_config)
        + ". Please update `.env` or `st.secrets`."
    )
    st.stop()

try:
    supabase = get_client(config["SUPABASE_URL"], config["SUPABASE_SERVICE_KEY"])
except Exception as exc:
    st.error(f"Failed to initialize Supabase client: {exc}")
    st.stop()

if "cert_settings" not in st.session_state:
    st.session_state.cert_settings = get_certificate_settings()

settings = st.session_state.cert_settings
settings["VERIFY_BASE_URL"] = config["VERIFY_BASE_URL"]
settings["RESEND_API_KEY"] = config.get("RESEND_API_KEY")
settings["RESEND_FROM_EMAIL"] = config.get("RESEND_FROM_EMAIL")
settings["RESEND_FROM_NAME"] = config.get("RESEND_FROM_NAME")
settings["STRINGS"] = STRINGS

with st.sidebar:
    st.header(STRINGS["sidebar_title"])
    try:
        workshop_ids = get_workshop_ids(supabase)
        workshop_titles = get_workshop_titles(supabase)
    except Exception as exc:
        st.error(f"Unable to load workshop IDs: {exc}")
        st.stop()

    if not workshop_ids:
        st.warning("No workshop registrations found.")
        st.stop()

    selected_workshop = st.selectbox(
        STRINGS["workshop_select"],
        workshop_ids,
        format_func=lambda workshop_slug: workshop_titles.get(workshop_slug, workshop_slug),
    )
    search_text = st.text_input(STRINGS["search_name"], "")

    settings["date_mode"] = st.radio(
        "Date Source",
        options=["generation_date", "registration_date"],
        index=0 if settings["date_mode"] == "generation_date" else 1,
    )

    st.subheader("Calibration")
    if st.button("Reset to line-matched preset"):
        st.session_state.cert_settings = get_certificate_settings()
        settings = st.session_state.cert_settings
        st.success("Applied line-matched preset for date/name/workshop.")
    for field in ("name", "workshop", "date", "verify_text"):
        st.markdown(f"**{field.title()}**")
        settings[field]["x"] = st.slider(
            f"{field} X", 0, 2000, int(settings[field]["x"]), key=f"{field}_x"
        )
        settings[field]["y"] = st.slider(
            f"{field} Y", 0, 1200, int(settings[field]["y"]), key=f"{field}_y"
        )
        settings[field]["font_size"] = st.slider(
            f"{field} Font Size", 8, 120, int(settings[field]["font_size"]), key=f"{field}_size"
        )
        settings[field]["align"] = st.selectbox(
            f"{field} Alignment",
            options=["left", "center", "right"],
            index=["left", "center", "right"].index(settings[field].get("align", "center")),
            key=f"{field}_align",
        )
        settings[field]["color_hex"] = st.color_picker(
            f"{field} Color", settings[field]["color_hex"], key=f"{field}_color"
        )

try:
    registrations = get_registrations(supabase, selected_workshop)
except Exception as exc:
    st.error(f"Failed to load registrations: {exc}")
    st.stop()

selected_workshop_title = workshop_titles.get(selected_workshop, selected_workshop)
for row in registrations:
    row["workshop_title"] = selected_workshop_title

if search_text.strip():
    normalized = search_text.strip().lower()
    registrations = [
        row
        for row in registrations
        if normalized in str(row.get("full_name", "")).lower()
    ]

has_sent_column = has_certificate_sent_column(supabase)
total_count = len(registrations)
sent_count = (
    len([row for row in registrations if row.get("certificate_sent_at")]) if has_sent_column else 0
)
pending_count = total_count - sent_count if has_sent_column else total_count

metric_cols = st.columns(3)
metric_cols[0].metric(STRINGS["metrics_total"], total_count)
metric_cols[1].metric(STRINGS["metrics_sent"], sent_count if has_sent_column else "N/A")
metric_cols[2].metric(STRINGS["metrics_pending"], pending_count)

table_rows = []
for row in registrations:
    status_value = "⏳ Pending"
    sent_value = row.get("certificate_sent_at")
    if sent_value:
        status_value = f"✅ Sent ({sent_value})"
    item = {
        "full_name": row.get("full_name"),
        "email": row.get("email"),
        "created_at": row.get("created_at"),
        "status": status_value,
    }
    if has_sent_column:
        item["certificate_sent_at"] = row.get("certificate_sent_at")
    table_rows.append(item)

st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

if not config.get("RESEND_API_KEY"):
    st.warning("Email sending is disabled until `RESEND_API_KEY` is configured.")

st.subheader("Email Delivery")
pending_rows = [row for row in registrations if row.get("certificate_sent_at") is None]
if st.button("Send All Pending", type="primary", disabled=not config.get("RESEND_API_KEY")):
    progress = st.progress(0.0)
    status_box = st.empty()
    failures: list[dict[str, str]] = []
    total_pending = len(pending_rows)
    if total_pending == 0:
        status_box.info("No pending registrations to send.")
    else:
        for index, registration in enumerate(pending_rows, start=1):
            email = str(registration.get("email") or "")
            name = str(registration.get("full_name") or "Participant")
            status_box.info(f"Sending: {name}")
            try:
                pdf_bytes = generate_certificate(registration, settings, config["PDF_TEMPLATE_PATH"])
                is_sent = send_certificate_email(registration, pdf_bytes, settings)
                if is_sent:
                    mark_certificate_sent(str(registration["id"]))
                else:
                    failures.append({"name": name, "email": email, "error": "send failed"})
            except Exception as exc:
                failures.append({"name": name, "email": email, "error": str(exc)})
            progress.progress(index / total_pending)
        status_box.success("Send-all run finished.")
        if failures:
            st.warning(f"{len(failures)} email(s) failed.")
            st.dataframe(pd.DataFrame(failures), use_container_width=True, hide_index=True)
        st.rerun()

st.markdown("**Send per participant**")
for registration in registrations:
    full_name = str(registration.get("full_name") or "Participant")
    email = str(registration.get("email") or "")
    sent_at = registration.get("certificate_sent_at")
    row_cols = st.columns([3, 3, 2, 2])
    row_cols[0].write(full_name)
    row_cols[1].write(email)
    if sent_at:
        row_cols[2].write(STRINGS["email_already_sent"].format(date=sent_at))
        row_cols[3].button("Send", key=f"send_{registration.get('id')}", disabled=True)
        continue

    send_clicked = row_cols[3].button(
        "Send",
        key=f"send_{registration.get('id')}",
        disabled=not config.get("RESEND_API_KEY"),
    )
    if send_clicked:
        try:
            pdf_bytes = generate_certificate(registration, settings, config["PDF_TEMPLATE_PATH"])
            is_sent = send_certificate_email(registration, pdf_bytes, settings)
            if is_sent:
                mark_certificate_sent(str(registration["id"]))
                st.success(STRINGS["email_send_success"].format(email=email))
                st.rerun()
            else:
                st.error(STRINGS["email_send_failed"].format(email=email))
        except Exception:
            st.error(STRINGS["email_send_failed"].format(email=email))

if not registrations:
    st.info("No registrations match your current filters.")
    st.stop()

st.subheader(STRINGS["preview_header"])
st.caption(STRINGS["preview_help"])

participant_options = {
    f"{entry.get('full_name', 'Participant')} ({entry.get('email', 'no-email')})": entry
    for entry in registrations
}
selected_label = st.selectbox("Preview Participant", list(participant_options.keys()))
selected_registration = participant_options[selected_label]

try:
    preview_pdf = generate_certificate(
        selected_registration,
        settings,
        config["PDF_TEMPLATE_PATH"],
    )
    preview_png = render_preview_image(preview_pdf)
    st.image(preview_png, caption="Preview", use_container_width=True)
except Exception as exc:
    st.error(f"Preview failed: {exc}")

st.subheader(STRINGS["single_download_header"])
download_cols = st.columns(min(3, len(registrations)))
for index, registration in enumerate(registrations):
    try:
        cert_bytes = generate_certificate(registration, settings, config["PDF_TEMPLATE_PATH"])
        cert_filename = safe_certificate_filename(
            str(registration.get("full_name") or "Participant"),
            selected_workshop,
        )
        with download_cols[index % len(download_cols)]:
            st.download_button(
                label=f"Download {registration.get('full_name', 'Participant')}",
                data=cert_bytes,
                file_name=cert_filename,
                mime="application/pdf",
                key=f"single_download_{registration.get('id', index)}",
            )
    except Exception as exc:
        st.warning(f"Skipping {registration.get('full_name', 'Participant')}: {exc}")

st.subheader(STRINGS["bulk_header"])
if st.button(STRINGS["generate_all"], type="primary"):
    progress = st.progress(0.0)
    status = st.empty()

    def _progress_callback(current: int, total: int, message: str) -> None:
        pct = current / total if total else 1
        progress.progress(min(max(pct, 0.0), 1.0))
        status.info(message)

    zip_bytes, failures = generate_zip(
        registrations=registrations,
        settings=settings,
        template_path=config["PDF_TEMPLATE_PATH"],
        progress_cb=_progress_callback,
    )
    progress.progress(1.0)
    status.success("Bulk generation complete.")
    st.download_button(
        STRINGS["download_zip"],
        data=zip_bytes,
        file_name=f"certificates_{selected_workshop}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip",
    )
    if failures:
        st.warning(f"{len(failures)} certificate(s) failed.")
        st.dataframe(pd.DataFrame(failures), use_container_width=True, hide_index=True)
