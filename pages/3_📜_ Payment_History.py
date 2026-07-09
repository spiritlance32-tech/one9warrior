import streamlit as st
import pandas as pd

from database import get_all_payments

st.set_page_config(page_title="Payment History", page_icon="📜", layout="wide")
st.title("📜 Payment History")

payments = get_all_payments()

if not payments:
    st.info("No payments found.")
    st.stop()


def get_member_value(row, key):
    members = row.get("members")
    if isinstance(members, dict):
        return members.get(key, "")
    return ""


df = pd.DataFrame(payments)

df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
df["Name"] = df.apply(lambda row: get_member_value(row, "full_name"), axis=1)
df["Phone"] = df.apply(lambda row: get_member_value(row, "phone"), axis=1)

period = st.selectbox(
    "View",
    ["Today", "This Week", "This Month", "This Year", "All Time"],
)

today = pd.Timestamp.today().normalize()
filtered_df = df.copy()

if period == "Today":
    filtered_df = filtered_df[filtered_df["payment_date"].dt.normalize() == today]
elif period == "This Week":
    start_week = today - pd.Timedelta(days=today.weekday())
    filtered_df = filtered_df[filtered_df["payment_date"].dt.normalize() >= start_week]
elif period == "This Month":
    filtered_df = filtered_df[
        (filtered_df["payment_date"].dt.month == today.month)
        & (filtered_df["payment_date"].dt.year == today.year)
    ]
elif period == "This Year":
    filtered_df = filtered_df[filtered_df["payment_date"].dt.year == today.year]

show_df = filtered_df[["payment_date", "Name", "Phone", "plan", "amount_paid", "payment_mode"]].copy()
show_df["Date"] = show_df["payment_date"].dt.strftime("%d %b %Y")
show_df["Amount"] = show_df["amount_paid"].fillna(0).astype(float)
show_df = show_df[["Date", "Name", "Phone", "plan", "Amount", "payment_mode"]].rename(columns={
    "plan": "Plan",
    "payment_mode": "Payment Mode",
})

col1, col2 = st.columns(2)
with col1:
    st.metric("Payments", len(show_df))
with col2:
    st.metric("Total Amount", f"₹{show_df['Amount'].sum():,.0f}")

st.dataframe(show_df, use_container_width=True, hide_index=True)