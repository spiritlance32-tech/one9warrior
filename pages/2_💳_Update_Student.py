import streamlit as st


from database import get_all_members, renew_member, add_payment, get_payment_history
from receipt import generate_receipt
from storage import upload_receipt
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(
    page_title="Update Student",
    page_icon="💳",
    layout="centered"
)

st.title("💳 Update Student")

# Load all members
members = get_all_members()

if not members:
    st.warning("No members found.")
    st.stop()

# -------------------------
# Search Student
# -------------------------
search = st.text_input(
    "🔍 Search Student",
    placeholder="Type name or phone..."
)

filtered_members = members

if search:
    search = search.lower()

    filtered_members = [
        m for m in members
        if search in m["full_name"].lower()
        or search in str(m["phone"])
    ]

if len(filtered_members) == 0:
    st.warning("No student found.")
    st.stop()

selected_member = st.selectbox(
    "Select Student",
    filtered_members,
    format_func=lambda x: f"{x['full_name']} ({x['phone']})"
)

st.divider()

st.subheader("Current Details")

st.write(f"**Name:** {selected_member['full_name']}")
st.write(f"**Phone:** {selected_member['phone']}")
st.write(f"**Fees Paid:** ₹{selected_member['fees_amount']}")
st.write(f"**Expiry Date:** {selected_member['expiry_date']}")
st.divider()


PLANS = {
    "Monthly": 1,
    "3 Months": 3,
    "6 Months": 6,
    "1 Year": 12,
}

PLAN_FEES = {
    "Monthly": 2000,
    "3 Months": 5000,
    "6 Months": 8000,
    "1 Year": 15000,
}

st.subheader("💰 Renew Membership")

plan = st.selectbox(
    "Membership Plan",
    list(PLANS.keys())
)

standard_fee = PLAN_FEES[plan]

if "discount" not in st.session_state:
    st.session_state.discount = 0

if "amount" not in st.session_state:
    st.session_state.amount = standard_fee

# Reset values when plan changes
if st.session_state.amount > standard_fee:
    st.session_state.amount = standard_fee
    st.session_state.discount = 0

st.info(f"💰 Standard Fee : ₹{standard_fee:,}")

col1, col2 = st.columns(2)

with col1:

    discount = st.number_input(
        "Discount",
        min_value=0,
        max_value=standard_fee,
        value=st.session_state.discount,
        step=100,
    )

with col2:

    amount = st.number_input(
        "Fees Paid",
        min_value=0,
        value=standard_fee - discount,
        step=100,
    )

# Keep both values synchronized
discount = standard_fee - amount

st.session_state.discount = discount
st.session_state.amount = amount

st.divider()

st.metric("Final Amount", f"₹{amount:,}")

payment_mode = st.selectbox(
    "Payment Mode",
    [
        "Cash",
        "UPI",
        "Card",
        "Bank Transfer"
    ]
)

payment_date = st.date_input(
    "Payment Date",
    value=datetime.today()
)

expiry_date = payment_date + relativedelta(
    months=PLANS[plan]
)

st.success(
    f"Membership will expire on **{expiry_date.strftime('%d %b %Y')}**"
)

update_btn = st.button(
    "✅ Update Membership",
    use_container_width=True,
    type="primary"
)

# --------------------------------------------------
# UPDATE MEMBERSHIP
# --------------------------------------------------

st.divider()

if update_btn:

    try:
        # Update member in database
        renew_member(
            selected_member["id"],
            payment_date,
            expiry_date,
            amount
        )

        # Generate receipt
        file_name, pdf_bytes = generate_receipt(
            selected_member["full_name"],
            selected_member["phone"],
            amount,
            plan,
            payment_date,
            expiry_date
        )

        add_payment(
    member_id=selected_member["id"],
    amount=amount,
    payment_date=payment_date,
    expiry_date=expiry_date,
    plan=plan,
    discount=discount,
    payment_mode=payment_mode,      # We'll make this selectable later
    receipt_file_name=file_name,
    receipt_url=None,
)

        # Upload to Supabase Storage
        pdf_bytes = upload_receipt(
            file_name,
            pdf_bytes
        )

        st.success("✅ Membership updated successfully!")

        # Download receipt
        st.download_button(
            "📄 Download Receipt",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
            use_container_width=True
        )

        # WhatsApp message
        msg = (
            f"Hi {selected_member['full_name']}, "
            f"your membership at ONE9 WARRIORS has been renewed.\n\n"
            f"Plan: {plan}\n"
            f"Amount Paid: ₹{amount}\n"
            f"Valid Till: {expiry_date.strftime('%d %b %Y')}"
        )

        wa_url = (
            f"https://wa.me/{selected_member['phone']}?"
            f"text={msg.replace(' ', '%20').replace(chr(10), '%0A')}"
        )

        st.markdown(f"[💬 Send via WhatsApp]({wa_url})")

    except Exception as e:
        st.error(f"Error updating membership: {e}")

st.divider()
st.subheader("📜 Payment History")

history = get_payment_history(selected_member["id"])

if not history:
    st.info("No payment history found.")

else:
    for payment in history:

        with st.expander(
            f"₹{payment['amount_paid']} • {payment['payment_date']}"
        ):

            st.write(f"**Plan:** {payment['plan']}")
            st.write(f"**Amount:** ₹{payment['amount_paid']}")
            st.write(f"**Payment Date:** {payment['payment_date']}")
            st.write(f"**Valid Till:** {payment['valid_until']}")
            st.write(f"**Payment Mode:** {payment['payment_mode']}")

            if payment["receipt_file_name"]:
                st.caption(payment["receipt_file_name"])




