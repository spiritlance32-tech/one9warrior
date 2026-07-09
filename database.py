import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_all_members():
    response = supabase.table("members").select("*").execute()
    print("SUPABASE RESPONSE:", response)
    return response.data

def add_new_member(name, phone, amount, start_date, expiry_date):
    # Inserts a new student
    data = {
        "full_name": name,
        "phone": phone,
        "fees_amount": amount,
        "last_payment_date": start_date,
        "expiry_date": expiry_date
    }
    response = supabase.table("members").insert(data).execute()
    return response

def update_member_payment(member_id, new_expiry, amount):
    # Updates payment for an existing student
    data = {
        "last_payment_date": "now()",
        "expiry_date": new_expiry,
        "fees_amount": amount
    }
    response = supabase.table("members").update(data).eq("id", member_id).execute()
    return response

def renew_member(member_id, start_date, expiry_date, amount):
    """Updates a member's subscription when they pay again."""
    data = {
        "last_payment_date": str(start_date),
        "expiry_date": str(expiry_date),
        "fees_amount": amount
    }
    response = supabase.table("members").update(data).eq("id", member_id).execute()
    return response

def delete_member(member_id):
    response = supabase.table("members").delete().eq("id", member_id).execute()
    return response

def add_payment(
    member_id,
    amount,
    payment_date,
    expiry_date,
    plan,
    discount,
    payment_mode,
    receipt_file_name,
    receipt_url,
):
    data = {
        "member_id": member_id,
        "amount_paid": amount,
        "payment_date": str(payment_date),
        "valid_until": str(expiry_date),
        "plan": plan,
        "discount": discount,
        "payment_mode": payment_mode,
        "receipt_file_name": receipt_file_name,
        "receipt_url": receipt_url,
    }

    return (
        supabase.table("payments")
        .insert(data)
        .execute()
    )
def get_payment_history(member_id):
    response = (
        supabase.table("payments")
        .select("*")
        .eq("member_id", member_id)
        .order("payment_date", desc=True)
        .execute()
    )

    return response.data

def get_all_payments():

    response = (
        supabase.table("payments")
        .select(
            """
            *,
            members (
                full_name,
                phone
            )
            """
        )
        .order("payment_date", desc=True)
        .execute()
    )

    return response.data

def update_member_status(member_id, status):
    return (
        supabase.table("members")
        .update({"status": status})
        .eq("id", member_id)
        .execute()
    )