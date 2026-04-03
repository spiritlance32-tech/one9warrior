import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_all_members, add_new_member, renew_member, delete_member

# --- PAGE CONFIG ---
st.set_page_config(page_title="ONE9 WARRIORS", layout="centered", initial_sidebar_state="expanded")

# Plan mapping (Months)
PLANS = {"Monthly": 1, "3 Months": 3, "6 Months": 6, "1 Year": 12}

def get_expiry(start_date, plan_name):
    months = PLANS.get(plan_name, 1)
    return start_date + timedelta(days=30 * months)

# --- 1. DATA LOADING ---
today = pd.Timestamp(datetime.now().date())
try:
    data = get_all_members()
    df = pd.DataFrame(data)
    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
        df['joined_date'] = pd.to_datetime(df['joined_date'], errors='coerce')
except Exception as e:
    st.error("Connection Error. Check Supabase credentials.")
    st.stop()

# --- 2. SIDEBAR: ADD MEMBER ---
with st.sidebar:
    st.header("🥋 New Admission")
    with st.form("add_member_form", clear_on_submit=True):
        new_name = st.text_input("Full Name")
        new_phone = st.text_input("Phone (Country Code first)")
        new_plan = st.selectbox("Select Plan", list(PLANS.keys()))
        new_amt = st.number_input("Fees Paid", value=100)
        new_start = st.date_input("Start Date", value=datetime.now().date())
        
        calculated_end = get_expiry(new_start, new_plan)
        st.caption(f"Will expire on: {calculated_end.strftime('%d %b %Y')}")
        
        if st.form_submit_button("Enroll Student", use_container_width=True):
            if new_name and new_phone:
                add_new_member(new_name, new_phone, new_amt, str(new_start), str(calculated_end))
                st.success(f"Added {new_name}!")
                st.rerun()
            else:
                st.error("Name and Phone are required.")

# --- 3. MAIN DASHBOARD ---
st.title("🥋 ONE9 WARRIORS Dashboard")

if not df.empty:
    active_df = df[df['expiry_date'] >= today]
    expired_df = df[df['expiry_date'] < today]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total", len(df))
    m2.metric("Active", len(active_df))
    m3.metric("Expired", len(expired_df), delta_color="inverse")

    # Search
    search = st.text_input("🔍 Search by Name or Phone").lower()
    if search:
        df = df[df['full_name'].str.lower().str.contains(search) | df['phone'].str.contains(search)]

    tab_pend, tab_act, tab_all = st.tabs(["🔴 Fees Pending", "🟢 Active", "📋 All Members"])

    def show_cards(target_df, tab_id):
        if target_df.empty:
            st.info("No students found.")
            return
        
        for _, row in target_df.iterrows():
            kid = f"{tab_id}_{row['id']}"
            is_active = row['expiry_date'] >= today
            status = "🟢" if is_active else "🔴"
            
            with st.expander(f"{status} {row['full_name']} | Exp: {row['expiry_date'].strftime('%d %b')}"):
                st.write(f"**Phone:** {row['phone']}")

                # WhatsApp Reminder
                if not is_active:
                    msg = f"Hi {row['full_name']}, your fees for ONE9 WARRIORS IS pending."
                    wa_url = f"https://wa.me/{row['phone']}?text={msg.replace(' ', '%20')}"
                    st.link_button("💬 Send WhatsApp Reminder", wa_url, use_container_width=True)

                # --- EDIT DATES ---
                with st.popover("🔧 Edit Dates", use_container_width=True):
                    ed_s = st.date_input("Start Date", value=row['joined_date'], key=f"s_{kid}")
                    ed_e = st.date_input("End Date", value=row['expiry_date'], key=f"e_{kid}")
                    if st.button("Save Changes", key=f"sv_{kid}", use_container_width=True):
                        renew_member(row['id'], ed_s, ed_e, row['fees_amount'])
                        st.rerun()

                # --- MARK AS PAID ---
                if not is_active:
                    st.divider()
                    st.subheader("💰 Mark as Paid")
                    p_plan = st.selectbox("New Plan", ["-- Select --"] + list(PLANS.keys()), key=f"pl_{kid}")
                    p_amt = st.number_input("Amount", value=int(row['fees_amount']), key=f"am_{kid}")
                    
                    if p_plan != "-- Select --":
                        p_expiry = get_expiry(datetime.now().date(), p_plan)
                        st.info(f"New Expiry: {p_expiry.strftime('%d %b %Y')}")
                        if st.button("Confirm Payment", key=f"bt_{kid}", type="primary", use_container_width=True):
                            renew_member(row['id'], datetime.now().date(), p_expiry, p_amt)
                            st.rerun()

                # --- 🔥 DELETE FEATURE ---
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
