import streamlit as st

st.set_page_config(page_title="Data Sources & References", layout="wide")

st.title("Data Sources & Reference Information")
st.divider()

st.subheader("Data Sources")
st.write("The data used in this tool is aggregated from the following open datasets:")
st.markdown("""
* **Wikimedia Analytics (Pageviews):** [Country Project Page Datasets](https://analytics.wikimedia.org/published/datasets/country_project_page/) - Used to derive median monthly traffic.
* **WP1.0 OpenZIM:** [WikiProject Africa Articles](https://wp1.openzim.org/#/project/Africa/articles) - The primary source for the project list.
""")

st.divider()

st.subheader("Project References")
st.write("These resources define the scope and assessment standards for the project:")
st.markdown("""
* **WikiProject Africa:** [Main Project Page](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Africa)
* **Content Assessment:** [Wikipedia Assessment Scale](https://en.wikipedia.org/wiki/Wikipedia:Content_assessment)
""")

st.divider()

st.subheader("Contributor Guide")
st.write("New to editing? Use the link below to learn how to improve Wikipedia articles:")
st.write("**[Help: Introduction to Editing](https://en.wikipedia.org/wiki/Help:Editing)**")