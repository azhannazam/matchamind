import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date

API_URL = "http://localhost:8000"

def show():
    st.title("📊 Dashboard")
    
    # Date range selector
    col1, col2 = st.columns([2, 1])
    with col1:
        date_range = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "This Month", "Last Month", "All Time"],
            index=1
        )
    
    # Map selection to days
    days_map = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "This Month": 30,  # Approximate
        "Last Month": 30,
        "All Time": 365
    }
    days = days_map.get(date_range, 30)
    
    with col2:
        st.metric("Today", datetime.now().strftime("%B %d, %Y"))
    
    # Fetch summary data
    summary_response = requests.get(
        f"{API_URL}/analytics/summary?days={days}",
        headers={"X-User-ID": st.session_state.user_id}
    )
    
    if summary_response.status_code == 200:
        summary = summary_response.json()
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Spent",
                f"RM {summary['total_spent']:,.2f}",
                delta=f"{summary['total_transactions']} transactions"
            )
        
        with col2:
            st.metric(
                "Daily Average",
                f"RM {summary['daily_avg']:.2f}",
                delta="per day"
            )
        
        with col3:
            st.metric(
                "Indulgences",
                f"RM {summary['indulgence_spent']:,.2f}",
                delta=f"{summary['indulgence_percentage']:.0f}% of total"
            )
        
        with col4:
            st.metric(
                "Top Category",
                summary['top_category'] or "N/A",
                delta=summary['top_merchant'][:20] if summary['top_merchant'] else None
            )
        
        st.divider()
        
        # Fetch transaction data for charts
        transactions_response = requests.get(
            f"{API_URL}/transactions/recent?days={days}&limit=500",
            headers={"X-User-ID": st.session_state.user_id}
        )
        
        if transactions_response.status_code == 200:
            transactions = transactions_response.json()
            
            if transactions:
                df = pd.DataFrame(transactions)
                df['date'] = pd.to_datetime(df['transaction_date'])
                df['amount'] = df['amount'].astype(float)
                
                # Create two columns for charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Spending trend line chart
                    st.subheader("📈 Spending Trend")
                    daily_spend = df.groupby('date')['amount'].sum().reset_index()
                    
                    fig = px.line(
                        daily_spend,
                        x='date',
                        y='amount',
                        title="Daily Spending",
                        labels={'amount': 'Amount (RM)', 'date': 'Date'},
                        markers=True
                    )
                    
                    # Add rolling average
                    if len(daily_spend) >= 7:
                        rolling_avg = daily_spend['amount'].rolling(window=7).mean()
                        fig.add_trace(go.Scatter(
                            x=daily_spend['date'],
                            y=rolling_avg,
                            name='7-Day Average',
                            line=dict(dash='dash', color='orange')
                        ))
                    
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Category breakdown pie chart
                    st.subheader("🎯 Spending by Category")
                    category_spend = df.groupby('category_name')['amount'].sum().reset_index()
                    
                    fig = px.pie(
                        category_spend,
                        values='amount',
                        names='category_name',
                        title="",
                        hole=0.3,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Second row of charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Top merchants bar chart
                    st.subheader("🏪 Top Merchants")
                    merchant_spend = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(10).reset_index()
                    
                    fig = px.bar(
                        merchant_spend,
                        x='merchant',
                        y='amount',
                        title="Top 10 Merchants by Spending",
                        labels={'amount': 'Total Spent (RM)', 'merchant': ''},
                        color='amount',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(xaxis_tickangle=-45, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Indulgence vs essential
                    st.subheader("💰 Spending Breakdown")
                    indulgence_data = pd.DataFrame([
                        {"Type": "Indulgences", "Amount": summary['indulgence_spent']},
                        {"Type": "Essentials", "Amount": summary['essential_spent']}
                    ])
                    
                    fig = px.bar(
                        indulgence_data,
                        x='Type',
                        y='Amount',
                        title="Indulgence vs Essentials",
                        labels={'Amount': 'Amount (RM)'},
                        color='Type',
                        color_discrete_sequence=['#FF6B6B', '#4ECDC4']
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Recent transactions table
                st.subheader("🕒 Recent Transactions")
                
                # Prepare display dataframe
                display_df = df.head(10)[['date', 'merchant', 'category_name', 'amount']].copy()
                display_df.columns = ['Date', 'Merchant', 'Category', 'Amount (RM)']
                display_df['Amount (RM)'] = display_df['Amount (RM)'].apply(lambda x: f"RM {x:.2f}")
                display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
                
                st.dataframe(display_df, use_container_width=True)
                
                # Quick insight
                st.divider()
                st.subheader("💡 Quick Insight")
                
                # Find highest spending day
                highest_day = daily_spend.loc[daily_spend['amount'].idxmax()]
                st.info(f"📊 Your highest spending day was {highest_day['date'].strftime('%B %d, %Y')} with RM {highest_day['amount']:.2f}")
                
                # Compare to previous period
                if days >= 30:
                    comp_response = requests.get(
                        f"{API_URL}/analytics/comparison",
                        headers={"X-User-ID": st.session_state.user_id}
                    )
                    if comp_response.status_code == 200:
                        comp = comp_response.json()
                        trend_icon = "📈" if comp['trend'] == 'up' else "📉"
                        st.info(f"{trend_icon} Spending is {abs(comp['change_percentage']):.1f}% {comp['trend']} compared to previous period")
            
            else:
                st.info("No transactions yet. Go to 'Add Expense' to start tracking! 🚀")
                st.image("https://via.placeholder.com/800x300?text=Start+Adding+Expenses", use_container_width=True)
    
    else:
        st.error("Failed to load dashboard data")