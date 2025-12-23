"""
R3ACT Dashboard - Streamlit Application
Resilience, Reaction and Recovery Analysis of Critical Transitions
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.r3act_system import R3ACTSystem
from src.data_loader import SkillCornerDataLoader

# Page configuration
st.set_page_config(
    page_title="R3ACT Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Color palette
COLORS = {
    'background': '#0E1117',
    'primary_text': '#00FF88',
    'secondary_text': '#00D4AA',
    'accent_blue': '#00BFFF',
    'accent_cyan': '#00CED1',
    'success': '#00FF88',
    'warning': '#FFD700',
    'danger': '#FF6B6B',
    'neutral': '#808080',
    'gradient_start': '#00FF88',
    'gradient_mid': '#00BFFF',
    'gradient_end': '#0066CC',
}

# Custom CSS
st.markdown(f"""
<style>
    .main {{
        background-color: {COLORS['background']};
    }}
    .stApp {{
        background-color: {COLORS['background']};
    }}
    h1, h2, h3 {{
        color: {COLORS['primary_text']};
    }}
    .metric-card {{
        background-color: #1E2130;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid {COLORS['primary_text']};
    }}
    .league-avg {{
        color: {COLORS['accent_blue']};
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'league_averages' not in st.session_state:
    st.session_state.league_averages = {}

# Default event weights
DEFAULT_EVENT_WEIGHTS = {
    "possession_loss_defensive_third": 1.0,
    "possession_loss_middle_third": 0.7,
    "possession_loss_attacking_third": 0.5,
    "possession_loss_penalty_area": 1.5,
    "failed_pass_dangerous": 1.2,
    "failed_pass_lead_to_shot": 1.5,
    "failed_pass_offside": 0.8,
    "goal_conceded": 2.0,
    "goal_scored": 2.0,
    "defensive_error_lead_to_shot": 1.3,
    "interception_conceded_dangerous": 0.8,
    "interception_conceded_defensive_third": 1.0,
}

# Event type labels for display
EVENT_LABELS = {
    "possession_loss_defensive_third": "Possession Loss (Defensive Third)",
    "possession_loss_middle_third": "Possession Loss (Middle Third)",
    "possession_loss_attacking_third": "Possession Loss (Attacking Third)",
    "possession_loss_penalty_area": "Possession Loss (Penalty Area)",
    "failed_pass_dangerous": "Failed Pass (Dangerous)",
    "failed_pass_lead_to_shot": "Failed Pass (Led to Shot)",
    "failed_pass_offside": "Failed Pass (Offside)",
    "goal_conceded": "Goal Conceded",
    "goal_scored": "Goal Scored",
    "defensive_error_lead_to_shot": "Defensive Error (Led to Shot)",
    "interception_conceded_dangerous": "Interception Conceded (Dangerous)",
    "interception_conceded_defensive_third": "Interception Conceded (Defensive Third)",
}

def calculate_league_averages(df):
    """Calculate league averages for comparison"""
    if df is None or df.empty:
        return {}
    
    averages = {
        'total_events': len(df),
        'events_per_match': len(df) / df['match_id'].nunique() if df['match_id'].nunique() > 0 else 0,
    }
    
    if 'CRT' in df.columns:
        crt_values = df['CRT'].dropna()
        if len(crt_values) > 0:
            averages['crt_mean'] = crt_values.mean()
            averages['crt_median'] = crt_values.median()
    
    if 'TSI' in df.columns:
        tsi_values = df['TSI'].dropna()
        if len(tsi_values) > 0:
            averages['tsi_mean'] = tsi_values.mean()
            averages['tsi_median'] = tsi_values.median()
    
    if 'GIRI' in df.columns:
        giri_values = df['GIRI'].dropna()
        if len(giri_values) > 0:
            averages['giri_mean'] = giri_values.mean()
            averages['giri_median'] = giri_values.median()
    
    return averages

def load_data():
    """Load R3ACT results"""
    if st.session_state.results_df is None:
        with st.spinner("Loading data and calculating R3ACT metrics (this may take several minutes)..."):
            r3act = R3ACTSystem(time_window='medium')
            results_df = r3act.process_all_matches(load_tracking=True)
            st.session_state.results_df = results_df
            st.session_state.league_averages = calculate_league_averages(results_df)
    return st.session_state.results_df, st.session_state.league_averages

def create_kpi_card(title, value, subtitle="", color=COLORS['primary_text']):
    """Create a KPI card"""
    return f"""
    <div class="metric-card">
        <h3 style="color: {color}; margin: 0; font-size: 14px;">{title}</h3>
        <h1 style="color: {color}; margin: 10px 0; font-size: 32px;">{value}</h1>
        <p style="color: {COLORS['secondary_text']}; margin: 0; font-size: 12px;">{subtitle}</p>
    </div>
    """

def main():
    # Load data
    results_df, league_avg = load_data()
    
    if results_df is None or results_df.empty:
        st.error("No data available. Please run the R3ACT system first.")
        return
    
    # Title and Subtitle
    st.markdown("<h1 style='text-align: center; color: #00FF88;'>R3ACT Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #00D4AA; font-size: 18px; font-weight: normal;'>Resilience, Reaction and Recovery Analysis of Critical Transitions</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("## Filters")
        
        # Match filter
        match_ids = ['All'] + sorted(results_df['match_id'].unique().tolist())
        selected_match = st.selectbox("Match", match_ids)
        
        # Team filter
        if selected_match != 'All':
            match_data = results_df[results_df['match_id'] == selected_match]
            teams = ['All'] + sorted(match_data['team_id'].unique().tolist())
        else:
            teams = ['All'] + sorted(results_df['team_id'].unique().tolist())
        selected_team = st.selectbox("Team", teams)
        
        # Player filter
        if selected_team != 'All':
            if selected_match != 'All':
                player_data = match_data[match_data['team_id'] == selected_team]
            else:
                player_data = results_df[results_df['team_id'] == selected_team]
            players = ['All'] + sorted([p for p in player_data['player_id'].dropna().unique().tolist() if pd.notna(p)])
        else:
            players = ['All'] + sorted([p for p in results_df['player_id'].dropna().unique().tolist() if pd.notna(p)])
        selected_player = st.selectbox("Player", players)
        
        # Period filter
        periods = ['All', 'First Half', 'Second Half']
        selected_period = st.selectbox("Period", periods)
        
        # Position filter (if available)
        st.markdown("---")
        st.markdown("### Additional Filters")
        show_crt = st.checkbox("Show CRT", value=True)
        show_tsi = st.checkbox("Show TSI", value=True)
        show_giri = st.checkbox("Show GIRI", value=True)
    
    # Apply filters
    filtered_df = results_df.copy()
    if selected_match != 'All':
        filtered_df = filtered_df[filtered_df['match_id'] == selected_match]
    if selected_team != 'All':
        filtered_df = filtered_df[filtered_df['team_id'] == selected_team]
    if selected_player != 'All':
        filtered_df = filtered_df[filtered_df['player_id'] == selected_player]
    if selected_period == 'First Half':
        filtered_df = filtered_df[filtered_df['period'] == 1]
    elif selected_period == 'Second Half':
        filtered_df = filtered_df[filtered_df['period'] == 2]
    
    # KPI Cards
    st.markdown("## Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_events = len(filtered_df)
        league_total = league_avg.get('total_events', 0)
        st.markdown(create_kpi_card(
            "Total Critical Events",
            f"{total_events:,}",
            f"League Avg: {league_total:,}" if league_total > 0 else "Total events detected",
            COLORS['primary_text']
        ), unsafe_allow_html=True)
    
    with col2:
        if 'CRT' in filtered_df.columns:
            crt_values = filtered_df['CRT'].dropna()
            if len(crt_values) > 0:
                crt_mean = crt_values.mean()
                league_crt = league_avg.get('crt_mean', 0)
                st.markdown(create_kpi_card(
                    "Cognitive Reset Time",
                    f"{crt_mean:.1f}s",
                    f"League Avg: {league_crt:.1f}s" if league_crt > 0 else "Individual recovery time",
                    COLORS['accent_blue']
                ), unsafe_allow_html=True)
            else:
                st.markdown(create_kpi_card("Cognitive Reset Time", "N/A", "No data available", COLORS['neutral']), unsafe_allow_html=True)
        else:
            st.markdown(create_kpi_card("Cognitive Reset Time", "N/A", "Column not found", COLORS['neutral']), unsafe_allow_html=True)
    
    with col3:
        if 'TSI' in filtered_df.columns:
            tsi_values = filtered_df['TSI'].dropna()
            if len(tsi_values) > 0:
                tsi_mean = tsi_values.mean()
                league_tsi = league_avg.get('tsi_mean', 0)
                st.markdown(create_kpi_card(
                    "Team Support Index",
                    f"{tsi_mean:.3f}",
                    f"League Avg: {league_tsi:.3f}" if league_tsi != 0 else "Collective team response",
                    COLORS['accent_cyan']
                ), unsafe_allow_html=True)
            else:
                st.markdown(create_kpi_card("Team Support Index", "N/A", "No data available", COLORS['neutral']), unsafe_allow_html=True)
        else:
            st.markdown(create_kpi_card("Team Support Index", "N/A", "Column not found", COLORS['neutral']), unsafe_allow_html=True)
    
    with col4:
        if 'GIRI' in filtered_df.columns:
            giri_values = filtered_df['GIRI'].dropna()
            if len(giri_values) > 0:
                giri_mean = giri_values.mean()
                league_giri = league_avg.get('giri_mean', 0)
                st.markdown(create_kpi_card(
                    "Goal Impact Response Index",
                    f"{giri_mean:.3f}",
                    f"League Avg: {league_giri:.3f}" if league_giri != 0 else "Tactical change post-goal",
                    COLORS['accent_blue']
                ), unsafe_allow_html=True)
            else:
                st.markdown(create_kpi_card("Goal Impact Response Index", "N/A", "No goal events", COLORS['neutral']), unsafe_allow_html=True)
        else:
            st.markdown(create_kpi_card("Goal Impact Response Index", "N/A", "Column not found", COLORS['neutral']), unsafe_allow_html=True)
    
    with col5:
        events_per_min = total_events / 90 if total_events > 0 else 0
        league_epm = league_avg.get('events_per_match', 0) / 90 if league_avg.get('events_per_match', 0) > 0 else 0
        st.markdown(create_kpi_card(
            "Events per Minute",
            f"{events_per_min:.2f}",
            f"League Avg: {league_epm:.2f}" if league_epm > 0 else "Critical events frequency",
            COLORS['success']
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Critical Event Metrics Configuration
    st.markdown("## Critical Event Metrics Configuration")
    st.markdown("Adjust the weights for each critical event type. Higher weights indicate more critical events.")
    
    # Create sliders for event weights
    event_weights = {}
    cols = st.columns(3)
    
    for idx, (event_type, default_weight) in enumerate(DEFAULT_EVENT_WEIGHTS.items()):
        col_idx = idx % 3
        with cols[col_idx]:
            label = EVENT_LABELS.get(event_type, event_type.replace('_', ' ').title())
            weight = st.slider(
                label,
                min_value=0.0,
                max_value=3.0,
                value=float(default_weight),
                step=0.1,
                key=f"weight_{event_type}"
            )
            event_weights[event_type] = weight
    
    st.markdown("---")
    
    # Time Window Configuration
    st.markdown("## Time Window Configuration")
    time_window = st.radio(
        "Select temporal window for analysis:",
        ["Short (2 minutes)", "Medium (5 minutes)", "Long (10 minutes)"],
        index=1,
        horizontal=True
    )
    
    window_map = {
        "Short (2 minutes)": "short",
        "Medium (5 minutes)": "medium",
        "Long (10 minutes)": "long"
    }
    selected_window = window_map[time_window]
    
    st.markdown(f"**Selected:** {time_window} - {'Immediate response' if selected_window == 'short' else 'Tactical response' if selected_window == 'medium' else 'Sustained impact'}")
    
    st.markdown("---")
    
    # Visualizations in 2x1 layout
    st.markdown("## Analysis Visualizations")
    
    # Row 1: Event Distribution and Timeline
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Event Distribution by Type")
        if not filtered_df.empty:
            event_counts = filtered_df['event_type'].value_counts()
            fig = go.Figure(data=[
                go.Bar(
                    x=event_counts.values,
                    y=[EVENT_LABELS.get(et, et.replace('_', ' ').title()) for et in event_counts.index],
                    orientation='h',
                    marker=dict(
                        color=COLORS['primary_text'],
                        line=dict(color=COLORS['accent_blue'], width=1)
                    )
                )
            ])
            fig.update_layout(
                plot_bgcolor=COLORS['background'],
                paper_bgcolor=COLORS['background'],
                font=dict(color=COLORS['primary_text']),
                height=400,
                xaxis=dict(title="Number of Events", title_font=dict(color=COLORS['secondary_text'])),
                yaxis=dict(title="", title_font=dict(color=COLORS['secondary_text']))
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Distribution of critical events by type. Higher values indicate more frequent critical situations.")
        else:
            st.info("No data available for selected filters.")
    
    with col2:
        st.markdown("### Events Timeline")
        if not filtered_df.empty and 'timestamp' in filtered_df.columns:
            # Convert timestamp to minutes
            filtered_df_copy = filtered_df.copy()
            filtered_df_copy['minute'] = filtered_df_copy['timestamp'] / 60
            
            fig = go.Figure()
            for event_type in filtered_df_copy['event_type'].unique()[:5]:  # Top 5 event types
                event_data = filtered_df_copy[filtered_df_copy['event_type'] == event_type]
                fig.add_trace(go.Scatter(
                    x=event_data['minute'],
                    y=[event_type] * len(event_data),
                    mode='markers',
                    name=EVENT_LABELS.get(event_type, event_type),
                    marker=dict(size=8, opacity=0.6)
                ))
            
            fig.update_layout(
                plot_bgcolor=COLORS['background'],
                paper_bgcolor=COLORS['background'],
                font=dict(color=COLORS['primary_text']),
                height=400,
                xaxis=dict(title="Match Minute", title_font=dict(color=COLORS['secondary_text'])),
                yaxis=dict(title="Event Type", title_font=dict(color=COLORS['secondary_text']))
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Temporal distribution of critical events throughout the match. Identify critical moments.")
        else:
            st.info("No timeline data available.")
    
    # Row 2: CRT and TSI Analysis
    if show_crt and 'CRT' in filtered_df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Cognitive Reset Time (CRT) Distribution")
            crt_data = filtered_df['CRT'].dropna()
            if len(crt_data) > 0:
                league_crt = league_avg.get('crt_mean', 0)
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=crt_data,
                    nbinsx=30,
                    marker_color=COLORS['primary_text'],
                    opacity=0.7,
                    name='CRT Distribution'
                ))
                
                if league_crt > 0:
                    fig.add_vline(
                        x=league_crt,
                        line_dash="dash",
                        line_color=COLORS['accent_blue'],
                        annotation_text=f"League Avg: {league_crt:.1f}s",
                        annotation_position="top"
                    )
                
                fig.update_layout(
                    plot_bgcolor=COLORS['background'],
                    paper_bgcolor=COLORS['background'],
                    font=dict(color=COLORS['primary_text']),
                    height=400,
                    xaxis=dict(title="CRT (seconds)", title_font=dict(color=COLORS['secondary_text'])),
                    yaxis=dict(title="Frequency", title_font=dict(color=COLORS['secondary_text']))
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"CRT measures individual recovery time. Lower values indicate better resilience. League average: {league_crt:.1f}s" if league_crt > 0 else "CRT measures individual recovery time. Lower values indicate better resilience.")
            else:
                st.info("No CRT data available for selected filters.")
        
        with col2:
            st.markdown("### CRT by Event Type")
            if len(crt_data) > 0:
                crt_by_event = filtered_df.groupby('event_type')['CRT'].mean().sort_values(ascending=True)
                fig = go.Figure(data=[
                    go.Bar(
                        x=crt_by_event.values,
                        y=[EVENT_LABELS.get(et, et.replace('_', ' ').title()) for et in crt_by_event.index],
                        orientation='h',
                        marker=dict(
                            color=COLORS['accent_blue'],
                            line=dict(color=COLORS['primary_text'], width=1)
                        )
                    )
                ])
                fig.update_layout(
                    plot_bgcolor=COLORS['background'],
                    paper_bgcolor=COLORS['background'],
                    font=dict(color=COLORS['primary_text']),
                    height=400,
                    xaxis=dict(title="Average CRT (seconds)", title_font=dict(color=COLORS['secondary_text'])),
                    yaxis=dict(title="", title_font=dict(color=COLORS['secondary_text']))
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Average recovery time by event type. Higher values indicate events that cause longer recovery periods.")
            else:
                st.info("No CRT data available.")
    
    # Row 3: TSI Analysis
    if show_tsi and 'TSI' in filtered_df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Team Support Index (TSI) Distribution")
            tsi_data = filtered_df['TSI'].dropna()
            if len(tsi_data) > 0:
                league_tsi = league_avg.get('tsi_mean', 0)
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=tsi_data,
                    nbinsx=30,
                    marker_color=COLORS['accent_cyan'],
                    opacity=0.7,
                    name='TSI Distribution'
                ))
                
                if league_tsi != 0:
                    fig.add_vline(
                        x=league_tsi,
                        line_dash="dash",
                        line_color=COLORS['accent_blue'],
                        annotation_text=f"League Avg: {league_tsi:.3f}",
                        annotation_position="top"
                    )
                
                # Add reference lines for interpretation
                fig.add_vline(x=0.3, line_dash="dot", line_color=COLORS['success'], annotation_text="Excellent Support")
                fig.add_vline(x=-0.3, line_dash="dot", line_color=COLORS['danger'], annotation_text="Isolation Risk")
                
                fig.update_layout(
                    plot_bgcolor=COLORS['background'],
                    paper_bgcolor=COLORS['background'],
                    font=dict(color=COLORS['primary_text']),
                    height=400,
                    xaxis=dict(title="TSI", title_font=dict(color=COLORS['secondary_text'])),
                    yaxis=dict(title="Frequency", title_font=dict(color=COLORS['secondary_text']))
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"TSI measures collective team response. Positive values indicate support, negative values suggest isolation. League average: {league_tsi:.3f}" if league_tsi != 0 else "TSI measures collective team response. Positive values indicate support, negative values suggest isolation.")
            else:
                st.info("No TSI data available for selected filters.")
        
        with col2:
            st.markdown("### TSI by Event Type")
            if len(tsi_data) > 0:
                tsi_by_event = filtered_df.groupby('event_type')['TSI'].mean().sort_values(ascending=True)
                fig = go.Figure(data=[
                    go.Bar(
                        x=tsi_by_event.values,
                        y=[EVENT_LABELS.get(et, et.replace('_', ' ').title()) for et in tsi_by_event.index],
                        orientation='h',
                        marker=dict(
                            color=COLORS['accent_cyan'],
                            line=dict(color=COLORS['primary_text'], width=1)
                        )
                    )
                ])
                fig.update_layout(
                    plot_bgcolor=COLORS['background'],
                    paper_bgcolor=COLORS['background'],
                    font=dict(color=COLORS['primary_text']),
                    height=400,
                    xaxis=dict(title="Average TSI", title_font=dict(color=COLORS['secondary_text'])),
                    yaxis=dict(title="", title_font=dict(color=COLORS['secondary_text']))
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Average team support by event type. Higher values indicate better collective response to specific error types.")
            else:
                st.info("No TSI data available.")
    
    # Row 4: GIRI Analysis
    if show_giri and 'GIRI' in filtered_df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Goal Impact Response Index (GIRI) Distribution")
            giri_data = filtered_df['GIRI'].dropna()
            if len(giri_data) > 0:
                league_giri = league_avg.get('giri_mean', 0)
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=giri_data,
                    nbinsx=30,
                    marker_color=COLORS['accent_blue'],
                    opacity=0.7,
                    name='GIRI Distribution'
                ))
                
                if league_giri != 0:
                    fig.add_vline(
                        x=league_giri,
                        line_dash="dash",
                        line_color=COLORS['primary_text'],
                        annotation_text=f"League Avg: {league_giri:.3f}",
                        annotation_position="top"
                    )
                
                fig.add_vline(x=0, line_dash="dot", line_color=COLORS['neutral'], annotation_text="Neutral")
                
                fig.update_layout(
                    plot_bgcolor=COLORS['background'],
                    paper_bgcolor=COLORS['background'],
                    font=dict(color=COLORS['primary_text']),
                    height=400,
                    xaxis=dict(title="GIRI", title_font=dict(color=COLORS['secondary_text'])),
                    yaxis=dict(title="Frequency", title_font=dict(color=COLORS['secondary_text']))
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"GIRI measures tactical changes post-goal. Positive values indicate proactive response, negative values suggest disorganization. League average: {league_giri:.3f}" if league_giri != 0 else "GIRI measures tactical changes post-goal. Positive values indicate proactive response, negative values suggest disorganization.")
            else:
                st.info("No GIRI data available for selected filters.")
        
        with col2:
            st.markdown("### GIRI: Goals Scored vs Conceded")
            if len(giri_data) > 0:
                goal_types = filtered_df[filtered_df['GIRI'].notna()]['event_type'].unique()
                if 'goal_scored' in goal_types or 'goal_conceded' in goal_types:
                    giri_comparison = filtered_df[filtered_df['event_type'].isin(['goal_scored', 'goal_conceded'])].groupby('event_type')['GIRI'].mean()
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=['Goal Scored', 'Goal Conceded'],
                            y=[giri_comparison.get('goal_scored', 0), giri_comparison.get('goal_conceded', 0)],
                            marker=dict(
                                color=[COLORS['success'], COLORS['danger']],
                                line=dict(color=COLORS['primary_text'], width=1)
                            )
                        )
                    ])
                    fig.update_layout(
                        plot_bgcolor=COLORS['background'],
                        paper_bgcolor=COLORS['background'],
                        font=dict(color=COLORS['primary_text']),
                        height=400,
                        xaxis=dict(title="Goal Type", title_font=dict(color=COLORS['secondary_text'])),
                        yaxis=dict(title="Average GIRI", title_font=dict(color=COLORS['secondary_text']))
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("Comparison of tactical response after scoring vs conceding. Analyze if team responds differently to different goal situations.")
                else:
                    st.info("No goal events available for GIRI analysis.")
            else:
                st.info("No GIRI data available.")
    
    # Data table
    st.markdown("---")
    st.markdown("## Detailed Data Table")
    st.dataframe(
        filtered_df[['match_id', 'event_type', 'timestamp', 'player_id', 'team_id', 'CRT', 'TSI', 'GIRI']].head(100),
        use_container_width=True,
        height=400
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name=f"r3act_data_{selected_match}_{selected_team}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()

