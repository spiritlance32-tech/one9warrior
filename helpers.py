from receipt import generate_receipt
from storage import upload_receipt


def make_receipt(
    name,
    phone,
    amount,
    plan,
    start_date,
    expiry_date,
):
    """
    Generate a receipt, upload it to Supabase Storage,
    and return the filename and PDF bytes.
    """

    file_name, pdf_bytes = generate_receipt(
        name=name,
        phone=str(phone),
        amount=f"{int(amount):,}",
        plan=plan,
        start_date=start_date.strftime("%d %b %Y"),
        expiry_date=expiry_date.strftime("%d %b %Y"),
        logo_path="assets/logo.jpeg",
    )

    pdf_bytes = upload_receipt(file_name, pdf_bytes)

    return file_name, pdf_bytes