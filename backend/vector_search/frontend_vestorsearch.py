import streamlit as st
from query_engine_vector_search import search_documents

# Set Streamlit page title
st.set_page_config(page_title="🔍 Vector-Based Semantic Contract Search", layout="wide")

st.title("🔍 Contract Search Engine")

query = st.text_input("Enter search query:")

if st.button("Search"):
    if query:
        results = search_documents(query)

        if results:
            for res in results:
                st.write(f"📄 **File:** {res['file_name']} (Chunk {res['chunk_id']})")
                st.markdown(f"🔎 **Snippet:** {res['text'][:300]}")
                st.write("---")
        else:
            st.warning("No results found!")
