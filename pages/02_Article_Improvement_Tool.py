import streamlit as st
import pandas as pd
import zipfile
from io import TextIOWrapper

# --- Page Config ---
st.set_page_config(
    page_title="WikiProject Africa | Editor Tool", 
    page_icon="🌍",
    layout="wide", 
    initial_sidebar_state="expanded" 
)

# --- Custom Styling ---
st.markdown("""
    <style>
    /* Global Page Width */
    [data-testid="stMainViewContainer"] > section > div {
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
        padding-top: 2rem;
    }
    
    /* Standard Metric Styling (Kept Clean) */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #007BFF;
    }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
    }
            
    
    /* TARGETED STYLING: Only for the Info Box in the right column */
    .info-box-container [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f0f7ff !important;
        border: 1px solid #007BFF !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
    
    .target-header {
        color: #007BFF;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.85rem;
        margin-top: 10px;
        margin-bottom: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Metadata Dictionaries ---
QUALITY_DESCRIPTIONS = {
    'Stub-Class': {"desc": "Very basic description; may be little more than a dictionary definition.", "edit": "Add referenced reasons for significance."},
    'Start-Class': {"desc": "Developing but incomplete; provides some content but needs much more.", "edit": "Provide reliable sources and improve organization."},
    'C-Class': {"desc": "Substantial but missing important content or contains irrelevant material.", "edit": "Close gaps in content and solve cleanup problems."},
    'B-Class': {"desc": "Mostly complete; requires work to reach GA standards.", "edit": "Check compliance with Manual of Style."},
    'GA-Class': {"desc": "Approaching professional quality; meets all 'Good Article' criteria.", "edit": "Subject expert review for remaining weak areas."},
    'A-Class': {"desc": "Essentially complete; useful to nearly all readers.", "edit": "Expert tweaking and minor style fixes."},
    'FA-Class': {"desc": "Definitive, outstanding, and professional source.", "edit": "Maintain quality as new information arises."},
    'List-Class': {"desc": "Primarily a list of links to articles in a subject area.", "edit": "Ensure logical organization and live links."}
}

IMPORTANCE_DESCRIPTIONS = {
    'Top-Class': "Must-have for a print encyclopedia; high global visibility.",
    'High-Class': "Extremely important within its specific field or region.",
    'Mid-Class': "Notable but may not be known outside its specific field.",
    'Low-Class': "Highly specific or niche in nature.",
    'Unknown-Class': "Importance has not yet been assessed.",
    'NA-Class': "Importance is not applicable for this page type."
}

# --- Data Loading ---
@st.cache_data
def load_data():
    try:
        zip_filepath = "data/wikiproject_africa_monthlyviews.zip"
        csv_filename = "wikiproject_africa_monthlyviews.csv"
        with zipfile.ZipFile(zip_filepath, "r") as zf:
            with zf.open(csv_filename) as f:
                df = pd.read_csv(TextIOWrapper(f, encoding="utf-8"))
    except Exception:
        return pd.DataFrame(), [], []
    
    df['median_views'] = pd.to_numeric(df['median_views'], errors='coerce').fillna(0)
    df = df[df['median_views'] >= 1].copy()
    
    quality_order = list(QUALITY_DESCRIPTIONS.keys())
    importance_order = list(IMPORTANCE_DESCRIPTIONS.keys())
    
    df = df[df['quality'].isin(quality_order)].copy()
    df = df[df['importance'].isin(importance_order)].copy()
    df['url'] = "https://en.wikipedia.org/wiki/" + df['article'].astype(str).str.replace(' ', '_')
    
    return df, quality_order, importance_order

df, quality_order, importance_order = load_data()

# --- Main Dashboard ---
if not df.empty:
    st.title("WikiProject Africa: Article Improvement Editor Tool")
    
    st.markdown(f"""
    This tool identifies high-impact articles within the **WikiProject Africa** scope that require content improvements. 
    By cross-referencing article quality and importance with pageviews, editors can prioritize work on 
    consistently viewed articles that currently lack professional depth.
    
    **Note on Data Scope:** This tool analyzes a priority subset of **{len(df):,} articles** that have consistent monthly viewership.
    """)
    
    st.divider()

    # --- ROW 1: Selection and Info Box ---
    col_filters, col_info = st.columns([1.5, 1], gap="large")

    with col_filters:
        st.subheader("Selection Criteria")
        selected_q = st.selectbox("Quality Class:", options=quality_order, index=1)
        selected_i_list = st.multiselect("Importance Classes:", options=importance_order, default=["Low-Class"])

    # We wrap col_info in a custom div class to ensure the CSS only applies here
    with col_info:
        st.markdown('<div class="info-box-container">', unsafe_allow_html=True)
        with st.container(border=True):
            q_info = QUALITY_DESCRIPTIONS.get(selected_q, {"desc": "N/A", "edit": "N/A"})
            
            st.markdown(f'<p class="target-header">{selected_q} Quality Definition</p>', unsafe_allow_html=True)
            st.write(q_info['desc'])
            
            if selected_i_list:
                st.markdown('<p class="target-header">Importance Class Definitions</p>', unsafe_allow_html=True)
                for imp in selected_i_list:
                    desc = IMPORTANCE_DESCRIPTIONS.get(imp, "N/A")
                    st.markdown(f"**{imp}:** {desc}")
            else:
                st.warning("Please select at least one Importance Class.")

            st.markdown('<p class="target-header">Action Recommendation</p>', unsafe_allow_html=True)
            st.info(q_info['edit'])
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ROW 2: Metrics ---
    mask = (df['quality'] == selected_q) & (df['importance'].isin(selected_i_list))
    filtered_pool = df[mask].copy()

    st.markdown("### Metrics")
    if not filtered_pool.empty:
        benchmark_val = filtered_pool['median_views'].median()
        final_df = filtered_pool[filtered_pool['median_views'] >= benchmark_val].sort_values(by='median_views', ascending=False)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Number of Recommended Articles", f"{len(final_df):,}", help="Count of articles above the median threshold.")
        m2.metric("Median Views", f"{int(benchmark_val):,}", help="The median pageview count for this selection.")
        m3.metric("Max Views", f"{int(final_df['median_views'].max()):,}", help="Highest views recorded in this selection.")
        
        st.divider()

        # --- ROW 3: Download and Table ---
        csv_data = final_df[['article', 'url', 'median_views']].to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Worklist (CSV)", data=csv_data, file_name=f"worklist_{selected_q}.csv", mime='text/csv')

        st.dataframe(
            final_df[['article', 'url', 'median_views']],
            use_container_width=True,
            hide_index=True,
            height=450,
            column_config={
                "article": st.column_config.TextColumn("Title"),
                "url": st.column_config.LinkColumn("Link", display_text="Open"),
                "median_views": st.column_config.ProgressColumn("Monthly Views", format="%d", min_value=0, max_value=int(final_df['median_views'].max()))
            }
        )
    else:
        st.warning("No articles found matching your current selection.")

else:
    st.error("Data not found.")

