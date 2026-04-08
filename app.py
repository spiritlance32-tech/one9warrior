import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from database import get_all_members, add_new_member, renew_member, delete_member
from receipt import generate_receipt
from storage import upload_receipt

# --- PAGE CONFIG ---
st.set_page_config(page_title="ONE9 WARRIORS", layout="centered", initial_sidebar_state="expanded")

# Plan mapping (Months)
PLANS = {"Monthly": 1, "3 Months": 3, "6 Months": 6, "1 Year": 12}

# Plan default fees
PLAN_FEES = {"Monthly": 2000, "3 Months": 5000, "6 Months": 8000, "1 Year": 15000}


# --- EXPIRY FUNCTION ---
def get_expiry(start_date, plan_name):
    months = PLANS.get(plan_name, 1)
    start_date = datetime.combine(start_date, datetime.min.time())
    return start_date + relativedelta(months=months)


# --- RECEIPT HELPER ---
# Centralises receipt generation + upload so every call site is one line
def make_receipt(name, phone, amount, plan, start_date, expiry_date):
    """
    Generate receipt PDF and upload to Supabase.
    Returns (file_name, pdf_bytes) — pdf_bytes is always available for
    the Streamlit download button even if the upload fails.
    """
    file_name, pdf_bytes = generate_receipt(
        name        = name,
        phone       = str(phone),
        amount      = f"{int(amount):,}",
        plan        = plan,
        start_date  = start_date.strftime("%d %b %Y") if hasattr(start_date, "strftime") else str(start_date),
        expiry_date = expiry_date.strftime("%d %b %Y") if hasattr(expiry_date, "strftime") else str(expiry_date),
        logo_path   = "logo.jpeg",
    )
    _, pdf_bytes = upload_receipt(file_name, pdf_bytes)
    return file_name, pdf_bytes


# --- DATA LOADING ---
today = pd.Timestamp(datetime.now().date())

try:
    data = get_all_members()
    df = pd.DataFrame(data)

    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
        df['joined_date'] = pd.to_datetime(df['joined_date'], errors='coerce')

except Exception:
    st.error("Connection Error. Check Supabase credentials.")
    st.stop()


# --- SIDEBAR: ADD MEMBER ---
with st.sidebar:
    st.header("🥋 New Admission")

    if st.session_state.get("clear_form"):
        st.session_state["enroll_name"] = ""
        st.session_state["enroll_phone"] = ""
        st.session_state["clear_form"] = False

    new_name  = st.text_input("Full Name", key="enroll_name")
    new_phone = st.text_input("Phone (Country Code first)", key="enroll_phone")
    new_plan  = st.selectbox("Select Plan", list(PLANS.keys()), key="enroll_plan")

    new_amt = st.number_input(
        "Fees Paid",
        value=PLAN_FEES.get(new_plan, 2000),
        key=f"enroll_amt_{new_plan}"
    )

    new_start = st.date_input("Start Date", value=datetime.now().date(), key="enroll_start")

    calculated_end = get_expiry(new_start, new_plan)
    st.caption(f"Will expire on: {calculated_end.date().strftime('%d %b %Y')}")

    if st.button("Enroll Student", use_container_width=True, type="primary"):
        if new_name and new_phone:
            existing = (
                df[df['phone'].astype(str).str.strip() == str(new_phone).strip()]
                if not df.empty else pd.DataFrame()
            )

            if not existing.empty:
                st.session_state["duplicate_pending"] = {
                    "id":     existing.iloc[0]['id'],
                    "name":   existing.iloc[0]['full_name'],
                    "phone":  new_phone,
                    "plan":   new_plan,
                    "start":  new_start,
                    "expiry": calculated_end,
                    "amount": new_amt,
                }
            else:
                add_new_member(new_name, new_phone, new_amt, str(new_start), str(calculated_end.date()))

                file_name, pdf_bytes = make_receipt(
                    new_name, new_phone, new_amt, new_plan,
                    new_start, calculated_end.date()
                )

                st.success(f"✅ {new_name} enrolled successfully!")

                st.download_button(
                    label="📄 Download Receipt",
                    data=pdf_bytes,
                    file_name=file_name,
                    mime="application/pdf"
                )

                msg = (f"Hi {new_name}, your admission is confirmed at ONE9 WARRIORS. "
                       f"Amount paid: Rs.{new_amt}. "
                       f"Valid till {calculated_end.date().strftime('%d %b %Y')}.")
                wa_url = f"https://wa.me/{new_phone}?text={msg.replace(' ', '%20')}"
                st.link_button("💬 Send via WhatsApp", wa_url, use_container_width=True)

                st.session_state["clear_form"] = True
                st.stop()

        else:
            st.error("Name and Phone are required.")


# --- DUPLICATE CONFIRMATION ---
if "duplicate_pending" in st.session_state:
    pending = st.session_state["duplicate_pending"]

    st.sidebar.divider()
    st.sidebar.warning(
        f"⚠️ **Duplicate Found!**\n\n"
        f"Phone **{pending['phone']}** already belongs to **{pending['name']}**.\n\n"
        f"Do you want to update their fees and renewal date instead?"
    )

    col1, col2 = st.sidebar.columns(2)

    if col1.button("✅ Yes, Update", use_container_width=True):
        renew_member(pending["id"], pending["start"], pending["expiry"], pending["amount"])

        file_name, pdf_bytes = make_receipt(
            pending["name"], pending["phone"], pending["amount"], pending["plan"],
            pending["start"], pending["expiry"].date()
        )

        st.sidebar.success(f"✅ {pending['name']}'s fees updated!")

        st.sidebar.download_button(
            label="📄 Download Receipt",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
            key="dup_receipt_dl"
        )

        msg = (f"Hi {pending['name']}, your renewal is confirmed at ONE9 WARRIORS. "
               f"Amount paid: Rs.{pending['amount']}. "
               f"Valid till {pending['expiry'].date().strftime('%d %b %Y')}.")
        wa_url = f"https://wa.me/{pending['phone']}?text={msg.replace(' ', '%20')}"
        st.sidebar.link_button("💬 Send via WhatsApp", wa_url, use_container_width=True)

        del st.session_state["duplicate_pending"]

    if col2.button("❌ Cancel", use_container_width=True):
        del st.session_state["duplicate_pending"]
        st.rerun()


# --- MAIN DASHBOARD ---
st.title("🥋 ONE9 WARRIORS Dashboard")

if not df.empty:
    active_df  = df[df['expiry_date'] >= today]
    expired_df = df[df['expiry_date'] < today]

    m1, m2, m3 = st.columns(3)
    m1.metric("Total",   len(df))
    m2.metric("Active",  len(active_df))
    m3.metric("Expired", len(expired_df), delta_color="inverse")

    search = st.text_input("🔍 Search by Name or Phone").lower()

    if search:
        df = df[
            df['full_name'].str.lower().str.contains(search) |
            df['phone'].str.contains(search)
        ]

    tab_pend, tab_act, tab_all = st.tabs(["🔴 Fees Pending", "🟢 Active", "📋 All Members"])

    def show_cards(target_df, tab_id):
        if target_df.empty:
            st.info("No students found.")
            return

        for _, row in target_df.iterrows():
            kid       = f"{tab_id}_{row['id']}"
            is_active = row['expiry_date'] >= today
            status    = "🟢" if is_active else "🔴"

            with st.expander(f"{status} {row['full_name']} | Exp: {row['expiry_date'].strftime('%d %b %Y')}"):
                st.write(f"**Phone:** {row['phone']}")

                if not is_active:
                    msg = f"Hi {row['full_name']}, your fees for ONE9 WARRIORS IS pending."
                    wa_url = f"https://wa.me/{row['phone']}?text={msg.replace(' ', '%20')}"
                    st.link_button("💬 Send WhatsApp Reminder", wa_url, use_container_width=True)

                # EDIT DATES
                with st.popover("🔧 Edit Dates", use_container_width=True):
                    ed_s = st.date_input("Start Date", value=row['joined_date'], key=f"s_{kid}")
                    ed_e = st.date_input("End Date",   value=row['expiry_date'], key=f"e_{kid}")

                    if st.button("Save Changes", key=f"sv_{kid}", use_container_width=True):
                        renew_member(row['id'], ed_s, ed_e, row['fees_amount'])
                        st.rerun()

                # MARK AS PAID (expired members only)
                if not is_active:
                    st.divider()
                    st.subheader("💰 Mark as Paid")

                    p_plan = st.selectbox(
                        "New Plan", ["-- Select --"] + list(PLANS.keys()), key=f"pl_{kid}"
                    )
                    default_fee = (
                        PLAN_FEES.get(p_plan, int(row['fees_amount']))
                        if p_plan != "-- Select --"
                        else int(row['fees_amount'])
                    )
                    p_amt  = st.number_input("Amount", value=default_fee, key=f"am_{kid}")
                    p_date = st.date_input("Payment Date", value=None, key=f"pd_{kid}")

                    if p_plan != "-- Select --" and p_date:
                        p_expiry = get_expiry(p_date, p_plan)
                        st.info(f"New Expiry: {p_expiry.date().strftime('%d %b %Y')}")

                        if st.button("Confirm Payment", key=f"bt_{kid}", type="primary", use_container_width=True):
                            renew_member(row['id'], p_date, p_expiry, p_amt)

                            file_name, pdf_bytes = make_receipt(
                                row['full_name'], row['phone'], p_amt, p_plan,
                                p_date, p_expiry.date()
                            )

                            st.success(f"✅ Payment confirmed for {row['full_name']}!")

                            st.download_button(
                                label="📄 Download Receipt",
                                data=pdf_bytes,
                                file_name=file_name,
                                mime="application/pdf",
                                key=f"dl_{kid}"
                            )

                            msg = (f"Hi {row['full_name']}, your renewal is confirmed at ONE9 WARRIORS. "
                                   f"Amount paid: Rs.{p_amt}. "
                                   f"Valid till {p_expiry.date().strftime('%d %b %Y')}.")
                            wa_url = f"https://wa.me/{row['phone']}?text={msg.replace(' ', '%20')}"
                            st.link_button("💬 Send via WhatsApp", wa_url, use_container_width=True)

                    elif p_plan != "-- Select --" and not p_date:
                        st.warning("⚠️ Please select a payment date to calculate expiry.")

                # DELETE
                st.divider()

                if st.button("🗑 Delete Member", key=f"del_{kid}", use_container_width=True):
                    st.session_state[f"confirm_{kid}"] = True

                if st.session_state.get(f"confirm_{kid}"):
                    st.warning("Are you sure you want to delete this member?")
                    c1, c2 = st.columns(2)

                    if c1.button("Yes, Delete", key=f"yes_{kid}"):
                        delete_member(row['id'])
                        st.success("Member deleted successfully")
                        st.rerun()

                    if c2.button("Cancel", key=f"no_{kid}"):
                        st.session_state[f"confirm_{kid}"] = False

    with tab_pend:
        show_cards(df[df['expiry_date'] < today], "pend")

    with tab_act:
        show_cards(df[df['expiry_date'] >= today], "act")

    with tab_all:
        show_cards(df, "all")

else:
    st.info("No members in database. Use the sidebar to add your first student.")