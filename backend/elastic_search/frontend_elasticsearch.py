import streamlit as st
from query_engine_elasticsearch import search_documents

# Streamlit UI
st.set_page_config(page_title="🔍 Contract Search Engine", layout="wide")

st.title("🔍 Contract Search Engine")

query = st.text_input("Enter search query:")

if st.button("Search"):
    if query:
        results = search_documents(query)

        if results:
            for res in results:
                st.write(f"📄 **File:** {res['file_name']} (Chunk {res['chunk_id']})")
                st.markdown(f"🔎 **Snippet:** {res['highlight']}", unsafe_allow_html=True)
                st.write("---")
        else:
            st.warning("No results found!")
