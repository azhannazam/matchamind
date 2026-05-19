import streamlit as st
import requests
from datetime import date, datetime
import pandas as pd

API_URL = "http://localhost:8000"

def show():
    st.title("📝 Add New Expense")
    
    # Two input methods
    input_method = st.radio(
        "Choose input method:",
        ["✨ AI Parse from Text", "📝 Manual Entry"],
        horizontal=True
    )
    
    if input_method == "✨ AI Parse from Text":
        st.markdown("""
        ### Paste your receipt/transaction text
        The AI will automatically extract:
        - Amount
        - Merchant name  
        - Category
        - Indulgence status
        
        **Examples:**
        - `RM 45.90 - Tealive Midvalley (Matcha Latte + Boba)`
        - `KFC: RM 32.40 2pc combo meal`
        - `Nasi Kandar Pelita - RM 18.50 (Roti Canai + Teh Tarik)`
        - `Paid RM 129 for Matcha powder from Shopee`
        """)
        
        raw_text = st.text_area(
            "Transaction text:",
            height=100,
            placeholder="Paste your receipt text here..."
        )
        
        transaction_date = st.date_input(
            "Transaction date:",
            value=date.today()
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            parse_button = st.button("🔮 AI Parse & Add", type="primary", use_container_width=True)
        
        if parse_button and raw_text:
            with st.spinner("AI is analyzing your transaction..."):
                try:
                    response = requests.post(
                        f"{API_URL}/transactions/parse-and-add",
                        json={
                            "raw_text": raw_text,
                            "transaction_date": transaction_date.isoformat()
                        },
                        headers={"X-User-ID": st.session_state.user_id}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        parsed = data['parsed_data']
                        
                        # Show parsed results
                        st.success("✅ Transaction added successfully!")
                        
                        st.markdown("---")
                        st.subheader("📊 AI Parsed Results")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Merchant", parsed['merchant'])
                            st.metric("Category", parsed['category'])
                        with col2:
                            st.metric("Amount", f"RM {parsed['amount']:.2f}")
                            st.metric("Confidence", f"{parsed['confidence']*100:.0f}%")
                        
                        if parsed['is_indulgence']:
                            st.info("🍵 This was marked as an indulgence (discretionary spending)")
                        else:
                            st.success("✅ This was marked as an essential expense")
                        
                        st.balloons()
                        
                        # Option to add another
                        if st.button("➕ Add Another Transaction"):
                            st.rerun()
                    
                    elif response.status_code == 422:
                        st.error("Could not parse this transaction. Please check the format or use manual entry.")
                        st.json(response.json())
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    st.error(f"Failed to connect to server: {e}")
                    st.info("Make sure the backend is running on http://localhost:8000")
        
        elif parse_button and not raw_text:
            st.warning("Please enter transaction text first")
    
    else:  # Manual Entry
        st.markdown("### Enter transaction details manually")
        
        with st.form("manual_transaction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                merchant = st.text_input("Merchant name *", placeholder="e.g., Tealive, KFC, Grocery Store")
                amount = st.number_input("Amount (RM) *", min_value=0.01, step=1.0, format="%.2f")
            
            with col2:
                transaction_date = st.date_input("Date", value=date.today())
                
                # Fetch categories
                response = requests.get(
                    f"{API_URL}/categories",
                    headers={"X-User-ID": st.session_state.user_id}
                )
                
                categories = ["Uncategorized"]
                if response.status_code == 200:
                    categories = [cat['name'] for cat in response.json()]
                
                selected_category = st.selectbox("Category", categories)
            
            notes = st.text_area("Notes (optional)", placeholder="Any additional details...")
            
            submitted = st.form_submit_button("💾 Save Transaction", type="primary", use_container_width=True)
            
            if submitted:
                if not merchant or amount <= 0:
                    st.error("Please fill in merchant name and valid amount")
                else:
                    # Find category ID
                    category_id = None
                    if selected_category != "Uncategorized":
                        cat_response = requests.get(
                            f"{API_URL}/categories",
                            headers={"X-User-ID": st.session_state.user_id}
                        )
                        if cat_response.status_code == 200:
                            for cat in cat_response.json():
                                if cat['name'] == selected_category:
                                    category_id = cat['id']
                                    break
                    
                    # Create transaction
                    transaction_data = {
                        "amount": amount,
                        "merchant": merchant,
                        "transaction_date": transaction_date.isoformat(),
                        "notes": notes,
                        "category_id": category_id
                    }
                    
                    response = requests.post(
                        f"{API_URL}/transactions",
                        json=transaction_data,
                        headers={"X-User-ID": st.session_state.user_id}
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Transaction added successfully!")
                        st.balloons()
                        
                        # Clear form by rerunning
                        if st.button("➕ Add Another Transaction"):
                            st.rerun()
                    else:
                        st.error(f"Failed to add transaction: {response.text}")
    
    st.markdown("---")
    
    # Quick add templates
    st.subheader("⚡ Quick Templates")
    st.markdown("Click any template to pre-fill the AI parser:")
    
    col1, col2, col3 = st.columns(3)
    
    templates = [
        ("🍵 Matcha Latte", "RM 25.90 - Tealive (Matcha Latte)"),
        ("🍗 Fried Chicken", "KFC: RM 32.40 2pc combo"),
        ("🍛 Mamak", "Nasi Kandar Pelita - RM 18.50"),
        ("☕ Coffee", "Starbucks - Grande Latte RM18.00"),
        ("🛒 Groceries", "RM 120.50 - AEON Big (groceries)"),
        ("📦 Online", "RM 89.00 - Shopee (electronics)")
    ]
    
    for i, (label, text) in enumerate(templates):
        col = [col1, col2, col3][i % 3]
        if col.button(label, key=f"template_{i}"):
            st.session_state.template_text = text
            st.rerun()
    
    if 'template_text' in st.session_state:
        st.info(f"Template loaded: {st.session_state.template_text}")
        if st.button("Clear template"):
            del st.session_state.template_text
            st.rerun()