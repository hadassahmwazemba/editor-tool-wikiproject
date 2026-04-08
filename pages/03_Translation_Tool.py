import streamlit as st
import pandas as pd
import zipfile
import json
import os
import codecs
from urllib.parse import unquote, quote

# Page Configuration
st.set_page_config(
    page_title="WikiProject Africa | Translation Tool",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
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
    .target-value {
        font-size: 0.9rem;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

# Helpers
def normalize_text(x):
    return str(x).strip().lower()


def fix_mojibake(text):
    """
    Repairs common UTF-8 mojibake such as:
    'CÃ´te d'Ivoire' -> 'Côte d'Ivoire'
    'MÃ©morial' -> 'Mémorial'
    """
    if not isinstance(text, str):
        text = str(text)

    original = text

    # Try common bad decodings
    for enc in ("latin1", "cp1252"):
        try:
            repaired = text.encode(enc).decode("utf-8")
            text = repaired
            break
        except Exception:
            continue

    # If repair made things worse somehow, fall back
    if not text:
        return original
    return text


def decode_title(val):
    """
    Makes article titles readable by:
    - fixing UTF-8 mojibake like AlgÃ©rie -> Algérie
    - decoding unicode escape sequences like \\u00e9
    - decoding percent-encoding if present
    - replacing underscores with spaces
    """
    try:
        text = str(val)

        # 1. Decode percent-encoding first if present
        text = unquote(text)

        # 2. Fix mojibake
        text = fix_mojibake(text)

        # 3. Decode literal unicode escapes only when they are present
        if "\\u" in text or "\\x" in text:
            try:
                text = codecs.decode(text, "unicode_escape")
            except Exception:
                pass

        # Clean up formatting
        text = text.replace("_", " ").strip()

        return text
    except Exception:
        return str(val).replace("_", " ").strip()


def make_url_title(title):
    """
    Converts a readable article title into a Wikipedia-safe URL title.
    Keeps accents correctly and URL-encodes them properly.
    """
    title = str(title).strip().replace(" ", "_")
    return quote(title, safe=":/()_'-")


# Data Loading Functions
@st.cache_data
def load_mapping():
    mapping_path = "data/language_mapping.json"
    try:
        if os.path.exists(mapping_path):
            with open(mapping_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading language mapping: {e}")
    return {}


@st.cache_data
def load_data():
    zip_path = "data/african_countries_dpdp_views.zip"
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_files = [f for f in zf.namelist() if f.endswith(".csv")]
            if not csv_files:
                return pd.DataFrame()

            with zf.open(csv_files[0]) as f:
                df = pd.read_csv(f)

                if "Page_Title" in df.columns:
                    df["Page_Title"] = df["Page_Title"].apply(decode_title)

                return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


# Initialize data
df = load_data()
lang_map = load_mapping()

# Support either:
# {"en": "English", "fr": "French"}
# or
# {"English": "en", "French": "fr"}
code_to_name = {}
name_to_code = {}

if lang_map:
    sample_key = next(iter(lang_map.keys()))
    sample_val = lang_map[sample_key]

    # If keys look like language codes, assume code -> name
    if len(str(sample_key).strip()) <= 5:
        code_to_name = {
            normalize_text(k): str(v).strip()
            for k, v in lang_map.items()
        }
        name_to_code = {
            normalize_text(v): str(k).strip()
            for k, v in lang_map.items()
        }
    else:
        # Otherwise assume name -> code
        name_to_code = {
            normalize_text(k): str(v).strip()
            for k, v in lang_map.items()
        }
        code_to_name = {
            normalize_text(v): str(k).strip()
            for k, v in lang_map.items()
        }


def get_display_name(language_value):
    """
    Show readable language names in the UI.
    If the raw value is already a name, keep it readable.
    If it's a code, convert it to the full language name.
    """
    val = normalize_text(language_value)

    if val in code_to_name:
        return code_to_name[val]

    if val in name_to_code:
        return str(language_value).strip()

    return str(language_value).strip()


def resolve_language_code(language_value):
    """
    Returns the correct Wikipedia language code whether the raw value
    is already a code or is a language name.
    """
    val = normalize_text(language_value)

    # Already a language code
    if val in code_to_name:
        return val.lower()

    # Language name -> code
    if val in name_to_code:
        return name_to_code[val].lower()

    # Fallback: assume the raw value is already the code
    return val.lower()


def make_wiki_link(row):
    """
    Always create a standard Wikipedia article URL:
    https://<lang>.wikipedia.org/wiki/<title>

    This avoids accidental domains like nostalgia.wikipedia.org.
    """

    # FORCE English to use "en"
    if normalize_text(row["language"]) in {"english", "en", "eng"}:
        lang_code = "en"
    else:
        lang_code = resolve_language_code(row["language"])

    url_title = make_url_title(row["Page_Title"])
    return f"https://{lang_code}.wikipedia.org/wiki/{url_title}"


if not df.empty:
    # 5. Header Section
    st.title("WikiProject Africa: Translation Tool")

    st.markdown("""
    This tool is designed to bridge the knowledge gap on Wikiproject Africa across the continent.
    by identifying articles that are frequently viewed in non-native languages
    within specific African countries for recommendations on articles to translate.

    **Objective:** To prioritize content for translation into local languages. By translating
    high-traffic articles, vital information can be accessible to readers in the language
    they understand best to increase user engagement and local language representation online.
    """)
    st.divider()

    # Filters Section
    col_filters, col_info = st.columns([1.5, 1], gap="large")

    with col_filters:
        st.markdown("### Choose Category:")

        countries = sorted(df["Country"].dropna().unique())
        selected_country = st.selectbox("1. Select Target Country:", options=countries)

        mask = (df["Country"] == selected_country) & (df["Native"] == "Non-Native")
        translation_demand = df[mask].copy()

        aggregated = (
            translation_demand.groupby("Item_ID", as_index=False)
            .agg({
                "Page_Title": "first",
                "language": "first",
                "Project": "first" if "Project" in translation_demand.columns else lambda x: None,
                "Views": "sum"
            })
            .sort_values(by="Views", ascending=False)
        )

        available_entries = sorted(aggregated["language"].dropna().unique())
        entry_to_display = {
            entry: get_display_name(entry)
            for entry in available_entries
        }

        selected_displays = st.multiselect(
            "2. Filter by Source Language:",
            options=list(entry_to_display.values()),
            default=list(entry_to_display.values()),
            help="Source Language refers to the language in which the article is currently being accessed by readers in this country, even though it is not a native language there. These are the languages from which translation demand has been identified."
        )

        selected_raw_values = [
            raw_value for raw_value, display_value in entry_to_display.items()
            if display_value in selected_displays
        ]

        if selected_raw_values:
            aggregated = aggregated[aggregated["language"].isin(selected_raw_values)].copy()
            aggregated["Language_Name"] = aggregated["language"].apply(get_display_name)
        else:
            st.warning("Please select at least one language.")
            aggregated = pd.DataFrame(columns=[
                "Item_ID", "Page_Title", "language", "Project", "Views", "Language_Name"
            ])

        if not aggregated.empty:
            aggregated["wiki_url"] = aggregated.apply(make_wiki_link, axis=1)

    with col_info:
        final_langs = sorted(aggregated["Language_Name"].unique()) if not aggregated.empty else []
        lang_string = ", ".join(final_langs) if final_langs else "No languages selected"

        st.markdown(f"""
            <div class="target-card">
                <h3>DEMAND IN: {selected_country}</h3>
                <div class="target-label">Filtered Source Languages ({len(final_langs)})</div>
                <div class="target-value">{lang_string}</div>
                <div class="target-label">Action</div>
                <div class="target-value">Translate the articles below to increase local language coverage.</div>
            </div>
            """, unsafe_allow_html=True)

    # Impact Metrics
    st.markdown("### Impact Metrics")
    m1, m2, m3 = st.columns(3)

    total_views = aggregated["Views"].sum() if not aggregated.empty else 0
    unique_items = len(aggregated)
    avg_impact = aggregated["Views"].mean() if unique_items > 0 else 0

    m1.metric(
        "Articles to Translate",
        f"{unique_items:,}",
        help="The number of unique articles identified as high-demand for this selection."
    )
    m2.metric(
        "Total Number of Views",
        f"{int(total_views):,}",
        help="The total number of views from readers in the chosen country currently accessing this content in a non-native language."
    )
    m3.metric(
        "Avg Views per Article",
        f"{int(avg_impact):,}",
        help="Average number of pageviews of the article in the category chosen."
    )

    st.divider()

    # 8. Results Table
    st.markdown(f"### Articles Recommended for Translation: {selected_country}")

    if not aggregated.empty:
        st.dataframe(
            aggregated[["Page_Title", "Views", "Language_Name", "wiki_url"]],
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "Page_Title": st.column_config.TextColumn("Article Title"),
                "Language_Name": st.column_config.TextColumn("Source Language"),
                "wiki_url": st.column_config.LinkColumn("Read Original", display_text="Open Article"),
                "Views": st.column_config.ProgressColumn(
                    "Number of Views",
                    format="%d",
                    min_value=0,
                    max_value=int(aggregated["Views"].max()) if not aggregated.empty else 100
                )
            }
        )
    else:
        st.info("Adjust filters to view article recommendations.")

else:
    st.error("Data could not be loaded. Please ensure data files are present in the data folder.")


















































# import streamlit as st
# import pandas as pd
# import zipfile
# import json
# import os
# import codecs
# from urllib.parse import unquote, quote

# # 1. Page Configuration
# st.set_page_config(
#     page_title="WikiProject Africa | Translation Tool",
#     page_icon="🌍",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # 2. Custom Styling
# st.markdown("""
#     <style>
#     [data-testid="stMainViewContainer"] > section > div {
#         max-width: 1200px;
#         margin-left: auto;
#         margin-right: auto;
#         padding-top: 2rem;
#     }
#     [data-testid="stMetricValue"] {
#         font-size: 28px !important;
#         font-weight: 700 !important;
#         color: #007BFF;
#     }
#     [data-testid="stMetric"] {
#         background-color: #ffffff;
#         padding: 15px;
#         border-radius: 10px;
#         border: 1px solid #e5e7eb;
#     }
#     .target-card {
#         background: linear-gradient(135deg, #1D3557 0%, #457B9D 100%);
#         color: white;
#         padding: 20px;
#         border-radius: 12px;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#         min-height: 180px;
#         display: flex;
#         flex-direction: column;
#         justify-content: center;
#     }
#     .target-card h3 {
#         color: white !important;
#         margin: 0 0 10px 0;
#         font-size: 1.1rem;
#         border-bottom: 1px solid rgba(255,255,255,0.2);
#         padding-bottom: 8px;
#     }
#     .target-label {
#         font-weight: bold;
#         text-transform: uppercase;
#         font-size: 0.7rem;
#         color: #A8DADC;
#         margin-top: 10px;
#     }
#     .target-value {
#         font-size: 0.9rem;
#         line-height: 1.4;
#     }
#     </style>
#     """, unsafe_allow_html=True)

# # 3. Helpers
# def normalize_text(x):
#     return str(x).strip().lower()


# def fix_mojibake(text):
#     """
#     Repairs common UTF-8 mojibake such as:
#     'CÃ´te d'Ivoire' -> 'Côte d'Ivoire'
#     'MÃ©morial' -> 'Mémorial'
#     """
#     if not isinstance(text, str):
#         text = str(text)

#     original = text

#     # Try common bad decodings
#     for enc in ("latin1", "cp1252"):
#         try:
#             repaired = text.encode(enc).decode("utf-8")
#             text = repaired
#             break
#         except Exception:
#             continue

#     # If repair made things worse somehow, fall back
#     if not text:
#         return original
#     return text


# def decode_title(val):
#     """
#     Makes article titles readable by:
#     - fixing UTF-8 mojibake like AlgÃ©rie -> Algérie
#     - decoding unicode escape sequences like \\u00e9
#     - decoding percent-encoding if present
#     - replacing underscores with spaces
#     """
#     try:
#         text = str(val)

#         # 1. Decode percent-encoding first if present
#         text = unquote(text)

#         # 2. Fix mojibake
#         text = fix_mojibake(text)

#         # 3. Decode literal unicode escapes only when they are present
#         if "\\u" in text or "\\x" in text:
#             try:
#                 text = codecs.decode(text, "unicode_escape")
#             except Exception:
#                 pass

#         # 4. Clean up formatting
#         text = text.replace("_", " ").strip()

#         return text
#     except Exception:
#         return str(val).replace("_", " ").strip()


# def make_url_title(title):
#     """
#     Converts a readable article title into a Wikipedia-safe URL title.
#     Keeps accents correctly and URL-encodes them properly.
#     """
#     title = str(title).strip().replace(" ", "_")
#     return quote(title, safe=":/()_'-")


# # 4. Data Loading Functions
# @st.cache_data
# def load_mapping():
#     mapping_path = "data/language_mapping.json"
#     try:
#         if os.path.exists(mapping_path):
#             with open(mapping_path, "r", encoding="utf-8") as f:
#                 return json.load(f)
#     except Exception as e:
#         st.error(f"Error loading language mapping: {e}")
#     return {}


# @st.cache_data
# def load_data():
#     zip_path = "data/african_countries_dpdp_views.zip"
#     try:
#         with zipfile.ZipFile(zip_path, "r") as zf:
#             csv_files = [f for f in zf.namelist() if f.endswith(".csv")]
#             if not csv_files:
#                 return pd.DataFrame()

#             with zf.open(csv_files[0]) as f:
#                 df = pd.read_csv(f)

#                 if "Page_Title" in df.columns:
#                     df["Page_Title"] = df["Page_Title"].apply(decode_title)

#                 return df
#     except Exception as e:
#         st.error(f"Error loading data: {e}")
#         return pd.DataFrame()


# # Initialize data
# df = load_data()
# lang_map = load_mapping()

# # Support either:
# # {"en": "English", "fr": "French"}
# # or
# # {"English": "en", "French": "fr"}
# code_to_name = {}
# name_to_code = {}

# if lang_map:
#     sample_key = next(iter(lang_map.keys()))
#     sample_val = lang_map[sample_key]

#     # If keys look like language codes, assume code -> name
#     if len(str(sample_key).strip()) <= 5:
#         code_to_name = {
#             normalize_text(k): str(v).strip()
#             for k, v in lang_map.items()
#         }
#         name_to_code = {
#             normalize_text(v): str(k).strip()
#             for k, v in lang_map.items()
#         }
#     else:
#         # Otherwise assume name -> code
#         name_to_code = {
#             normalize_text(k): str(v).strip()
#             for k, v in lang_map.items()
#         }
#         code_to_name = {
#             normalize_text(v): str(k).strip()
#             for k, v in lang_map.items()
#         }


# def get_display_name(language_value):
#     """
#     Show readable language names in the UI.
#     If the raw value is already a name, keep it readable.
#     If it's a code, convert it to the full language name.
#     """
#     val = normalize_text(language_value)

#     if val in code_to_name:
#         return code_to_name[val]

#     if val in name_to_code:
#         return str(language_value).strip()

#     return str(language_value).strip()


# def resolve_language_code(language_value):
#     """
#     Returns the correct Wikipedia language code whether the raw value
#     is already a code or is a language name.
#     """
#     val = normalize_text(language_value)

#     # Already a language code
#     if val in code_to_name:
#         return val.lower()

#     # Language name -> code
#     if val in name_to_code:
#         return name_to_code[val].lower()

#     # Fallback: assume the raw value is already the code
#     return val.lower()


# def make_wiki_link(row):
#     """
#     Always create a standard Wikipedia article URL:
#     https://<lang>.wikipedia.org/wiki/<title>

#     This avoids accidental domains like nostalgia.wikipedia.org.
#     """
#     lang_code = resolve_language_code(row["language"])
#     url_title = make_url_title(row["Page_Title"])
#     return f"https://{lang_code}.wikipedia.org/wiki/{url_title}"


# if not df.empty:
#     # 5. Header Section
#     st.title("WikiProject Africa: Translation Tool")

#     st.markdown("""
#     ### About this Tool
#     This tool is designed to bridge the knowledge gap on Wikipedia across the African continent.
#     By analyzing traffic data, we identify articles that are frequently accessed in non-native languages
#     within specific countries.

#     **Our Objective:** To prioritize content for translation into local languages. By translating
#     high-traffic articles, we ensure that vital information is accessible to readers in the language
#     they understand best, increasing digital equity and local language representation online.
#     """)
#     st.divider()

#     # 6. Filters Section
#     col_filters, col_info = st.columns([1.5, 1], gap="large")

#     with col_filters:
#         st.markdown("### Filter Results")

#         countries = sorted(df["Country"].dropna().unique())
#         selected_country = st.selectbox("1. Select Target Country:", options=countries)

#         mask = (df["Country"] == selected_country) & (df["Native"] == "Non-Native")
#         translation_demand = df[mask].copy()

#         aggregated = (
#             translation_demand.groupby("Item_ID", as_index=False)
#             .agg({
#                 "Page_Title": "first",
#                 "language": "first",
#                 "Project": "first" if "Project" in translation_demand.columns else lambda x: None,
#                 "Views": "sum"
#             })
#             .sort_values(by="Views", ascending=False)
#         )

#         available_entries = sorted(aggregated["language"].dropna().unique())
#         entry_to_display = {
#             entry: get_display_name(entry)
#             for entry in available_entries
#         }

#         selected_displays = st.multiselect(
#             "2. Filter by Source Language:",
#             options=list(entry_to_display.values()),
#             default=list(entry_to_display.values())
#         )

#         selected_raw_values = [
#             raw_value for raw_value, display_value in entry_to_display.items()
#             if display_value in selected_displays
#         ]

#         if selected_raw_values:
#             aggregated = aggregated[aggregated["language"].isin(selected_raw_values)].copy()
#             aggregated["Language_Name"] = aggregated["language"].apply(get_display_name)
#         else:
#             st.warning("Please select at least one language.")
#             aggregated = pd.DataFrame(columns=[
#                 "Item_ID", "Page_Title", "language", "Project", "Views", "Language_Name"
#             ])

#         if not aggregated.empty:
#             aggregated["wiki_url"] = aggregated.apply(make_wiki_link, axis=1)

#     with col_info:
#         final_langs = sorted(aggregated["Language_Name"].unique()) if not aggregated.empty else []
#         lang_string = ", ".join(final_langs) if final_langs else "No languages selected"

#         st.markdown(f"""
#             <div class="target-card">
#                 <h3>DEMAND IN: {selected_country}</h3>
#                 <div class="target-label">Filtered Source Languages ({len(final_langs)})</div>
#                 <div class="target-value">{lang_string}</div>
#                 <div class="target-label">Action</div>
#                 <div class="target-value">Translate the articles below to increase local language coverage.</div>
#             </div>
#             """, unsafe_allow_html=True)

#     # 7. Impact Metrics
#     st.markdown("### Impact Metrics")
#     m1, m2, m3 = st.columns(3)

#     total_views = aggregated["Views"].sum() if not aggregated.empty else 0
#     unique_items = len(aggregated)
#     avg_impact = aggregated["Views"].mean() if unique_items > 0 else 0

#     m1.metric(
#         "Articles to Translate",
#         f"{unique_items:,}",
#         help="The number of unique articles identified as high-demand for this selection."
#     )
#     m2.metric(
#         "Total Potential Reach",
#         f"{int(total_views):,}",
#         help="The total number of views from readers currently accessing this content in a non-native language."
#     )
#     m3.metric(
#         "Avg Views per Article",
#         f"{int(avg_impact):,}",
#         help="Average impact score per translation effort."
#     )

#     st.divider()

#     # 8. Results Table
#     st.markdown(f"### Articles Recommended for Translation: {selected_country}")

#     if not aggregated.empty:
#         st.dataframe(
#             aggregated[["Page_Title", "Views", "Language_Name", "wiki_url"]],
#             use_container_width=True,
#             hide_index=True,
#             height=500,
#             column_config={
#                 "Page_Title": st.column_config.TextColumn("Article Title"),
#                 "Language_Name": st.column_config.TextColumn("Source Language"),
#                 "wiki_url": st.column_config.LinkColumn("Read Original", display_text="View Article"),
#                 "Views": st.column_config.ProgressColumn(
#                     "Reader Demand (Views)",
#                     format="%d",
#                     min_value=0,
#                     max_value=int(aggregated["Views"].max()) if not aggregated.empty else 100
#                 )
#             }
#         )
#     else:
#         st.info("Adjust filters to view article recommendations.")

# else:
#     st.error("Data could not be loaded. Please ensure data files are present in the data folder.")