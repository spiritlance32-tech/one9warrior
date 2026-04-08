import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET       = "Recipts"

print(f"URL  : {SUPABASE_URL}")
print(f"KEY  : {SUPABASE_KEY[:30]}...")   # only prints first 30 chars for safety
print()

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test: list buckets
try:
    buckets = client.storage.list_buckets()
    print("✅ Connected. Buckets found:")
    for b in buckets:
        print(f"   - {b.name}  (id: {b.id})")
except Exception as e:
    print(f"❌ Could not list buckets: {e}")

print()

# Test: upload a tiny test file
try:
    test_bytes = b"test pdf content"
    client.storage.from_(BUCKET).upload(
        path="test_debug.pdf",
        file=test_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"}
    )
    print(f"✅ Upload to '{BUCKET}' succeeded!")
except Exception as e:
    print(f"❌ Upload failed: {e}")
