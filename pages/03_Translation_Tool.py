import streamlit as st
import pandas as pd
import altair as alt
import zipfile
import io

# page config
st.set_page_config(
    page_title="WikiProject Africa | Translation Tool", 
    page_icon="",
    layout="wide", 
    initial_sidebar_state="expanded" 
)

# custom styling section
st.markdown("""
    <style>
    [data-testid="stMainViewContainer"] > section > div {
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
        padding-top: 2rem;
    }
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
    .target-card {
        background: linear-gradient(135deg, #1D3557 0%, #457B9D 100%);
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
        color: #A8DADC; 
        margin-top: 10px;
    }
    .target-value { font-size: 0.9rem; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

# load data
@st.cache_data
def load_data():
    zip_path = "data/african_countries_dpdp_views.zip"
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
            if not csv_files: return pd.DataFrame()
            with zf.open(csv_files[0]) as f:
                return pd.read_csv(f)
    except Exception:
        return pd.DataFrame()

df = load_data()

# main dashboard
if not df.empty:
    st.title("WikiProject Africa: Translation Tool")
    st.markdown("### Identifying high-traffic content for localization")
    st.divider()

    # selection
    col_filters, col_info = st.columns([1.5, 1], gap="large")

    with col_filters:
        st.markdown("### Filter by Region:")
        countries = sorted(df['Country'].unique())
        selected_country = st.selectbox("Select Target Country:", options=countries)
        
        
        mask = (df['Country'] == selected_country) & (df['Native'] == 'Non-Native')
        translation_demand = df[mask].copy()
        
        #aggregating
        aggregated = translation_demand.groupby('Item_ID').agg({
            'Page_Title': 'first',
            'language': 'first',
            'Project': 'first',
            'Views': 'sum'
        }).reset_index().sort_values(by='Views', ascending=False)

        #links
        def make_wiki_link(row):
            # Formats: https://en.wikipedia.org/wiki/Article_Name
            # Assuming 'Project' is 'en.wikipedia', we add '.org'
            base = f"https://{row['Project']}.org/wiki/"
            clean_title = str(row['Page_Title']).replace(" ", "_")
            return base + clean_title

        aggregated['wiki_url'] = aggregated.apply(make_wiki_link, axis=1)

    with col_info:
        source_langs = sorted(aggregated['language'].unique())
        lang_string = ", ".join(source_langs) if source_langs else "None found"
        lang_count = len(source_langs)

        st.markdown(f"""
            <div class="target-card">
                <h3>DEMAND IN: {selected_country}</h3>
                <div class="target-label">Source Languages ({lang_count})</div>
                <div class="target-value">{lang_string}</div>
                <div class="target-label">Action</div>
                <div class="target-value">Translate the articles below to increase local language coverage.</div>
            </div>
            """, unsafe_allow_html=True)

    # impact metrics section
    st.markdown("### Impact Metrics")
    m1, m2, m3 = st.columns(3)
    
    total_views = aggregated['Views'].sum()
    unique_items = len(aggregated)
    avg_impact = aggregated['Views'].mean() if unique_items > 0 else 0

    m1.metric("Articles to Translate", f"{unique_items:,}")
    m2.metric("Non-Native Language Articles Total Pageviews", f"{int(total_views):,}")
    m3.metric("Avg Views/Article", f"{int(avg_impact):,}")

    st.divider()

    # article table
    st.markdown(f"### Articles Recommended for Translation: {selected_country}")
    
    st.dataframe(
        aggregated[['Page_Title', 'Views', 'language', 'wiki_url']],
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Page_Title": st.column_config.TextColumn("Article Title"),
            "language": st.column_config.TextColumn("Source Language"),
            "wiki_url": st.column_config.LinkColumn("Read Original", display_text="Link"),
            "Views": st.column_config.ProgressColumn(
                "Non-Native Views", 
                format="%d", 
                min_value=0, 
                max_value=int(aggregated['Views'].max()) if not aggregated.empty else 100
            )
        }
    )

    # visualization of 10 15 articles
    if not aggregated.empty:
        st.divider()
        st.markdown("### View Distribution (Top 15 Articles)")
        chart_data = aggregated.head(15)
        chart = alt.Chart(chart_data).mark_bar(color='#007BFF', cornerRadiusEnd=8).encode(
            x=alt.X('Views:Q', title='Aggregate Non-Native Views'),
            y=alt.Y('Page_Title:N', sort='-x', title=None),
            tooltip=['Page_Title', 'Views', 'language']
        ).properties(height=450)
        
        st.altair_chart(chart, use_container_width=True)

else:
    st.error("Data could not be loaded from 'data/african_countries_dpdp_views.zip'. Please verify the file path.")