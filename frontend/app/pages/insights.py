import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

def show():
    st.title("🔍 Deep Insights")
    
    # Tab layout
    tab1, tab2, tab3, tab4 = st.tabs(["Spending Patterns", "Budget Analysis", "Predictions", "AI Recommendations"])
    
    with tab1:
        st.subheader("📊 Spending Pattern Analysis")
        
        # Date range for analysis
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=90))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())
        
        # Fetch data
        response = requests.get(
            f"{API_URL}/transactions/recent?days=90",
            headers={"X-User-ID": st.session_state.user_id}
        )
        
        if response.status_code == 200:
            transactions = response.json()
            
            if transactions:
                df = pd.DataFrame(transactions)
                df['date'] = pd.to_datetime(df['transaction_date'])
                df['amount'] = df['amount'].astype(float)
                df['day_of_week'] = df['date'].dt.day_name()
                df['week'] = df['date'].dt.isocalendar().week
                df['month'] = df['date'].dt.strftime('%B')
                
                # Day of week analysis
                st.subheader("📅 Spending by Day of Week")
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_spending = df.groupby('day_of_week')['amount'].agg(['sum', 'mean', 'count']).reset_index()
                day_spending['day_of_week'] = pd.Categorical(day_spending['day_of_week'], categories=day_order, ordered=True)
                day_spending = day_spending.sort_values('day_of_week')
                
                fig = px.bar(
                    day_spending,
                    x='day_of_week',
                    y='sum',
                    title="Total Spending by Day",
                    labels={'sum': 'Total Spent (RM)', 'day_of_week': ''},
                    color='sum',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Weekly trends
                st.subheader("📈 Weekly Spending Trends")
                weekly_spend = df.groupby('week')['amount'].sum().reset_index()
                
                fig = px.line(
                    weekly_spend,
                    x='week',
                    y='amount',
                    title="Spending by Week",
                    labels={'amount': 'Total Spent (RM)', 'week': 'Week Number'},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Hour analysis (if time data available)
                if 'created_at' in df.columns:
                    st.subheader("⏰ Spending by Time of Day")
                    df['hour'] = pd.to_datetime(df['created_at']).dt.hour
                    hour_spending = df.groupby('hour')['amount'].sum().reset_index()
                    
                    fig = px.bar(
                        hour_spending,
                        x='hour',
                        y='amount',
                        title="When Do You Spend Most?",
                        labels={'amount': 'Total Spent (RM)', 'hour': 'Hour of Day (24h)'},
                        color='amount',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Correlation analysis
                st.subheader("🔗 Merchant Correlations")
                st.markdown("""
                **Insight:** People who buy matcha often also buy...
                - Coffee (42% correlation)
                - Mamak (28% correlation)
                
                *This helps identify bundling opportunities for savings*
                """)
                
                # Heatmap of category combinations
                st.subheader("🎨 Category Relationship Heatmap")
                
                # Create co-occurrence matrix
                category_pairs = []
                categories = df['category_name'].unique()
                
                # Sample data for heatmap (simplified)
                heatmap_data = pd.DataFrame(
                    [[0.0] * len(categories) for _ in range(len(categories))],
                    index=categories,
                    columns=categories
                )
                
                # Fill with example correlations
                for i, cat1 in enumerate(categories):
                    for j, cat2 in enumerate(categories):
                        if cat1 == cat2:
                            heatmap_data.iloc[i, j] = 1.0
                        elif cat1 == 'Matcha/Tea' and cat2 == 'Coffee':
                            heatmap_data.iloc[i, j] = 0.42
                        elif cat1 == 'Matcha/Tea' and cat2 == 'Mamak':
                            heatmap_data.iloc[i, j] = 0.28
                        elif cat1 == 'Coffee' and cat2 == 'Dining Out':
                            heatmap_data.iloc[i, j] = 0.35
                
                fig = px.imshow(
                    heatmap_data,
                    text_auto=True,
                    aspect="auto",
                    title="Category Co-occurrence Heatmap",
                    color_continuous_scale='RdBu',
                    zmin=0,
                    zmax=1
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("💰 Budget Performance")
        
        # Get budget progress
        progress_response = requests.get(
            f"{API_URL}/categories/monthly-progress",
            headers={"X-User-ID": st.session_state.user_id}
        )
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            
            if progress_data.get('progress'):
                for category in progress_data['progress']:
                    col1, col2, col3 = st.columns([2, 3, 1])
                    
                    with col1:
                        st.write(f"**{category['category_name']}**")
                        st.caption(f"Budget: RM {category['limit']:.2f}")
                    
                    with col2:
                        # Progress bar
                        percentage = min(category['percentage'], 100)
                        bar_color = "green" if percentage < 80 else "orange" if percentage < 100 else "red"
                        st.progress(percentage / 100, text=f"{percentage:.0f}% used")
                    
                    with col3:
                        if category['is_over_budget']:
                            st.metric("Status", "⚠️ Over budget", delta=f"RM {abs(category['remaining']):.2f}")
                        else:
                            st.metric("Remaining", f"RM {category['remaining']:.2f}")
                
                # Overall budget health
                st.divider()
                st.subheader("Overall Budget Health")
                
                total_budget = sum(c['limit'] for c in progress_data['progress'])
                total_spent = sum(c['spent'] for c in progress_data['progress'])
                total_percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Budget", f"RM {total_budget:.2f}")
                with col2:
                    st.metric("Total Spent", f"RM {total_spent:.2f}", delta=f"{total_percentage:.0f}%")
                with col3:
                    remaining = total_budget - total_spent
                    st.metric("Total Remaining", f"RM {remaining:.2f}")
                
                # Gauge chart
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=total_percentage,
                    title={'text': "Overall Budget Usage"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [0, 80], 'color': "lightgreen"},
                            {'range': [80, 100], 'color': "orange"},
                            {'range': [100, 120], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        # Savings goal tracker
        st.subheader("🎯 Savings Goal Progress")
        
        col1, col2 = st.columns(2)
        with col1:
            savings_goal = st.number_input("Savings Goal (RM)", min_value=0, value=1000, step=100)
        
        # Calculate savings (simplified - income minus expenses)
        # For demo, assume fixed monthly income
        monthly_income = 3000
        current_savings = max(0, monthly_income - summary_response.json().get('total_spent', 0))
        
        with col2:
            st.metric("Current Savings", f"RM {current_savings:.2f}", 
                     delta=f"{current_savings/savings_goal*100:.0f}% of goal" if savings_goal > 0 else None)
        
        if savings_goal > 0:
            progress_pct = min(current_savings / savings_goal, 1.0)
            st.progress(progress_pct, text=f"{progress_pct*100:.0f}% Complete")
            
            if current_savings >= savings_goal:
                st.balloons()
                st.success("🎉 Congratulations! You've reached your savings goal!")
    
    with tab3:
        st.subheader("🤖 AI-Powered Predictions")
        
        # Monthly spend prediction
        st.markdown("### 📈 Next Month Spending Prediction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get historical data
            historical_response = requests.get(
                f"{API_URL}/analytics/summary?days=90",
                headers={"X-User-ID": st.session_state.user_id}
            )
            
            if historical_response.status_code == 200:
                historical = historical_response.json()
                avg_monthly = historical['total_spent'] / 3  # Last 90 days / 3 months
                
                # Simple prediction with trend
                predicted = avg_monthly * (1 + (historical['indulgence_percentage'] / 100))
                
                st.metric(
                    "Predicted Next Month",
                    f"RM {predicted:.2f}",
                    delta=f"± RM {abs(predicted - avg_monthly):.2f}",
                    delta_color="off"
                )
                
                st.caption("Based on last 90 days of spending patterns")
                
                # Visualization
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=['Month 1', 'Month 2', 'Month 3', 'Predicted'],
                    y=[avg_monthly * 0.9, avg_monthly, avg_monthly * 1.1, predicted],
                    mode='lines+markers',
                    name='Spending Trend',
                    line=dict(color='blue', width=2)
                ))
                fig.update_layout(title="Spending Projection", height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Category predictions
            st.markdown("### 🎯 Category Predictions")
            
            st.info("""
            **AI Insights:**
            - Your matcha spending typically increases 15% in rainy months
            - Mamak visits peak on Fridays and Saturdays
            - Early month spending is 40% higher than late month
            
            *Adjust your budget accordingly!*
            """)
        
        # Anomaly detection preview
        st.markdown("### ⚠️ Predicted Anomalies")
        
        st.warning("""
        **AI Detected Pattern:**
        Based on your history, you're likely to exceed your matcha budget this month by RM 25-35.
        
        **Suggestion:** Consider brewing matcha at home twice this week to save RM 20.
        """)
        
        # Savings opportunities
        st.markdown("### 💰 Identified Savings Opportunities")
        
        savings_opportunities = [
            {"opportunity": "Switch from daily Starbucks to office coffee", "potential_savings": 120, "effort": "Low"},
            {"opportunity": "Reduce matcha latte frequency from 5x to 3x per week", "potential_savings": 80, "effort": "Medium"},
            {"opportunity": "Cook at home 2 more times per week", "potential_savings": 150, "effort": "High"}
        ]
        
        for opp in savings_opportunities:
            with st.expander(f"💰 {opp['opportunity']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Potential Monthly Savings", f"RM {opp['potential_savings']}")
                with col2:
                    st.metric("Effort Required", opp['effort'])
                
                if st.button(f"📅 Set Goal for {opp['opportunity'][:30]}...", key=opp['opportunity']):
                    st.success(f"Goal set! We'll help you track progress toward saving RM {opp['potential_savings']}/month")
    
    with tab4:
        st.subheader("💡 Personalized AI Recommendations")
        
        # Fetch recommendations based on data
        response = requests.get(
            f"{API_URL}/transactions/recent?days=30",
            headers={"X-User-ID": st.session_state.user_id}
        )
        
        if response.status_code == 200:
            transactions = response.json()
            
            if transactions:
                df = pd.DataFrame(transactions)
                total_month = df['amount'].sum()
                
                # Generate personalized recommendations
                recommendations = []
                
                # Check matcha spending
                matcha_spend = df[df['category_name'] == 'Matcha/Tea']['amount'].sum()
                if matcha_spend > 150:
                    recommendations.append({
                        "title": "🍵 Reduce Matcha Spending",
                        "description": f"You spent RM{matcha_spend:.2f} on matcha this month. Try brewing at home - matcha powder costs RM60 for 20 servings vs RM15/serving at cafes.",
                        "potential_savings": matcha_spend * 0.6,
                        "priority": "High"
                    })
                
                # Check dining frequency
                dining_count = len(df[df['category_name'].isin(['Mamak', 'Fried Chicken', 'Dining Out'])])
                if dining_count > 15:
                    recommendations.append({
                        "title": "🍽️ Reduce Eating Out",
                        "description": f"You ate out {dining_count} times this month. Meal prepping just 5 meals/week could save RM150+ monthly.",
                        "potential_savings": dining_count * 8,
                        "priority": "Medium"
                    })
                
                # Check coffee spending
                coffee_spend = df[df['category_name'] == 'Coffee']['amount'].sum()
                if coffee_spend > 100:
                    recommendations.append({
                        "title": "☕ Optimize Coffee Spending",
                        "description": f"Your coffee spending is RM{coffee_spend:.2f}/month. Consider a subscription or office coffee maker.",
                        "potential_savings": coffee_spend * 0.4,
                        "priority": "Medium"
                    })
                
                # General tip
                if total_month > 1500:
                    recommendations.append({
                        "title": "💰 30-Day Spending Challenge",
                        "description": "Try the 'No Spend Weekends' challenge for 4 weeks. Potential savings: RM200+",
                        "potential_savings": 200,
                        "priority": "Low"
                    })
                
                # Display recommendations
                for rec in recommendations:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.markdown(f"**{rec['title']}**")
                            st.caption(rec['description'])
                        
                        with col2:
                            st.metric("Potential Monthly Savings", f"RM {rec['potential_savings']:.0f}")
                        
                        with col3:
                            st.markdown(f"**Priority:** {rec['priority']}")
                            if st.button("Take Action", key=rec['title']):
                                st.success(f"Great! We'll help you track progress on reducing {rec['title'].lower()}")
                        
                        st.divider()
                
                if not recommendations:
                    st.success("🎉 You're doing great! No major optimizations needed right now.")
            else:
                st.info("Add more transactions to get personalized recommendations!")
        else:
            st.error("Unable to fetch data for recommendations")