# WikiProject Africa: Editorial Prioritization Tool

A Streamlit app that helps Wikipedia editors find high-traffic, low-quality articles within [WikiProject Africa](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Africa) worth improving, and articles worth translating into local languages.

**🔗 Live app: [editor-tool-wikiprojectafrica.streamlit.app](https://editor-tool-wikiprojectafrica.streamlit.app/)**

by Hadassah Mwazemba · Advised by Professor Eni Mustafaraj

## What it does

- **Article Improvement Tool** — filter articles by quality and importance class, benchmark them against median pageviews, and export a worklist of articles that are widely read but under-developed.
- **Translation Tool** — pick a country and see which articles readers there are accessing in a non-native language, ranked by demand.
- **Data Sources page** — documents where the underlying data comes from.

## Data Sources

- [Wikimedia Analytics — Country Project Page Datasets](https://analytics.wikimedia.org/published/datasets/country_project_page/)
- [WP1.0 OpenZIM — WikiProject Africa Articles](https://wp1.openzim.org/#/project/Africa/articles)

## Run it locally

1. git clone https://github.com/hadassahmwazemba/editor-tool-wikiproject.git
2. cd editor-tool-wikiproject
3. pip install streamlit pandas
4. streamlit run Welcome.py

