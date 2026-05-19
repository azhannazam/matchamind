import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd

API_URL = "http://localhost:8000"

def show():
    st.title("🔔 AI Coach Alerts")
    
    # Fetch alerts
    response = requests.get(
        f"{API_URL}/alerts",
        headers={"X-User-ID": st.session_state.user_id}
    )
    
    if response.status_code == 200:
        alerts = response.json()
        
        # Alert filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.selectbox(
                "Filter by type",
                ["All", "spike", "budget_warning", "achievement", "info"]
            )
        with col2:
            filter_severity = st.selectbox(
                "Filter by severity",
                ["All", "success", "info", "warning", "critical"]
            )
        with col3:
            show_read = st.checkbox("Show read alerts", value=False)
        
        # Apply filters
        filtered_alerts = alerts
        if filter_type != "All":
            filtered_alerts = [a for a in filtered_alerts if a['type'] == filter_type]
        if filter_severity != "All":
            filtered_alerts = [a for a in filtered_alerts if a['severity'] == filter_severity]
        if not show_read:
            filtered_alerts = [a for a in filtered_alerts if not a['is_read']]
        
        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Alerts", len(alerts))
        with col2:
            unread = len([a for a in alerts if not a['is_read']])
            st.metric("Unread", unread, delta="⚠️" if unread > 0 else "✅")
        with col3:
            critical = len([a for a in alerts if a['severity'] == 'critical'])
            st.metric("Critical", critical, delta="🔴" if critical > 0 else "🟢")
        
        st.divider()
        
        # Display alerts
        if not filtered_alerts:
            st.info("No alerts match your filters 🎉")
        else:
            for alert in filtered_alerts:
                # Choose icon based on severity
                if alert['severity'] == 'success':
                    icon = "🎉"
                elif alert['severity'] == 'warning':
                    icon = "⚠️"
                elif alert['severity'] == 'critical':
                    icon = "🚨"
                else:
                    icon = "ℹ️"
                
                # Create expandable alert card
                with st.expander(f"{icon} {alert['message'][:100]}..." if len(alert['message']) > 100 else f"{icon} {alert['message']}", expanded=not alert['is_read']):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.caption(f"Type: {alert['type'].replace('_', ' ').title()} | Severity: {alert['severity'].title()}")
                        st.caption(f"Received: {datetime.fromisoformat(alert['created_at']).strftime('%B %d, %Y at %I:%M %p')}")
                    
                    with col2:
                        if not alert['is_read']:
                            if st.button("Mark as read", key=f"read_{alert['id']}"):
                                patch_response = requests.patch(
                                    f"{API_URL}/alerts/{alert['id']}/read",
                                    headers={"X-User-ID": st.session_state.user_id}
                                )
                                if patch_response.status_code == 200:
                                    st.success("Marked as read!")
                                    st.rerun()
                    
                    with col3:
                        if st.button("Delete", key=f"delete_{alert['id']}"):
                            delete_response = requests.delete(
                                f"{API_URL}/alerts/{alert['id']}",
                                headers={"X-User-ID": st.session_state.user_id}
                            )
                            if delete_response.status_code == 200:
                                st.success("Alert deleted!")
                                st.rerun()
                    
                    # Show metadata if available
                    if alert.get('metadata'):
                        with st.expander("View details"):
                            st.json(alert['metadata'])
        
        # Bulk actions
        if filtered_alerts:
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📖 Mark All as Read", use_container_width=True):
                    for alert in filtered_alerts:
                        if not alert['is_read']:
                            requests.patch(
                                f"{API_URL}/alerts/{alert['id']}/read",
                                headers={"X-User-ID": st.session_state.user_id}
                            )
                    st.success("All alerts marked as read!")
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear All Alerts", use_container_width=True, type="secondary"):
                    for alert in filtered_alerts:
                        requests.delete(
                            f"{API_URL}/alerts/{alert['id']}",
                            headers={"X-User-ID": st.session_state.user_id}
                        )
                    st.success("All alerts cleared!")
                    st.rerun()
    
    else:
        st.error("Failed to load alerts")
    
    # Quick actions
    st.divider()
    st.subheader("⚡ Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Run Alert Check Now", use_container_width=True):
            with st.spinner("AI is analyzing your spending patterns..."):
                response = requests.post(
                    f"{API_URL}/alerts/check-now",
                    headers={"X-User-ID": st.session_state.user_id}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Check complete! Found {data['anomalies_found']} anomalies, created {data['alerts_created']} new alerts.")
                    st.rerun()
                else:
                    st.error("Failed to run alert check")
    
    with col2:
        if st.button("📧 Send Weekly Report", use_container_width=True):
            st.info("Weekly report feature coming soon! (Would email you a summary of your spending)")