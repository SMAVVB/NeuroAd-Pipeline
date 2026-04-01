"""
NeuroAd Intelligence Dashboard - Main Application
A scientific-professional dashboard for analyzing ad campaign performance.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import local modules
from . import db
from . import loader
from . import brain_viz

# ============================================================================
# Streamlit Configuration
# ============================================================================
st.set_page_config(
    page_title="NeuroAd Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom CSS
# ============================================================================
st.markdown("""
<style>
    /* Dark background for all containers */
    .stApp {
        background-color: #0a0e1a;
        color: #ffffff;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #0f1424;
    }
    
    /* Metric cards with glowing borders */
    .metric-card {
        background: linear-gradient(145deg, #0f1424, #1a2035);
        border: 1px solid #00d4ff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1);
    }
    
    .metric-value {
        font-family: 'Courier New', monospace;
        font-size: 28px;
        font-weight: bold;
        color: #00d4ff;
    }
    
    .metric-label {
        font-size: 14px;
        color: #8b9bb4;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Score bars */
    .score-bar-container {
        background-color: #1a2035;
        border-radius: 4px;
        height: 24px;
        overflow: hidden;
        position: relative;
    }
    
    .score-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    .score-bar-text {
        position: absolute;
        top: 50%;
        left: 10px;
        transform: translateY(-50%);
        font-size: 12px;
        font-weight: bold;
        color: white;
        z-index: 1;
    }
    
    /* Grade badges */
    .grade-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        font-family: 'Courier New', monospace;
    }
    
    .grade-A { background-color: #10b981; color: white; }
    .grade-B { background-color: #06b6d4; color: white; }
    .grade-C { background-color: #f59e0b; color: white; }
    .grade-D { background-color: #ef4444; color: white; }
    .grade-F { background-color: #7c3aed; color: white; }
    
    /* Table styling */
    .dataframe {
        background-color: #0f1424;
    }
    
    .dataframe th {
        background-color: #1a2035;
        color: #00d4ff;
    }
    
    .dataframe td {
        color: #e2e8f0;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #00d4ff;
        color: #0a0e1a;
        border: none;
        border-radius: 8px;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #00a8cc;
    }
    
    /* Selectbox styling */
    .stSelectbox label {
        color: #00d4ff;
        font-weight: bold;
    }
    
    /* Header styling */
    .main-header {
        font-size: 32px;
        font-weight: bold;
        color: #00d4ff;
        margin-bottom: 20px;
    }
    
    .sub-header {
        font-size: 20px;
        color: #7c3aed;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Session State Initialization
# ============================================================================
if 'selected_campaign' not in st.session_state:
    st.session_state.selected_campaign = None
if 'selected_asset_tab2' not in st.session_state:
    st.session_state.selected_asset_tab2 = None
if 'selected_asset_tab3' not in st.session_state:
    st.session_state.selected_asset_tab3 = None
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False

# ============================================================================
# Helper Functions
# ============================================================================

def get_grade_color(grade: str) -> str:
    """Get CSS class for grade badge."""
    if grade == 'A':
        return 'grade-A'
    elif grade == 'B':
        return 'grade-B'
    elif grade == 'C':
        return 'grade-C'
    elif grade == 'D':
        return 'grade-D'
    else:
        return 'grade-F'


def format_score(value: float, default: str = "—") -> str:
    """Format a score value."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    return f"{value:.3f}"


def create_score_bar(score: float, color: str = "#00d4ff") -> str:
    """Create a custom HTML score bar."""
    if score is None or (isinstance(score, float) and np.isnan(score)):
        return '<div class="score-bar-container" style="opacity: 0.5;"><span class="score-bar-text">—</span></div>'
    
    width = min(max(score * 100, 0), 100)
    return f'''
        <div class="score-bar-container">
            <div class="score-bar-fill" style="width: {width}%; background-color: {color};"></div>
            <span class="score-bar-text">{score:.3f}</span>
        </div>
    '''


def create_brain_map_html(npy_path: str) -> str:
    """Create HTML for brain map display."""
    if not npy_path:
        return '<div style="text-align: center; color: #8b9bb4;">No brain map available</div>'
    
    npy_path = Path(npy_path)
    png_path = brain_viz.get_brain_map_path(str(npy_path))
    png_path = Path(png_path)
    
    if png_path.exists():
        return f'<img src="{png_path}" style="width: 100%; border-radius: 8px;">'
    else:
        return f'<div style="text-align: center; color: #8b9bb4;">Brain map PNG not found</div>'


# ============================================================================
# Sidebar
# ============================================================================

st.sidebar.markdown("### 🧠 NeuroAd")
st.sidebar.markdown("##### Intelligence Platform")

# Campaign selector
all_campaigns = db.get_all_campaigns()

if not st.session_state.db_initialized and all_campaigns:
    st.session_state.db_initialized = True

# Add refresh button
col1, col2 = st.sidebar.columns([3, 1])
with col1:
    selected_campaign = st.selectbox(
        "Campaign",
        all_campaigns,
        index=0 if all_campaigns else None,
        key="campaign_selector"
    )

with col2:
    if st.button("🔄", help="Refresh scores"):
        if selected_campaign:
            with st.spinner(f"Loading {selected_campaign}..."):
                loader.refresh_campaign(selected_campaign)
            st.rerun()

st.sidebar.markdown("---")

# Score type filter
score_filter = st.sidebar.selectbox(
    "Score Type",
    ["Composite", "Neural Only", "Saliency Only"],
    key="score_filter"
)

# Info box
if selected_campaign:
    stats = db.get_campaign_stats(selected_campaign)
    last_updated = db.get_last_updated(selected_campaign)
    
    st.sidebar.markdown("##### Statistics")
    st.sidebar.markdown(f"**Assets:** {stats.get('total_assets', 0)}")
    st.sidebar.markdown(f"**TRIBE:** {stats.get('tribe_assets', 0)}")
    if last_updated:
        st.sidebar.markdown(f"**Updated:** {last_updated}")

# ============================================================================
# Main Content
# ============================================================================

st.markdown('<div class="main-header">Campaign Overview</div>', unsafe_allow_html=True)

if not selected_campaign:
    st.info("Please select a campaign from the sidebar to view scores.")
    st.stop()

# Get campaign scores
scores = db.get_campaign_scores(selected_campaign)

if not scores:
    st.info(f"No scores found for campaign '{selected_campaign}'. Please run the loader.")
    st.stop()

# ============================================================================
# Tab 1: Campaign Overview
# ============================================================================

tab1, tab2, tab3 = st.tabs(["Campaign Overview", "Creative Deep Dive", "Saliency Analysis"])

with tab1:
    # KPI Cards
    st.markdown("##### Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Best Creative
    best_asset = max(scores, key=lambda x: x.get('total_score', 0) or 0)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Best Creative</div>
            <div class="metric-value">{best_asset.get('asset_name', 'N/A')}</div>
            <div style="color: #00d4ff; font-size: 18px;">{format_score(best_asset.get('total_score'))}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Avg Neural Engagement
    avg_neural = sum(s.get('neural_engagement', 0) or 0 for s in scores) / len(scores) if scores else 0
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Neural Engagement</div>
            <div class="metric-value">{format_score(avg_neural)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Max Emotional Impact
    max_emotional = max(scores, key=lambda x: x.get('emotional_impact', 0) or 0)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Highest Emotional Impact</div>
            <div class="metric-value">{format_score(max_emotional.get('emotional_impact'))}</div>
            <div style="color: #7c3aed; font-size: 12px;">{max_emotional.get('asset_name', '')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Assets analyzed
    total_assets = len(scores)
    tribe_assets = sum(1 for s in scores if s.get('has_tribe_preds', 0))
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Assets Analyzed</div>
            <div class="metric-value">{tribe_assets}/{total_assets}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Ranking Table
    st.markdown("##### Ranking")
    
    # Prepare data for table
    table_data = []
    for i, score in enumerate(scores, 1):
        breakdown = score.get('breakdown', {})
        if isinstance(breakdown, str):
            import json
            try:
                breakdown = json.loads(breakdown)
            except:
                breakdown = {}
        
        table_data.append({
            "Rank": i,
            "Creative Name": score.get('asset_name', ''),
            "Grade": score.get('grade', ''),
            "Composite Score": score.get('total_score'),
            "Neural Engagement": score.get('neural_engagement'),
            "Emotional Impact": score.get('emotional_impact'),
            "Visual Attention": breakdown.get('visual_attention', 0) if breakdown else 0,
            "Brand Consistency": breakdown.get('brand_consistency', 0) if breakdown else 0,
            "asset_data": score  # Store full data for deep dive
        })
    
    # Create DataFrame
    df = pd.DataFrame(table_data)
    
    # Display table with custom formatting
    st.dataframe(
        df[['Rank', 'Creative Name', 'Grade', 'Composite Score', 'Neural Engagement', 
            'Emotional Impact', 'Visual Attention', 'Brand Consistency']].style
        .format({
            'Composite Score': '{:.3f}',
            'Neural Engagement': '{:.3f}',
            'Emotional Impact': '{:.3f}',
        })
        .applymap(
            lambda x: f'background-color: #1a2035; color: #00d4ff' if isinstance(x, str) and x.startswith('grade-') else '',
            subset=['Grade']
        ),
        use_container_width=True,
        hide_index=True
    )
    
    # Store selected asset for deep dive
    if len(df) > 0:
        st.session_state.selected_asset_tab2 = df.iloc[0]['Creative Name']
        st.session_state.selected_asset_tab3 = df.iloc[0]['Creative Name']
    
    st.markdown("---")
    
    # Radar Chart
    st.markdown("##### Score Radar Chart")
    
    # Get breakdown data for radar
    radar_scores = []
    for score in scores:
        breakdown = score.get('breakdown', {})
        if isinstance(breakdown, str):
            try:
                breakdown = json.loads(breakdown)
            except:
                breakdown = {}
        
        radar_scores.append({
            'asset_name': score.get('asset_name', ''),
            'neural_engagement': score.get('neural_engagement', 0) or 0,
            'emotional_impact': score.get('emotional_impact', 0) or 0,
            'visual_attention': breakdown.get('visual_attention', 0) if breakdown else 0,
            'brand_consistency': breakdown.get('brand_consistency', 0) if breakdown else 0,
            'facial_emotion': breakdown.get('facial_emotion', 0) if breakdown else 0,
        })
    
    if radar_scores:
        fig = go.Figure()
        
        colors = ['#00d4ff', '#7c3aed', '#f59e0b', '#10b981', '#ef4444', '#3b82f6']
        
        for i, score_data in enumerate(radar_scores):
            fig.add_trace(go.Scatterpolar(
                r=[
                    score_data['neural_engagement'],
                    score_data['emotional_impact'],
                    score_data['visual_attention'],
                    score_data['brand_consistency'],
                    score_data['facial_emotion'],
                    score_data['neural_engagement']  # Close the loop
                ],
                theta=['Neural Engagement', 'Emotional Impact', 'Visual Attention', 
                       'Brand Consistency', 'Facial Emotion', 'Neural Engagement'],
                fill='toself',
                name=score_data['asset_name'],
                line=dict(color=colors[i % len(colors)]),
                opacity=0.7
            ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    color="#8b9bb4"
                ),
                angularaxis=dict(color="#8b9bb4")
            ),
            legend=dict(
                y=0.5,
                traceorder="reversed",
                font=dict(size=10),
                bgcolor="#0f1424",
                bordercolor="#1a2035",
                borderwidth=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# Tab 2: Creative Deep Dive
# ============================================================================

with tab2:
    st.markdown('<div class="sub-header">Creative Deep Dive</div>', unsafe_allow_html=True)
    
    # Asset selector
    asset_names = [s.get('asset_name', '') for s in scores]
    selected_asset = st.selectbox(
        "Select Creative",
        asset_names,
        index=0 if asset_names else None,
        key="deep_dive_selector"
    )
    
    if not selected_asset:
        st.stop()
    
    # Get selected asset data
    asset_data = next((s for s in scores if s.get('asset_name') == selected_asset), None)
    
    if not asset_data:
        st.error(f"Data not found for {selected_asset}")
        st.stop()
    
    # 2-column layout
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown("##### Score Breakdown")
        
        # Get breakdown data
        breakdown = asset_data.get('breakdown', {})
        weights = asset_data.get('weights_used', {})
        
        if isinstance(breakdown, str):
            try:
                breakdown = json.loads(breakdown)
            except:
                breakdown = {}
        
        if isinstance(weights, str):
            try:
                weights = json.loads(weights)
            except:
                weights = {}
        
        # Create horizontal bar chart
        if breakdown:
            fig = go.Figure()
            
            dimensions = ['neural_engagement', 'emotional_impact', 'visual_attention', 
                         'brand_consistency', 'facial_emotion', 'audio_engagement']
            colors = ['#00d4ff', '#7c3aed', '#f59e0b', '#10b981', '#ef4444', '#3b82f6']
            
            for i, dim in enumerate(dimensions):
                if dim in breakdown:
                    fig.add_trace(go.Bar(
                        y=[dim.replace('_', ' ').title()],
                        x=[breakdown[dim]],
                        orientation='h',
                        marker_color=colors[i % len(colors)],
                        text=f"{breakdown[dim]:.3f}",
                        textposition='auto',
                        hovertemplate=f"{dim.replace('_', ' ').title()}: %{{x:.3f}}<extra></extra>"
                    ))
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(range=[0, 1], color="#8b9bb4"),
                yaxis=dict(color="#8b9bb4"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        st.markdown("##### TRIBE ROI Scores")
        
        # ROI scores table
        roi_data = {
            'ROI': ['TPJ', 'FFA', 'PPA', 'V5', 'Broca', 'A1'],
            'Score': [0.0] * 6
        }
        
        # Try to extract ROI scores from data
        tribe = asset_data.get('tribe', {})
        if isinstance(tribe, dict):
            roi_data['Score'] = [
                tribe.get('tpj', 0) or 0,
                tribe.get('ffa', 0) or 0,
                tribe.get('ppa', 0) or 0,
                tribe.get('v5', 0) or 0,
                tribe.get('broca', 0) or 0,
                tribe.get('a1', 0) or 0,
            ]
        
        roi_df = pd.DataFrame(roi_data)
        
        # Create heatmap colors
        def color_rois(val):
            if val >= 0.5:
                return 'background-color: #ef4444; color: white'
            elif val >= 0.3:
                return 'background-color: #f59e0b; color: white'
            elif val >= 0.1:
                return 'background-color: #fbbf24; color: black'
            else:
                return 'background-color: #3b82f6; color: white'
        
        st.dataframe(
            roi_df.style.applymap(color_rois, subset=['Score']),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        st.markdown("##### Emotion Analysis")
        
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            dominant_emotion = asset_data.get('dominant_emotion', '')
            if dominant_emotion:
                st.markdown(f"**Dominant Emotion:** {dominant_emotion}")
        
        with col_e2:
            valence = asset_data.get('emotional_valence')
            if valence is not None:
                # Create gauge chart
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=valence,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Valence"},
                    gauge={
                        'axis': {'range': [-1, 1], 'tickcolor': "#8b9bb4"},
                        'bar': {'color': "#00d4ff"},
                        'steps': [
                            {'range': [-1, -0.5], 'color': "#ef4444"},
                            {'range': [-0.5, 0], 'color': "#f59e0b"},
                            {'range': [0, 0.5], 'color': "#fbbf24"},
                            {'range': [0.5, 1], 'color': "#10b981"},
                        ],
                    }
                ))
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=200
                )
                st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Brain Map")
        
        brain_map_path = asset_data.get('brain_map_path')
        
        if asset_data.get('tribe_error'):
            st.warning(f"TRIBE inference failed for this asset: {asset_data.get('tribe_error')}")
        elif brain_map_path:
            npy_path = Path(brain_map_path)
            if npy_path.exists():
                png_path = brain_viz.get_brain_map_path(str(npy_path))
                
                if Path(png_path).exists():
                    st.image(png_path, use_container_width=True)
                else:
                    if st.button("Generate Brain Map"):
                        with st.spinner("Generating brain map..."):
                            success = brain_viz.generate_brain_map(str(npy_path), png_path)
                            if success:
                                st.success("Brain map generated!")
                                st.rerun()
                            else:
                                st.error("Failed to generate brain map")
            else:
                st.info(f"TRIBE predictions file not found: {brain_map_path}")
        else:
            st.info("No brain map available for this asset")
        
        st.markdown("---")
        
        st.markdown("##### Temporal Profile")
        
        if brain_map_path:
            npy_path = Path(brain_map_path)
            if npy_path.exists():
                temporal_data = brain_viz.load_temporal_profile(str(npy_path))
                
                if temporal_data:
                    timesteps, mean_activation = temporal_data
                    temporal_peak = asset_data.get('temporal_peak', 0) or 0
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=timesteps,
                        y=mean_activation,
                        mode='lines+markers',
                        name='Mean Activation',
                        line=dict(color='#00d4ff', width=2),
                        marker=dict(size=4)
                    ))
                    
                    # Add vertical line for temporal peak
                    fig.add_vline(
                        x=temporal_peak,
                        line_dash="dash",
                        line_color="#f59e0b",
                        annotation_text=f"Peak: {temporal_peak}s",
                        annotation_position="top"
                    )
                    
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="Time (seconds)",
                        yaxis_title="Mean Activation",
                        xaxis=dict(color="#8b9bb4"),
                        yaxis=dict(color="#8b9bb4"),
                        margin=dict(l=20, r=20, t=20, b=20),
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Could not load temporal data")
            else:
                st.info("TRIBE predictions file not found")
        else:
            st.info("No brain map data available")

# ============================================================================
# Tab 3: Saliency Analysis
# ============================================================================

with tab3:
    st.markdown('<div class="sub-header">Saliency Analysis</div>', unsafe_allow_html=True)
    
    # Asset selector
    selected_asset_saliency = st.selectbox(
        "Select Creative",
        asset_names,
        index=0 if asset_names else None,
        key="saliency_selector"
    )
    
    if not selected_asset_saliency:
        st.stop()
    
    # Get campaign path
    campaign_path = Path.home() / "neuro_pipeline_project" / "campaigns" / selected_campaign
    scores_path = campaign_path / "scores"
    
    # Find saliency frames
    frame_files = sorted(scores_path.glob(f"{selected_asset_saliency}_saliency_frame*.png"))
    heatmap_file = scores_path / f"{selected_asset_saliency}_saliency_heatmap.png"
    
    # Display frames in grid
    if frame_files:
        st.markdown("##### Saliency Frames")
        
        cols = st.columns(min(4, len(frame_files)))
        
        for i, frame_file in enumerate(frame_files):
            with cols[i % 4]:
                st.image(str(frame_file), use_container_width=True)
                st.caption(f"Frame {i}")
    
    # Display heatmap
    if heatmap_file.exists():
        st.markdown("##### Saliency Heatmap")
        st.image(str(heatmap_file), use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("##### Saliency Scores")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        center_bias = asset_data.get('center_bias')
        if center_bias is not None:
            st.metric("Center Bias", f"{center_bias:.3f}")
    
    with col_s2:
        saliency_score = asset_data.get('saliency_score')
        if saliency_score is not None:
            st.metric("Saliency Score", f"{saliency_score:.3f}")

# ============================================================================
# Run Loader on Start
# ============================================================================

# Auto-load campaign if not already loaded
if selected_campaign and not scores:
    with st.spinner(f"Loading {selected_campaign} scores..."):
        loader.load_campaign(selected_campaign)
    st.rerun()
