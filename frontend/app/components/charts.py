import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict

def create_spending_timeline(transactions_df: pd.DataFrame):
    """Create an interactive spending timeline"""
    if transactions_df.empty:
        st.info("No transactions to display")
        return
    
    fig = px.line(
        transactions_df,
        x='date',
        y='amount',
        title='Daily Spending Trend',
        labels={'amount': 'Amount (RM)', 'date': 'Date'},
        markers=True
    )
    
    # Add rolling average
    rolling_avg = transactions_df['amount'].rolling(window=7).mean()
    fig.add_trace(go.Scatter(
        x=transactions_df['date'],
        y=rolling_avg,
        name='7-Day Average',
        line=dict(dash='dash', color='orange')
    ))
    
    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

def create_category_pie(category_data: List[Dict]):
    """Create a pie chart for category breakdown"""
    if not category_data:
        st.info("No category data available")
        return
    
    df = pd.DataFrame(category_data)
    
    fig = px.pie(
        df,
        values='total',
        names='category',
        title='Spending by Category',
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

def create_merchant_bar(merchants: List[Dict]):
    """Create a bar chart for top merchants"""
    if not merchants:
        st.info("No merchant data available")
        return
    
    df = pd.DataFrame(merchants[:10])  # Top 10
    
    fig = px.bar(
        df,
        x='merchant',
        y='total_spent',
        title='Top Merchants by Spending',
        labels={'total_spent': 'Total Spent (RM)', 'merchant': 'Merchant'},
        color='total_spent',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def create_budget_gauge(current: float, budget: float):
    """Create a gauge chart for budget progress"""
    percentage = (current / budget * 100) if budget > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current,
        title={'text': f"Budget Progress (RM)"},
        delta={'reference': budget, 'valueformat': '.0f'},
        gauge={
            'axis': {'range': [None, budget], 'tickformat': '.0f'},
            'bar': {'color': "darkgreen" if percentage < 80 else "orange" if percentage < 100 else "red"},
            'steps': [
                {'range': [0, budget * 0.8], 'color': "lightgreen"},
                {'range': [budget * 0.8, budget], 'color': "orange"},
                {'range': [budget, budget * 1.2], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': budget
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def create_heatmap(transactions_df: pd.DataFrame):
    """Create a spending heatmap by day of week and hour (if time data available)"""
    if transactions_df.empty:
        return
    
    # Add day of week
    transactions_df['day_of_week'] = pd.to_datetime(transactions_df['date']).dt.day_name()
    
    # Aggregate by day
    day_spending = transactions_df.groupby('day_of_week')['amount'].sum().reset_index()
    
    # Order days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_spending['day_of_week'] = pd.Categorical(day_spending['day_of_week'], categories=day_order, ordered=True)
    day_spending = day_spending.sort_values('day_of_week')
    
    fig = px.bar(
        day_spending,
        x='day_of_week',
        y='amount',
        title='Spending by Day of Week',
        labels={'amount': 'Total Spent (RM)', 'day_of_week': ''},
        color='amount',
        color_continuous_scale='Blues'
    )
    
    st.plotly_chart(fig, use_container_width=True)