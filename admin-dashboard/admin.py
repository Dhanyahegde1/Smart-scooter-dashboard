import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Smart Scooter Admin Dashboard",
    page_icon="🏍️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4fc3f7;
        text-align: center;
        margin-bottom: 2rem;
    }
    .state-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 10px;
        background: rgba(79, 195, 247, 0.1);
        border: 1px solid rgba(79, 195, 247, 0.3);
    }
    .health-score-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
        text-align: center;
    }
    .attack-timeline {
        background: rgba(255, 65, 108, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff416c;
    }
    .ml-decision {
        background: rgba(0, 176, 155, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00b09b;
    }
    .transaction-log {
        background: rgba(30, 30, 46, 0.8);
        padding: 0.5rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0e1117;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .attack-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
        margin-bottom: 0.3rem;
    }
    .ml-process-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: bold;
        text-align: center;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Backend URL
BACKEND_URL = "https://your-backend-name.onrender.com"

# Initialize session state for transaction log and historical data
if 'transaction_log' not in st.session_state:
    st.session_state.transaction_log = []

if 'historical_health_scores' not in st.session_state:
    st.session_state.historical_health_scores = []

if 'historical_anomaly_scores' not in st.session_state:
    st.session_state.historical_anomaly_scores = []

if 'historical_reconstruction_errors' not in st.session_state:
    st.session_state.historical_reconstruction_errors = []

def log_transaction(action, details, status="info"):
    """Log a transaction/security event"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Status colors
    status_colors = {
        "info": "#4fc3f7",
        "success": "#00b09b",
        "warning": "#ffb347",
        "error": "#ff416c",
        "attack": "#ff416c"
    }
    
    log_entry = {
        "timestamp": timestamp,
        "action": action,
        "details": details,
        "status": status,
        "color": status_colors.get(status, "#4fc3f7")
    }
    
    st.session_state.transaction_log.insert(0, log_entry)
    
    # Keep only last 100 entries
    if len(st.session_state.transaction_log) > 100:
        st.session_state.transaction_log.pop()

def update_historical_data(data):
    """Update historical data for graphs"""
    if not data:
        return
    
    timestamp = datetime.now()
    
    # Calculate health score
    health_score = calculate_health_score(data)
    
    # Add to historical data
    health_entry = {
        "timestamp": timestamp,
        "health_score": health_score,
        "system_state": data.get('system_state', 'UNKNOWN')
    }
    st.session_state.historical_health_scores.append(health_entry)
    
    anomaly_entry = {
        "timestamp": timestamp,
        "anomaly_score": data.get('anomaly_score', 0),
        "threshold": data.get('threshold', 0.7)
    }
    st.session_state.historical_anomaly_scores.append(anomaly_entry)
    
    error_entry = {
        "timestamp": timestamp,
        "reconstruction_error": data.get('reconstruction_error', 0)
    }
    st.session_state.historical_reconstruction_errors.append(error_entry)
    
    # Keep only last 1000 entries
    for history in [st.session_state.historical_health_scores, 
                    st.session_state.historical_anomaly_scores, 
                    st.session_state.historical_reconstruction_errors]:
        if len(history) > 1000:
            history.pop(0)

def get_system_state():
    """Fetch current system state from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/system-state")
        if response.status_code == 200:
            data = response.json()
            log_transaction("System State Fetch", f"Successfully fetched system state: {data.get('system_state', 'UNKNOWN')}", "success")
            update_historical_data(data)
            return data
        else:
            log_transaction("System State Fetch", f"Failed with status code: {response.status_code}", "error")
    except Exception as e:
        log_transaction("System State Fetch", f"Connection error: {str(e)}", "error")
    return None

def simulate_attack(attack_type="GPS Spoofing"):
    """Trigger attack simulation"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/simulate-attack", json={"attack_type": attack_type})
        if response.status_code == 200:
            data = response.json()
            log_transaction("Attack Simulation", f"Triggered {attack_type} attack", "attack")
            return data
        else:
            log_transaction("Attack Simulation", f"Failed with status code: {response.status_code}", "error")
    except Exception as e:
        log_transaction("Attack Simulation", f"Connection error: {str(e)}", "error")
    return None

def reset_system():
    """Reset system to normal"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/reset-system")
        if response.status_code == 200:
            data = response.json()
            log_transaction("System Reset", "System reset to NORMAL state", "success")
            return data
        else:
            log_transaction("System Reset", f"Failed with status code: {response.status_code}", "error")
    except Exception as e:
        log_transaction("System Reset", f"Connection error: {str(e)}", "error")
    return None

def get_attack_history():
    """Get attack history from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/attack-history")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"attacks": []}

def calculate_health_score(data):
    """Calculate system health score based on anomaly score and other metrics"""
    if not data:
        return 0
    
    anomaly_score = data.get('anomaly_score', 0)
    reconstruction_error = data.get('reconstruction_error', 0)
    
    # Health score based on inverse of anomaly (higher anomaly = lower health)
    base_health = max(0, 100 * (1 - anomaly_score))
    
    # Penalty for high reconstruction error
    error_penalty = min(20, reconstruction_error * 1000)
    
    # Adjust based on system state
    state_penalty = 0
    state = data.get('system_state', 'NORMAL')
    if state == 'SAFE_MODE':
        state_penalty = 30
    elif state == 'ATTACK_DETECTED':
        state_penalty = 15
    
    health_score = base_health - error_penalty - state_penalty
    
    return max(0, min(100, health_score))

def create_health_timeline_chart():
    """Create health score timeline chart"""
    if not st.session_state.historical_health_scores or len(st.session_state.historical_health_scores) == 0:
        fig = go.Figure()
        fig.update_layout(
            title="No health score data available",
            height=400,
            template="plotly_dark"
        )
        return fig
    
    df = pd.DataFrame(st.session_state.historical_health_scores)
    # Convert timestamp to string for safer handling
    df['timestamp_str'] = df['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if isinstance(x, datetime) else str(x))
    
    fig = go.Figure()
    
    # Add health score line
    fig.add_trace(go.Scatter(
        x=df['timestamp_str'],
        y=df['health_score'],
        mode='lines+markers',
        name='System Health Score',
        line=dict(color='#00b09b', width=3),
        marker=dict(size=6)
    ))
    
    # Add state change markers as annotations instead of vlines
    state_changes = df[df['system_state'].shift() != df['system_state']]
    if not state_changes.empty:
        for _, row in state_changes.iterrows():
            state = row['system_state']
            color = {
                'NORMAL': '#00b09b',
                'ATTACK_DETECTED': '#ffb347',
                'SAFE_MODE': '#ff416c',
                'UNKNOWN': '#666666'
            }.get(state, '#666666')
            
            # Add annotation for state change
            fig.add_annotation(
                x=row['timestamp_str'],
                y=row['health_score'],
                text=state,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor=color,
                font=dict(color=color, size=10),
                bgcolor="rgba(0,0,0,0.7)",
                bordercolor=color,
                borderwidth=1
            )
    
    # Add health zones
    fig.add_hrect(
        y0=80, y1=100,
        fillcolor="rgba(0, 176, 155, 0.1)",
        line_width=0,
        annotation_text="Healthy (80-100%)",
        annotation_position="top left"
    )
    
    fig.add_hrect(
        y0=50, y1=80,
        fillcolor="rgba(255, 179, 71, 0.1)",
        line_width=0,
        annotation_text="Warning (50-80%)",
        annotation_position="top left"
    )
    
    fig.add_hrect(
        y0=0, y1=50,
        fillcolor="rgba(255, 65, 108, 0.1)",
        line_width=0,
        annotation_text="Critical (0-50%)",
        annotation_position="top left"
    )
    
    fig.update_layout(
        title="🏥 System Health Score Timeline",
        xaxis_title="Time",
        yaxis_title="Health Score (%)",
        height=400,
        template="plotly_dark",
        hovermode="x unified"
    )
    
    return fig

def create_anomaly_timeline_chart():
    """Create anomaly score timeline chart"""
    if not st.session_state.historical_anomaly_scores or len(st.session_state.historical_anomaly_scores) == 0:
        fig = go.Figure()
        fig.update_layout(
            title="No anomaly score data available",
            height=400,
            template="plotly_dark"
        )
        return fig
    
    df = pd.DataFrame(st.session_state.historical_anomaly_scores)
    # Convert timestamp to string for safer handling
    df['timestamp_str'] = df['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if isinstance(x, datetime) else str(x))
    
    fig = go.Figure()
    
    # Add anomaly score line
    fig.add_trace(go.Scatter(
        x=df['timestamp_str'],
        y=df['anomaly_score'],
        mode='lines+markers',
        name='Anomaly Score',
        line=dict(color='#4fc3f7', width=3),
        marker=dict(size=6)
    ))
    
    # Add threshold line
    if not df.empty:
        threshold = df['threshold'].iloc[0]
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="#ff416c",
            annotation_text=f"Threshold: {threshold}",
            annotation_position="bottom right"
        )
    
    # Add zones
    if not df.empty:
        threshold = df['threshold'].iloc[0] if 'threshold' in df.columns else 0.7
        fig.add_hrect(
            y0=0, y1=threshold,
            fillcolor="rgba(0, 176, 155, 0.1)",
            line_width=0,
            annotation_text="Normal Zone",
            annotation_position="top left"
        )
        
        fig.add_hrect(
            y0=threshold, y1=1,
            fillcolor="rgba(255, 65, 108, 0.1)",
            line_width=0,
            annotation_text="Attack Zone",
            annotation_position="top left"
        )
    
    fig.update_layout(
        title="📈 Anomaly Score Timeline",
        xaxis_title="Time",
        yaxis_title="Anomaly Score",
        height=400,
        template="plotly_dark",
        hovermode="x unified"
    )
    
    return fig

def create_reconstruction_error_timeline_chart():
    """Create reconstruction error timeline chart"""
    if not st.session_state.historical_reconstruction_errors or len(st.session_state.historical_reconstruction_errors) == 0:
        fig = go.Figure()
        fig.update_layout(
            title="No reconstruction error data available",
            height=400,
            template="plotly_dark"
        )
        return fig
    
    df = pd.DataFrame(st.session_state.historical_reconstruction_errors)
    # Convert timestamp to string for safer handling
    df['timestamp_str'] = df['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if isinstance(x, datetime) else str(x))
    
    fig = go.Figure()
    
    # Add error line
    fig.add_trace(go.Scatter(
        x=df['timestamp_str'],
        y=df['reconstruction_error'],
        mode='lines',
        name='Reconstruction Error',
        line=dict(color='#36d1dc', width=2),
        fill='tozeroy',
        fillcolor='rgba(54, 209, 220, 0.2)'
    ))
    
    # Calculate moving average
    window_size = min(10, len(df))
    if len(df) > 1:
        df['ma_error'] = df['reconstruction_error'].rolling(window=window_size, min_periods=1).mean()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp_str'],
            y=df['ma_error'],
            mode='lines',
            name=f'{window_size}-point Moving Average',
            line=dict(color='#ffb347', width=2, dash='dash')
        ))
    
    fig.update_layout(
        title="🔍 LSTM Reconstruction Error Timeline",
        xaxis_title="Time",
        yaxis_title="Reconstruction Error",
        height=400,
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def create_combined_metrics_chart():
    """Create combined chart showing all metrics"""
    if not (st.session_state.historical_health_scores and 
            st.session_state.historical_anomaly_scores and 
            st.session_state.historical_reconstruction_errors):
        fig = go.Figure()
        fig.update_layout(
            title="No data available for combined chart",
            height=500,
            template="plotly_dark"
        )
        return fig
    
    # Prepare data - use last 100 points
    health_data = st.session_state.historical_health_scores[-100:] if st.session_state.historical_health_scores else []
    anomaly_data = st.session_state.historical_anomaly_scores[-100:] if st.session_state.historical_anomaly_scores else []
    error_data = st.session_state.historical_reconstruction_errors[-100:] if st.session_state.historical_reconstruction_errors else []
    
    if not (health_data and anomaly_data and error_data):
        fig = go.Figure()
        fig.update_layout(
            title="Insufficient data for combined chart",
            height=500,
            template="plotly_dark"
        )
        return fig
    
    df_health = pd.DataFrame(health_data)
    df_anomaly = pd.DataFrame(anomaly_data)
    df_error = pd.DataFrame(error_data)
    
    # Convert timestamps to strings
    for df in [df_health, df_anomaly, df_error]:
        if not df.empty:
            df['timestamp_str'] = df['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if isinstance(x, datetime) else str(x))
    
    # Create subplot figure
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("🏥 Health Score", "📈 Anomaly Score", "🔍 Reconstruction Error"),
        vertical_spacing=0.1,
        shared_xaxes=True
    )
    
    # Health Score
    if not df_health.empty:
        fig.add_trace(
            go.Scatter(
                x=df_health['timestamp_str'],
                y=df_health['health_score'],
                mode='lines',
                name='Health Score',
                line=dict(color='#00b09b', width=2)
            ),
            row=1, col=1
        )
        # Add health thresholds
        for y, name, color in [(80, 'Healthy', '#00b09b'), (50, 'Warning', '#ffb347')]:
            fig.add_hline(y=y, line_dash="dash", line_color=color, 
                         annotation_text=name, annotation_position="top right",
                         row=1, col=1)
    
    # Anomaly Score
    if not df_anomaly.empty:
        fig.add_trace(
            go.Scatter(
                x=df_anomaly['timestamp_str'],
                y=df_anomaly['anomaly_score'],
                mode='lines',
                name='Anomaly Score',
                line=dict(color='#4fc3f7', width=2),
                fill='tozeroy',
                fillcolor='rgba(79, 195, 247, 0.1)'
            ),
            row=2, col=1
        )
        # Add threshold line
        if 'threshold' in df_anomaly.columns and not df_anomaly.empty:
            threshold = df_anomaly['threshold'].iloc[0]
            fig.add_hline(y=threshold, line_dash="dash", line_color="#ff416c",
                         annotation_text=f"Threshold: {threshold}", 
                         row=2, col=1)
    
    # Reconstruction Error
    if not df_error.empty:
        fig.add_trace(
            go.Scatter(
                x=df_error['timestamp_str'],
                y=df_error['reconstruction_error'],
                mode='lines',
                name='Reconstruction Error',
                line=dict(color='#36d1dc', width=2),
                fill='tozeroy',
                fillcolor='rgba(54, 209, 220, 0.1)'
            ),
            row=3, col=1
        )
    
    fig.update_layout(
        height=600,
        template="plotly_dark",
        showlegend=False,
        hovermode="x unified"
    )
    
    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="Score (%)", row=1, col=1)
    fig.update_yaxes(title_text="Anomaly Score", row=2, col=1)
    fig.update_yaxes(title_text="Error", row=3, col=1)
    
    return fig

def create_ml_process_visualization():
    """Create visualization of the ML process"""
    fig = go.Figure()
    
    # Create nodes for the ML process
    nodes = [
        {"id": 0, "label": "📱 Frontend\nTelemetry", "x": 0, "y": 0, "color": "#4fc3f7"},
        {"id": 1, "label": "📡 Data\nCollection", "x": 2, "y": 0, "color": "#36d1dc"},
        {"id": 2, "label": "🧠 LSTM\nEncoder", "x": 4, "y": 0.5, "color": "#00b09b"},
        {"id": 3, "label": "🔍 Latent\nSpace", "x": 6, "y": 0, "color": "#667eea"},
        {"id": 4, "label": "🔄 LSTM\nDecoder", "x": 8, "y": -0.5, "color": "#00b09b"},
        {"id": 5, "label": "📊 Reconstruction\nError", "x": 10, "y": 0, "color": "#ffb347"},
        {"id": 6, "label": "⚖️ Anomaly\nScore", "x": 12, "y": 0, "color": "#ff416c"},
        {"id": 7, "label": "🎯 ML\nDecision", "x": 14, "y": 0, "color": "#764ba2"},
        {"id": 8, "label": "🚨 Safe Mode\nTrigger", "x": 16, "y": 0, "color": "#ff416c"},
        {"id": 9, "label": "🛡️ Frontend\nLockdown", "x": 18, "y": 0, "color": "#ff416c"},
    ]
    
    # Add nodes
    for node in nodes:
        fig.add_trace(go.Scatter(
            x=[node["x"]],
            y=[node["y"]],
            mode="markers+text",
            text=[node["label"]],
            textposition="top center",
            marker=dict(
                size=100,
                color=node["color"],
                line=dict(width=3, color="white")
            ),
            textfont=dict(size=10, color="white"),
            hoverinfo="text",
            name=node["label"]
        ))
    
    # Add edges (connections)
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5),
        (5, 6), (6, 7), (7, 8), (8, 9),
        (5, 2),  # Feedback loop
    ]
    
    for start, end in edges:
        start_node = nodes[start]
        end_node = nodes[end]
        
        # Add arrow
        fig.add_annotation(
            x=end_node["x"],
            y=end_node["y"],
            ax=start_node["x"],
            ay=start_node["y"],
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#888"
        )
    
    # Add labels for each step
    step_labels = [
        (0, "1. Speed, GPS, Battery\nData from Scooter"),
        (2, "2. Sequence Encoding\n(10 time steps)"),
        (3, "3. Compressed\nRepresentation"),
        (4, "4. Sequence\nReconstruction"),
        (5, "5. Compare Input\nvs Reconstruction"),
        (6, "6. Calculate\nAnomaly Score"),
        (7, "7. Threshold Check:\n>0.7 = Attack"),
        (8, "8. Countdown:\n5s to Safe Mode"),
        (9, "9. Map & Music\nDisabled")
    ]
    
    for node_id, label in step_labels:
        node = nodes[node_id]
        fig.add_annotation(
            x=node["x"],
            y=node["y"] - 0.8,
            text=label,
            showarrow=False,
            font=dict(size=9, color="#ccc"),
            align="center"
        )
    
    fig.update_layout(
        title="🧠 ML Anomaly Detection Process Flow",
        height=600,
        template="plotly_dark",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 19]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2, 2]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_health_gauge(health_score):
    """Create health score gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health_score,
        title={'text': "System Health Score"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#4fc3f7"},
            'steps': [
                {'range': [0, 50], 'color': "#ff416c"},
                {'range': [50, 80], 'color': "#ffb347"},
                {'range': [80, 100], 'color': "#00b09b"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': health_score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        template="plotly_dark"
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🏍️ Smart Scooter Admin Dashboard</h1>', unsafe_allow_html=True)
    
    # Auto-refresh
    auto_refresh = st.checkbox("Auto-refresh every 5 seconds", value=True)
    
    # Get current state
    data = get_system_state()
    
    if data is None:
        st.error("⚠️ Cannot connect to backend. Make sure FastAPI server is running.")
        st.info("Run the backend with: `python backend/main.py`")
        return
    
    # Control buttons and attack type selection
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            log_transaction("Manual Refresh", "Admin manually refreshed dashboard", "info")
            st.rerun()
    
    with col2:
        if st.button("🚨 Simulate Attack", use_container_width=True, type="primary"):
            result = simulate_attack()
            if result:
                attack_type = result.get('attack_type', 'Unknown Attack')
                st.success(f"Attack simulation triggered! Type: {attack_type}")
                log_transaction("Attack Simulation", f"Triggered {attack_type}", "attack")
            else:
                st.error("Failed to trigger attack")
                log_transaction("Attack Simulation", "Failed to trigger attack", "error")
            time.sleep(1)
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset System", use_container_width=True):
            result = reset_system()
            if result:
                st.success("System reset to NORMAL")
                log_transaction("System Reset", "System reset successful", "success")
            else:
                st.error("Failed to reset system")
                log_transaction("System Reset", "System reset failed", "error")
            time.sleep(1)
            st.rerun()
    
    with col4:
        attack_types = ["GPS Spoofing", "Speed Injection", "Battery Drain", "Brake Tampering", "Complete Takeover"]
        selected_attack = st.selectbox("Select Attack Type", attack_types, index=0)
        if st.button("🎯 Test Specific Attack", use_container_width=True):
            result = simulate_attack(selected_attack)
            if result:
                st.success(f"{selected_attack} attack simulated!")
                log_transaction("Specific Attack Test", f"Triggered {selected_attack} attack", "attack")
            else:
                st.error(f"Failed to trigger {selected_attack} attack")
                log_transaction("Specific Attack Test", f"Failed to trigger {selected_attack}", "error")
            time.sleep(1)
            st.rerun()
    
    # System State Overview - Updated with health score and attacks detected
    st.markdown("## 📊 System State Overview")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        state = data.get('system_state', 'UNKNOWN')
        state_color = {
            'NORMAL': '#00b09b',
            'ATTACK_DETECTED': '#ffb347',
            'SAFE_MODE': '#ff416c'
        }.get(state, '#666666')
        
        st.markdown(f"""
        <div class="state-card" style="background: linear-gradient(135deg, {state_color} 0%, {state_color}88 100%);">
            <h3>Current State</h3>
            <h1>{state}</h1>
            <p>{data.get('last_update', 'No data')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        anomaly_score = data.get('anomaly_score', 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>Anomaly Score</h3>
            <h1 style="color: #4fc3f7;">{anomaly_score:.3f}</h1>
            <p>Threshold: {data.get('threshold', 0.7)}</p>
            <div style="background: rgba(255, 255, 255, 0.1); height: 10px; border-radius: 5px; margin-top: 10px;">
                <div style="width: {min(anomaly_score * 100, 100)}%; height: 100%; 
                     background: {'#ff416c' if anomaly_score > 0.7 else '#4fc3f7'}; 
                     border-radius: 5px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        reconstruction_error = data.get('reconstruction_error', 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>Reconstruction Error</h3>
            <h1 style="color: #36d1dc;">{reconstruction_error:.4f}</h1>
            <p>LSTM Autoencoder</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        countdown = data.get('safe_mode_countdown')
        countdown_text = str(countdown) if countdown is not None else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Safe Mode Countdown</h3>
            <h1 style="color: #ffb347;">{countdown_text}</h1>
            <p>{'Active' if countdown is not None else 'Inactive'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Calculate and display health score
        health_score = calculate_health_score(data)
        health_color = "#00b09b" if health_score > 80 else "#ffb347" if health_score > 50 else "#ff416c"
        
        st.markdown(f"""
        <div class="health-score-card" style="background: linear-gradient(135deg, {health_color} 0%, {health_color}88 100%);">
            <h3>System Health</h3>
            <h1>{health_score:.0f}%</h1>
            <p>{'Healthy' if health_score > 80 else 'Warning' if health_score > 50 else 'Critical'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        # Get attack history
        attack_history = get_attack_history()
        attack_count = len(attack_history.get('attacks', []))
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>Attacks Detected</h3>
            <h1 style="color: #ff416c;">{attack_count}</h1>
            <p>Total incidents</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Transaction Log / Security Event Register
    st.markdown("## 📜 Transaction Log & Security Events")
    
    # Filter options for transaction log
    col1, col2 = st.columns(2)
    with col1:
        show_all = st.checkbox("Show All Events", value=True)
    with col2:
        filter_status = st.selectbox("Filter by Status", ["All", "info", "success", "warning", "error", "attack"])
    
    # Display transaction log
    log_container = st.container(height=300)
    with log_container:
        if not st.session_state.transaction_log:
            st.info("No transactions logged yet.")
        else:
            for i, log in enumerate(st.session_state.transaction_log):
                if not show_all and i >= 20:  # Show only last 20 if not showing all
                    break
                
                if filter_status != "All" and log['status'] != filter_status:
                    continue
                
                status_emoji = {
                    "info": "ℹ️",
                    "success": "✅",
                    "warning": "⚠️",
                    "error": "❌",
                    "attack": "🚨"
                }.get(log['status'], "📝")
                
                st.markdown(f"""
                <div class="transaction-log" style="border-left: 3px solid {log['color']};">
                    <span style="color: #888;">[{log['timestamp']}]</span>
                    <span style="color: {log['color']}; font-weight: bold;"> {status_emoji} {log['action']}:</span>
                    <span style="color: #ccc;"> {log['details']}</span>
                </div>
                """, unsafe_allow_html=True)
    
    # Clear log button
    if st.button("🗑️ Clear Transaction Log"):
        st.session_state.transaction_log = []
        log_transaction("Log Cleared", "Transaction log cleared by admin", "info")
        st.rerun()
    
    # Comprehensive Metrics Dashboard
    st.markdown("## 📊 Comprehensive System Metrics")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏥 Health Score", 
        "📈 Anomaly Score", 
        "🔍 Reconstruction Error",
        "📊 All Metrics",
        "🧠 ML Process"
    ])
    
    with tab1:
        # Health Score Section
        col1, col2 = st.columns([1, 2])
        
        with col1:
            health_score = calculate_health_score(data)
            st.plotly_chart(create_health_gauge(health_score), use_container_width=True)
            
            st.markdown(f"""
            <div class="ml-decision">
                <h4>🏥 Health Score Calculation:</h4>
                <ul>
                    <li><strong>Base Health (100% - Anomaly):</strong> {100 * (1 - data.get('anomaly_score', 0)):.1f}%</li>
                    <li><strong>Error Penalty:</strong> -{min(20, data.get('reconstruction_error', 0) * 1000):.1f}%</li>
                    <li><strong>State Penalty:</strong> -{30 if data.get('system_state') == 'SAFE_MODE' else 15 if data.get('system_state') == 'ATTACK_DETECTED' else 0:.1f}%</li>
                    <li><strong>Final Health Score:</strong> {health_score:.1f}%</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.plotly_chart(create_health_timeline_chart(), use_container_width=True)
    
    with tab2:
        # Anomaly Score Section
        st.plotly_chart(create_anomaly_timeline_chart(), use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="ml-decision">
                <h4>📈 Anomaly Score Interpretation:</h4>
                <ul>
                    <li><strong>0.0 - 0.3:</strong> Normal operation</li>
                    <li><strong>0.3 - 0.7:</strong> Suspicious activity</li>
                    <li><strong>0.7 - 0.9:</strong> Attack detected</li>
                    <li><strong>0.9 - 1.0:</strong> Critical attack</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Current anomaly statistics
            if st.session_state.historical_anomaly_scores:
                df_anomaly = pd.DataFrame(st.session_state.historical_anomaly_scores)
                avg_anomaly = df_anomaly['anomaly_score'].mean()
                max_anomaly = df_anomaly['anomaly_score'].max()
                threshold_breaches = len(df_anomaly[df_anomaly['anomaly_score'] > 0.7])
                
                st.metric("Average Anomaly", f"{avg_anomaly:.3f}")
                st.metric("Maximum Anomaly", f"{max_anomaly:.3f}")
                st.metric("Threshold Breaches", threshold_breaches)
    
    with tab3:
        # Reconstruction Error Section
        st.plotly_chart(create_reconstruction_error_timeline_chart(), use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="ml-decision">
                <h4>🔍 Reconstruction Error Analysis:</h4>
                <ul>
                    <li><strong>Low Error:</strong> Pattern matches normal behavior</li>
                    <li><strong>Medium Error:</strong> Minor deviations detected</li>
                    <li><strong>High Error:</strong> Significant pattern mismatch</li>
                    <li><strong>Spike:</strong> Possible attack or sensor failure</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Current error statistics
            if st.session_state.historical_reconstruction_errors:
                df_error = pd.DataFrame(st.session_state.historical_reconstruction_errors)
                avg_error = df_error['reconstruction_error'].mean()
                max_error = df_error['reconstruction_error'].max()
                error_spikes = len(df_error[df_error['reconstruction_error'] > 0.1])
                
                st.metric("Average Error", f"{avg_error:.4f}")
                st.metric("Maximum Error", f"{max_error:.4f}")
                st.metric("Error Spikes", error_spikes)
    
    with tab4:
        # All Metrics Combined
        st.plotly_chart(create_combined_metrics_chart(), use_container_width=True)
        
        # Summary statistics
        st.markdown("### 📋 Metrics Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.session_state.historical_health_scores:
                df_health = pd.DataFrame(st.session_state.historical_health_scores)
                current_trend = "📈 Improving" if len(df_health) > 1 and df_health['health_score'].iloc[-1] > df_health['health_score'].iloc[-2] else "📉 Declining"
                st.metric("Health Trend", current_trend)
        
        with col2:
            if st.session_state.historical_anomaly_scores:
                df_anomaly = pd.DataFrame(st.session_state.historical_anomaly_scores)
                anomaly_trend = "📉 Decreasing" if len(df_anomaly) > 1 and df_anomaly['anomaly_score'].iloc[-1] < df_anomaly['anomaly_score'].iloc[-2] else "📈 Increasing"
                st.metric("Anomaly Trend", anomaly_trend)
        
        with col3:
            if st.session_state.historical_reconstruction_errors:
                df_error = pd.DataFrame(st.session_state.historical_reconstruction_errors)
                error_trend = "📉 Improving" if len(df_error) > 1 and df_error['reconstruction_error'].iloc[-1] < df_error['reconstruction_error'].iloc[-2] else "📈 Worsening"
                st.metric("Error Trend", error_trend)
        
        with col4:
            # System stability
            state_changes = 0
            if st.session_state.historical_health_scores:
                df_health = pd.DataFrame(st.session_state.historical_health_scores)
                state_changes = len(df_health[df_health['system_state'].shift() != df_health['system_state']])
            stability = "🔒 Stable" if state_changes < 3 else "⚠️ Unstable" if state_changes < 10 else "🚨 Volatile"
            st.metric("System Stability", stability)
    
    with tab5:
        # ML Process Visualization
        st.plotly_chart(create_ml_process_visualization(), use_container_width=True)
        
        # Add the text-based ML process explanation
        st.markdown("""
        <div style="background: rgba(79, 195, 247, 0.1); padding: 1.5rem; border-radius: 10px; margin-top: 1rem;">
            <h4>🧠 How ML Triggers Safe Mode:</h4>
            <ol>
                <li><strong>Telemetry Collection:</strong> Frontend sends speed, acceleration, and GPS data</li>
                <li><strong>LSTM Processing:</strong> Model compares current pattern with learned normal behavior</li>
                <li><strong>Anomaly Score:</strong> Calculates deviation score (0-1)</li>
                <li><strong>Decision Threshold:</strong> If score > 0.7 → ATTACK_DETECTED</li>
                <li><strong>Safe Mode Activation:</strong> After countdown or critical score > 0.9 → SAFE_MODE</li>
                <li><strong>Frontend Lockdown:</strong> Map and music disabled until page refresh</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Attacks Detected List
    st.markdown("## 🚨 Attacks Detected")
    
    attack_history = get_attack_history()
    if attack_history.get('attacks'):
        attacks_df = pd.DataFrame(attack_history['attacks'])
        
        # Add color coding for attack types
        attack_colors = {
            "GPS Spoofing": "#ff6b6b",
            "Speed Injection": "#ffa726",
            "Battery Drain": "#42a5f5",
            "Brake Tampering": "#ab47bc",
            "Complete Takeover": "#ef5350"
        }
        
        # Display attacks in a table with badges
        for _, attack in attacks_df.iterrows():
            attack_type = attack.get('type', 'Unknown')
            timestamp = attack.get('timestamp', '')
            anomaly_score = attack.get('anomaly_score', 0)
            
            color = attack_colors.get(attack_type, "#666")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.markdown(f"**{timestamp}**")
            with col2:
                st.markdown(f"""
                <span class="attack-badge" style="background-color: {color}; color: white;">
                    {attack_type}
                </span>
                <strong>Anomaly Score: {anomaly_score:.3f}</strong>
                """, unsafe_allow_html=True)
            with col3:
                if attack.get('mitigated'):
                    st.success("✅ Mitigated")
                else:
                    st.error("⚠️ Active")
            
            st.divider()
    else:
        st.info("No attacks detected yet.")
    
    # Data Consistency Note
    st.markdown("""
    ---
    ### 🔄 Data Consistency Rule
    <div style="background: rgba(0, 176, 155, 0.1); padding: 1rem; border-radius: 10px;">
        <p><strong>Single Source of Truth:</strong> All components (Frontend, Backend, Admin) display the same system state derived from one ML decision point in the FastAPI backend.</p>
        <p><strong>Current Verification:</strong> All dashboards show <strong>{state}</strong> with anomaly score <strong>{score:.3f}</strong></p>
    </div>
    """.format(state=data.get('system_state'), score=data.get('anomaly_score', 0)), unsafe_allow_html=True)
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()