import os
import streamlit as st
from supabase import create_client

# ── Supabase client ────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET       = "Recipts"


def get_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ SUPABASE_URL or SUPABASE_KEY missing from environment / secrets.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_receipt(file_name: str, pdf_bytes: bytes) -> bytes:
    """
    Upload PDF bytes to Supabase Storage bucket 'Recipts'.
    Always returns pdf_bytes so the download button works even if upload fails.
    Shows a visible Streamlit warning if upload fails.
    """
    client = get_client()

    if client is None:
        return pdf_bytes

    try:
        client.storage.from_(BUCKET).upload(
            path=file_name,
            file=pdf_bytes,
            file_options={
                "content-type": "application/pdf",
                "upsert":        "true",
            },
        )
        st.toast(f"Receipt saved to Supabase: {file_name}", icon="✅")

    except Exception as e:
        st.warning(f"⚠️ Receipt generated but could not be saved to Supabase: {e}")

    return pdf_bytes