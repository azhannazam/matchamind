import streamlit as st
import requests

st.set_page_config(page_title="MatchaMind", page_icon="🍵")

st.title("🍵 MatchaMind")
st.markdown("Your AI-Powered Expense Companion")

# Test backend connection
if st.button("Test Connection"):
    try:
        response = requests.get("http://localhost:8000/api/test")
        if response.status_code == 200:
            st.success("✅ Connected to backend!")
            st.json(response.json())
    except:
        st.error("❌ Backend not running. Start it first!")

# Simple expense input
st.subheader("Add Expense")
col1, col2 = st.columns(2)
with col1:
    merchant = st.text_input("Merchant")
with col2:
    amount = st.number_input("Amount (RM)", min_value=0.0)

if st.button("Save"):
    st.success(f"Added: {merchant} - RM{amount}")