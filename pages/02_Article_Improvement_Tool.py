import streamlit as st
import pandas as pd
import altair as alt
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
    /* 1. Dashboard Centering & Max-Width */
    [data-testid="stMainViewContainer"] > section > div {
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
        padding-top: 2rem;
    }

    /* 2. Metric Card Styling - Full Width Row Style */
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
    
    /* 3. Target Card (Blue Box) Styling */
    .target-card {
        background: linear-gradient(135deg, #007BFF 0%, #0056b3 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .target-card h3 { 
        color: white !important; 
        margin: 0 0 10px 0;
        font-size: 1.1rem; 
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 8px;
    }

    .target-label { 
        font-weight: bold; 
        text-transform: uppercase; 
        font-size: 0.7rem; 
        color: #dbeafe; 
        margin-top: 10px;
    }

    .target-value { font-size: 0.9rem; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

# --- Quality Data Dictionary ---
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
    importance_order = ['Low-Class', 'Mid-Class', 'High-Class', 'Top-Class', 'Unknown-Class', 'NA-Class']
    df = df[df['quality'].isin(quality_order)].copy()
    df = df[df['importance'].isin(importance_order)].copy()
    df['url'] = "https://en.wikipedia.org/wiki/" + df['article'].astype(str).str.replace(' ', '_')
    
    return df, quality_order, importance_order

df, quality_order, importance_order = load_data()

# --- Main Dashboard ---
if not df.empty:
    st.title("WikiProject Africa: Article Improvement Editor Tool")
    st.markdown(f"### Analyzing {len(df):,} articles for article improvement")
    st.divider()

    # --- ROW 1: Selection and Info Box (Side-by-Side) ---
    col_filters, col_info = st.columns([1.5, 1], gap="large")

    with col_filters:
        st.markdown("### Choose Category:")
        selected_q = st.selectbox("Quality Class:", options=quality_order, index=1)
        selected_i = st.selectbox("Importance Class:", options=importance_order, index=3)

    with col_info:
        info = QUALITY_DESCRIPTIONS.get(selected_q, {"desc": "N/A", "edit": "N/A"})
        st.markdown(f"""
            <div class="target-card">
                <h3>QUALITY: {selected_q}</h3>
                <div class="target-label">Status</div>
                <div class="target-value">{info['desc']}</div>
                <div class="target-label">Action Recommendation</div>
                <div class="target-value"> {info['edit']}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- ROW 2: Metrics (Back to full width row) ---
    mask = (df['quality'] == selected_q) & (df['importance'] == selected_i)
    filtered_pool = df[mask].copy()

    st.markdown("### Metrics")
    if not filtered_pool.empty:
        benchmark_val = filtered_pool['median_views'].median()
        final_df = filtered_pool[filtered_pool['median_views'] >= benchmark_val].sort_values(by='median_views', ascending=False)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Priority Articles", f"{len(final_df):,}")
        m2.metric("Median Views", f"{int(benchmark_val):,}")
        m3.metric("Max Views", f"{int(final_df['median_views'].max()):,}")
    else:
        st.warning(f"No articles found for {selected_q} at {selected_i} importance.")

    st.divider()

    # --- ROW 3: Table and Chart ---
    if not filtered_pool.empty:
        st.markdown("### Articles Recommended for Improvement")
        st.dataframe(
            final_df[['article', 'url', 'median_views']],
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "article": st.column_config.TextColumn("Title"),
                "url": st.column_config.LinkColumn("Link", display_text="Open"),
                "median_views": st.column_config.ProgressColumn(
                    "Total Pageviews", format="%d", min_value=0, max_value=int(final_df['median_views'].max()),
                )
            }
        )
        st.download_button(label="Download CSV Worklist", data=final_df.to_csv(index=False).encode('utf-8'), file_name="worklist.csv")

        st.divider()
        st.markdown("### View Distribution")
        chart_data = final_df.head(15)
        chart = alt.Chart(chart_data).mark_bar(color='#007BFF', cornerRadiusEnd=8).encode(
            x=alt.X('median_views:Q', title='Views'),
            y=alt.Y('article:N', sort='-x', title=None),
            tooltip=['article', 'median_views']
        ).properties(height=450)
        
        st.altair_chart(chart, use_container_width=True)

else:
    st.error("Data not found.")







# import streamlit as st
# import pandas as pd
# import altair as alt
# import zipfile
# from io import TextIOWrapper

# # --- Page Config ---
# st.set_page_config(
#     page_title="WikiProject Africa | Editor Tool", 
#     page_icon="🌍",
#     layout="wide", 
#     initial_sidebar_state="expanded" 
# )

# # --- Updated Custom Styling ---
# st.markdown("""
#     <style>
#     /* 1. Constrain the width of the entire dashboard to prevent stretching */
#     /* This makes the metrics and tables look compact and professional */
#     [data-testid="stMainViewContainer"] > section > div {
#         max-width: 1100px;
#         padding-left: 2rem;
#         padding-right: 2rem;
#         margin-left: auto;
#         margin-right: auto;
#     }

#     /* 2. Metric Card Styling - Slightly smaller for better fit */
#     [data-testid="stMetricValue"] {
#         font-size: 26px !important;
#         font-weight: 700 !important;
#         color: #007BFF;
#     }
#     [data-testid="stMetric"] {
#         background-color: #ffffff;
#         padding: 12px;
#         border-radius: 10px;
#         border: 1px solid #e5e7eb;
#     }
    
#     /* 3. Target Card (Blue Box) Styling */
#     .target-card {
#         background: linear-gradient(135deg, #007BFF 0%, #0056b3 100%);
#         color: white;
#         padding: 18px;
#         border-radius: 10px;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#     }
#     .target-card h3 { 
#         color: white !important; 
#         margin: 0 0 10px 0;
#         font-size: 1rem; 
#         border-bottom: 1px solid rgba(255,255,255,0.2);
#         padding-bottom: 5px;
#     }
#     .target-label { 
#         font-weight: bold; 
#         text-transform: uppercase; 
#         font-size: 0.65rem; 
#         color: #dbeafe; 
#         margin-top: 8px;
#     }
#     .target-value { font-size: 0.8rem; line-height: 1.3; }

#     /* Fix table padding */
#     .stDataFrame { margin-top: 10px; }
#     </style>
#     """, unsafe_allow_html=True)

# # --- Data Loading ---
# @st.cache_data
# def load_data():
#     try:
#         zip_filepath = "data/wikiproject_africa_monthlyviews.zip"
#         csv_filename = "wikiproject_africa_monthlyviews.csv"
#         with zipfile.ZipFile(zip_filepath, "r") as zf:
#             with zf.open(csv_filename) as f:
#                 df = pd.read_csv(TextIOWrapper(f, encoding="utf-8"))
#     except Exception:
#         return pd.DataFrame(), [], []
    
#     df['median_views'] = pd.to_numeric(df['median_views'], errors='coerce').fillna(0)
#     df = df[df['median_views'] >= 1].copy()
    
#     quality_order = ['Stub-Class', 'Start-Class', 'C-Class', 'B-Class', 'GA-Class', 'A-Class', 'FA-Class', 'List-Class']
#     importance_order = ['Low-Class', 'Mid-Class', 'High-Class', 'Top-Class', 'Unknown-Class', 'NA-Class']
#     df = df[df['quality'].isin(quality_order)].copy()
#     df = df[df['importance'].isin(importance_order)].copy()
#     df['url'] = "https://en.wikipedia.org/wiki/" + df['article'].astype(str).str.replace(' ', '_')
    
#     return df, quality_order, importance_order

# df, quality_order, importance_order = load_data()

# # --- Content ---
# if not df.empty:
#     st.title("WikiProject Africa: Article Finder Editor Tool")
#     st.markdown(f"#### Analyzing **{len(df):,}** active articles")
#     st.divider()

#     # --- Row 1: Filters & Target Card ---
#     # 2:1 ratio ensures dropdowns aren't a mile long
#     col_filter, col_card = st.columns([2, 1], gap="medium")

#     with col_filter:
#         st.markdown("### Choose Category:")
#         selected_q = st.selectbox("Improve Quality:", options=quality_order, index=1)
#         selected_i = st.selectbox("Target Importance:", options=importance_order, index=3)

#     with col_card:
#         quality_map = {
#             'Stub-Class': "Basic definition only.",
#             'Start-Class': "Developing but incomplete.",
#             'C-Class': "Substantial but missing info.",
#             'B-Class': "Complete; needs polish.",
#             'GA-Class': "Professional quality.",
#             'A-Class': "Expert source quality.",
#             'FA-Class': "Definitive source.",
#             'List-Class': "List format."
#         }
#         st.markdown(f"""
#             <div class="target-card">
#                 <h3>Goal: {selected_q}</h3>
#                 <div class="target-label">Status</div>
#                 <div class="target-value">{quality_map.get(selected_q, "N/A")}</div>
#                 <div class="target-label">Action</div>
#                 <div class="target-value">🛠 Improve organization.</div>
#             </div>
#             """, unsafe_allow_html=True)

#     # --- Row 2: Metrics ---
#     mask = (df['quality'] == selected_q) & (df['importance'] == selected_i)
#     filtered_pool = df[mask].copy()

#     if not filtered_pool.empty:
#         benchmark_val = filtered_pool['median_views'].median()
#         final_df = filtered_pool[filtered_pool['median_views'] >= benchmark_val].sort_values(by='median_views', ascending=False)

#         st.markdown("### Metrics")
#         m1, m2, m3 = st.columns(3)
#         m1.metric("Priority Articles", f"{len(final_df):,}")
#         m2.metric("Median Views", f"{int(benchmark_val):,}")
#         m3.metric("Max Views", f"{int(final_df['median_views'].max()):,}")

#         st.divider()

#         # --- Row 3: Table ---
#         st.markdown("### Articles Recommended for Improvement")
#         st.dataframe(
#             final_df[['article', 'url', 'median_views']],
#             use_container_width=True,
#             hide_index=True,
#             height=350,
#             column_config={
#                 "article": st.column_config.TextColumn("Title", width="medium"),
#                 "url": st.column_config.LinkColumn("Link", display_text="Open", width="small"),
#                 "median_views": st.column_config.ProgressColumn(
#                     "Impact (Pageviews)", format="%d", min_value=0, max_value=int(final_df['median_views'].max()),
#                 )
#             }
#         )
#         st.download_button(label="Download CSV", data=final_df.to_csv(index=False).encode('utf-8'), file_name="worklist.csv")

#         st.divider()

#         # --- Row 4: Chart ---
#         st.markdown("### View Distribution of User Engagement (pageviews)")
#         chart_data = final_df.head(15)
#         chart = alt.Chart(chart_data).mark_bar(color='#007BFF', cornerRadiusEnd=8).encode(
#             x=alt.X('median_views:Q', title='Views'),
#             y=alt.Y('article:N', sort='-x', title=None),
#             tooltip=['article', 'median_views']
#         ).properties(height=450)
        
#         st.altair_chart(chart, use_container_width=True)

#     else:
#         st.warning(f"No articles found for {selected_q} at {selected_i} importance.")
# else:
#     st.error("Data not found.") 





####ORIGINAL CODE#############
# import streamlit as st
# import pandas as pd
# import altair as alt
# import zipfile
# from io import TextIOWrapper

# # Set page config
# st.set_page_config(page_title="WikiProject Africa: Editorial Tool", layout="wide", initial_sidebar_state="expanded")

# # --- Dictionaries ---
# QUALITY_DESCRIPTIONS = {
#     'Stub-Class': {"desc": "Very basic description; may be little more than a dictionary definition.", "edit": "Add referenced reasons for significance."},
#     'Start-Class': {"desc": "Developing but incomplete; provides some content but needs much more.", "edit": "Provide reliable sources and improve organization."},
#     'C-Class': {"desc": "Substantial but missing important content or contains irrelevant material.", "edit": "Close gaps in content and solve cleanup problems."},
#     'B-Class': {"desc": "Mostly complete; requires work to reach GA standards.", "edit": "Check compliance with Manual of Style."},
#     'GA-Class': {"desc": "Approaching professional quality; meets all 'Good Article' criteria.", "edit": "Subject expert review for remaining weak areas."},
#     'A-Class': {"desc": "Essentially complete; useful to nearly all readers.", "edit": "Expert tweaking and minor style fixes."},
#     'FA-Class': {"desc": "Definitive, outstanding, and professional source.", "edit": "Maintain quality as new information arises."},
#     'List-Class': {"desc": "Primarily a list of links to articles in a subject area.", "edit": "Ensure logical organization and live links."}
# }

# IMPORTANCE_DESCRIPTIONS = {
#     'Top-Class': "Must-have for a print encyclopedia; high global visibility.",
#     'High-Class': "Extremely important within its specific field or region.",
#     'Mid-Class': "Notable but may not be known outside its specific field.",
#     'Low-Class': "Highly specific or niche in nature.",
#     'Unknown-Class': "Importance has not yet been assessed.",
#     'NA-Class': "Importance is not applicable for this page type."
# }

# @st.cache_data
# def load_data():
#     try:
#         zip_filepath = "data/wikiproject_africa_monthlyviews.zip"
#         csv_filename = "wikiproject_africa_monthlyviews.csv"

#         with zipfile.ZipFile(zip_filepath, "r") as zf:
#             with zf.open(csv_filename) as f:
#                 df = pd.read_csv(TextIOWrapper(f, encoding="utf-8"))
#     except FileNotFoundError:
#         st.error("Data file not found.")
#         return pd.DataFrame(), [], []
    
#     df['median_views'] = pd.to_numeric(df['median_views'], errors='coerce').fillna(0)
#     df = df[df['median_views'] >= 1].copy()
    
#     quality_order = ['Stub-Class', 'Start-Class', 'C-Class', 'B-Class', 'GA-Class', 'A-Class', 'FA-Class', 'List-Class']
#     importance_order = ['Low-Class', 'Mid-Class', 'High-Class', 'Top-Class', 'Unknown-Class', 'NA-Class']
    
#     df = df[df['quality'].isin(quality_order)].copy()
#     df = df[df['importance'].isin(importance_order)].copy()
#     df['url'] = "https://en.wikipedia.org/wiki/" + df['article'].astype(str).str.replace(' ', '_')
    
#     return df, quality_order, importance_order

# df, quality_order, importance_order = load_data()

# if not df.empty:
#     st.title("WikiProject Africa: Editorial Prioritization")

#     st.markdown(f"<p style='font-size: 20px;'><strong>Dataset Status:</strong> Analyzing <strong>{len(df):,}</strong> active articles.</p>", unsafe_allow_html=True)
#     st.divider()

#     # --- Filters and Descriptions ---
#     col_filter, col_desc = st.columns([1, 1])

#     with col_filter:
#         st.subheader("Filter Your Worklist")
#         selected_q = st.selectbox("1. Select Quality Class to Improve:", options=quality_order, index=1)
#         selected_i = st.selectbox("2. Select Importance Level:", options=importance_order, index=3) # Defaulting to Top-Class

#     with col_desc:
#         # Check if both selections exist in our dictionaries
#         if selected_q in QUALITY_DESCRIPTIONS and selected_i in IMPORTANCE_DESCRIPTIONS:
            
#             # Combine all info into one formatted string
#             combined_info = f"""
#             #### {selected_q} Quality
#             **Description:** {QUALITY_DESCRIPTIONS[selected_q]['desc']}
            
#             **Edit Suggestion:** {QUALITY_DESCRIPTIONS[selected_q]['edit']}
            
#             ---
#             #### {selected_i} Importance
#             **Definition:** {IMPORTANCE_DESCRIPTIONS[selected_i]}
#             """
            
#             # Display it in a single info box
#             st.info(combined_info)

#     st.divider()

#     # --- Logic: Calculate Benchmark ---
#     # FIX: Wrap selected_i in a list [] because .isin() expects a list-like object
#     mask = (df['quality'] == selected_q) & (df['importance'].isin([selected_i]))
#     filtered_pool = df[mask].copy()

#     if not filtered_pool.empty:
#         benchmark_val = filtered_pool['median_views'].median()
#         st.markdown(f"<p style='font-size: 20px;'><strong>Benchmark: </strong> The median monthly traffic for this group is <strong>{int(benchmark_val):,}</strong> views.</p>", unsafe_allow_html=True)

#         final_df = filtered_pool[filtered_pool['median_views'] >= benchmark_val].sort_values(by='median_views', ascending=False)

#         if not final_df.empty:
#             m1, m2, m3 = st.columns(3)
#             m1.metric("Priority Articles", f"{len(final_df):,}")
#             m2.metric("Group Median", f"{int(benchmark_val):,}")
            
#             max_traffic = final_df['median_views'].max()
#             m3.metric("Max Monthly Traffic", f"{int(max_traffic):,}" if pd.notna(max_traffic) else "N/A")

#             st.subheader(f"Top {selected_q} Priority List")
            
#             csv_columns = ['article', 'url', 'importance', 'median_views']
#             csv_data = final_df[csv_columns].to_csv(index=False).encode('utf-8')

#             st.dataframe(
#                 final_df[['article', 'url', 'importance', 'median_views']],
#                 use_container_width=True,
#                 hide_index=True,
#                 column_config={
#                     "article": "Article Title",
#                     "url": st.column_config.LinkColumn("Wikipedia Link", display_text="Open Page"),
#                     "importance": "Importance",
#                     "median_views": st.column_config.NumberColumn("Median Views", format="%d")
#                 }
#             )

#             st.download_button(label="Download CSV", data=csv_data, file_name=f"WikiProject_Africa_List.csv", mime="text/csv")
#         else:
#             st.warning("No articles found above the benchmark.")
#     else:
#         st.warning(f"No articles found for {selected_q} / {selected_i}.")
# else:
#     st.error("Could not load data.")


