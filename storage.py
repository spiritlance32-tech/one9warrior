import os
from supabase import create_client

# ── Supabase client ────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Bucket name (as it exists in your Supabase dashboard) ──────
BUCKET = "Recipts"


def upload_receipt(file_name: str, pdf_bytes: bytes) -> tuple[str, bytes]:
    """
    Upload PDF bytes to Supabase Storage bucket 'Recipts'.

    Returns:
        signed_url  — temporary download URL valid for 1 hour
        pdf_bytes   — same bytes passed in (so Streamlit can use them directly)
    """
    try:
        supabase.storage.from_(BUCKET).upload(
            path=file_name,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )

        signed = supabase.storage.from_(BUCKET).create_signed_url(file_name, 3600)
        signed_url = signed.get("signedURL") or signed.get("signedUrl", "")

        return signed_url, pdf_bytes

    except Exception as e:
        # If upload fails for any reason, still return bytes so download works
        print(f"[Storage] Upload failed: {e}")
        return None, pdf_bytes