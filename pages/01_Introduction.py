import streamlit as st

st.set_page_config(page_title="Introduction", layout="wide", initial_sidebar_state="expanded")

# Title Section
st.title("WikiProject Africa: Editorial Prioritization Tool")

st.markdown("""
**by: Hadassah Mpare** \n
*Advised by: Professor Eni Mustafaraj*
""")

st.divider()

# Overview Section
st.header("A Brief Overview")

st.markdown("""
This tool is designed to support contributors to **WikiProject Africa** by identifying high-impact articles that would benefit most from editorial improvement.

Using median monthly pageview data, this app highlights articles that:
- Receive consistent reader attention  
- Fall within lower or mid-level quality classes  
- Are considered important within the WikiProject  

By focusing on these articles, editors can make meaningful contributions to improve both content quality and reader experience.
""")

st.divider()

# What is WikiProject Africa Section
st.header("What is WikiProject Africa?")

col1, col2 = st.columns([2, 1])  

with col1:
    st.markdown("""
    **WikiProject Africa** is a collaborative effort on Wikipedia aimed at improving the coverage of topics related to the African continent.

    This includes:
    - Historical events and figures  
    - Cultural and linguistic topics  
    - Geography, politics, and society  
    - Biographies of notable individuals  

    Despite its importance, many Africa-related articles remain underdeveloped or uneven in quality.
    """)

with col2:
    st.image("data/africa.jpg", width=300) 

    st.markdown(
        "[Visit WikiProject Africa](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Africa)"
    )

st.divider()

# How This Tool Works Section
st.header("How This Tool Works")

st.markdown("""
This application uses **median monthly pageviews** as a proxy for reader interest.

It:
1. Filters articles by **quality class** (e.g., Stub, Start, C-Class)  
2. Allows selection of **importance levels** (Top, High, Mid, Low)  
3. Calculates a **benchmark median traffic value** for the selected group  
4. Surfaces articles performing **at or above this benchmark** 

These articles represent strong candidates for editorial attention because they combine:
- High visibility  
- Lower quality ratings  
""")

st.divider()

#Why It Matters Section
st.header("Why This Matters")

st.markdown("""
Improving widely viewed articles has a multiplier effect:

- **More readers benefit** from better information  
- **African topics gain more accurate representation** - **Knowledge gaps are reduced** on a global platform  

Rather than editing randomly, this tool helps prioritize **data-driven contributions**.
""")

# Data Source Section 
st.header("Data Source")

st.markdown("""
The dataset used in this tool includes:
- Wikipedia articles from WikiProject Africa  
- Quality and importance ratings from the WikiProject  
- Monthly median pageviews  

These metrics are combined to identify where editorial effort can have the greatest impact.
""")

st.divider()

st.info("Navigate to the main tool using the sidebar to start building your editorial worklist.")