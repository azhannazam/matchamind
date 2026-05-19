import streamlit as st
from datetime import datetime
import requests

API_URL = "http://localhost:8000"

def show():
    st.title("⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["Budget", "Categories", "Profile"])
    
    with tab1:
        st.subheader("💰 Monthly Budget")
        
        # Get current budget
        response = requests.get(f"{API_URL}/users/budget", 
                               headers={"X-User-ID": st.session_state.user_id})
        
        if response.status_code == 200:
            current_budget = response.json().get('monthly_budget', 500)
            new_budget = st.number_input(
                "Set your monthly spending budget (RM)",
                min_value=100.0,
                max_value=10000.0,
                value=float(current_budget),
                step=50.0
            )
            
            if st.button("Update Budget", type="primary"):
                update_response = requests.patch(
                    f"{API_URL}/users/budget",
                    json={"monthly_budget": new_budget},
                    headers={"X-User-ID": st.session_state.user_id}
                )
                
                if update_response.status_code == 200:
                    st.success(f"Budget updated to RM {new_budget:,.2f}!")
                    st.balloons()
                else:
                    st.error("Failed to update budget")
        
        st.subheader("🎯 Savings Goal")
        savings_goal = st.number_input("What's your savings goal? (RM)", min_value=0.0, value=1000.0, step=100.0)
        
        if savings_goal > 0:
            st.info(f"💪 You're working towards saving RM {savings_goal:,.2f}. Every small choice adds up!")
    
    with tab2:
        st.subheader("📂 Manage Categories")
        
        # Fetch categories
        response = requests.get(f"{API_URL}/categories",
                               headers={"X-User-ID": st.session_state.user_id})
        
        if response.status_code == 200:
            categories = response.json()
            
            # Display existing categories
            for cat in categories:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{cat['name']}**")
                with col2:
                    limit = cat.get('monthly_limit')
                    st.write(f"Limit: RM {limit:.2f}" if limit else "No limit")
                with col3:
                    if st.button("Delete", key=f"del_{cat['id']}"):
                        del_response = requests.delete(
                            f"{API_URL}/categories/{cat['id']}",
                            headers={"X-User-ID": st.session_state.user_id}
                        )
                        if del_response.status_code == 200:
                            st.success(f"Deleted {cat['name']}")
                            st.rerun()
            
            # Add new category
            st.divider()
            st.subheader("➕ Add Custom Category")
            
            col1, col2 = st.columns(2)
            with col1:
                new_category = st.text_input("Category Name", placeholder="e.g., Bubble Tea, Gaming, Books")
            with col2:
                monthly_limit = st.number_input("Monthly Limit (RM)", min_value=0.0, value=100.0, step=10.0)
            
            is_indulgence = st.checkbox("Mark as indulgence (discretionary spending)", value=True)
            
            if st.button("Create Category"):
                if new_category:
                    create_response = requests.post(
                        f"{API_URL}/categories",
                        json={
                            "name": new_category,
                            "monthly_limit": monthly_limit if monthly_limit > 0 else None,
                            "is_indulgence": is_indulgence
                        },
                        headers={"X-User-ID": st.session_state.user_id}
                    )
                    
                    if create_response.status_code == 200:
                        st.success(f"Created category: {new_category}")
                        st.rerun()
                    else:
                        st.error("Category might already exist")
    
    with tab3:
        st.subheader("👤 Profile Settings")
        
        # Display user info
        st.write(f"**User ID:** {st.session_state.user_id}")
        st.write(f"**Email:** {st.session_state.get('email', 'demo@matchamind.com')}")
        
        st.divider()
        
        # Export data
        st.subheader("📥 Export Your Data")
        
        if st.button("Export All Transactions (CSV)"):
            response = requests.get(f"{API_URL}/transactions/export",
                                   headers={"X-User-ID": st.session_state.user_id})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('transactions'):
                    import pandas as pd
                    df = pd.DataFrame(data['transactions'])
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"matchamind_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No transactions to export")
            else:
                st.error("Failed to export data")
        
        st.divider()
        
        # Danger zone
        st.subheader("⚠️ Danger Zone")
        
        if st.button("Delete All Data", type="secondary"):
            st.warning("This will delete ALL your transactions. This cannot be undone.")
            confirm = st.text_input("Type 'DELETE' to confirm")
            
            if confirm == "DELETE":
                if st.button("Permanently Delete Everything", type="primary"):
                    delete_response = requests.delete(
                        f"{API_URL}/users/data",
                        headers={"X-User-ID": st.session_state.user_id}
                    )
                    
                    if delete_response.status_code == 200:
                        st.error("All data has been deleted.")
                        st.balloons()
                    else:
                        st.error("Failed to delete data")