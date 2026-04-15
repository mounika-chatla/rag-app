import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Page config
st.set_page_config(page_title="AI RAG App", layout="wide")

st.title("📄 AI RAG Application")
st.header("💬 Ask Questions from Your PDFs")

# Session state
if "chunks" not in st.session_state:
    st.session_state.chunks = []

# Load PDFs function
def load_pdfs():
    documents = []
    data_path = "data"

    if not os.path.exists(data_path):
        st.error("❌ 'data' folder not found!")
        return []

    for file in os.listdir(data_path):
        if file.endswith(".pdf"):
            file_path = os.path.join(data_path, file)
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())

    # Text splitting
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    return text_splitter.split_documents(documents)

# Load PDFs button
if st.button("Load PDFs"):
    chunks = load_pdfs()
    if chunks:
        st.session_state.chunks = chunks
        st.success(f"✅ {len(chunks)} chunks created from PDFs!")
    else:
        st.warning("⚠️ No PDFs found")

# Question input
user_question = st.text_input("Enter your question:")

# Get Answer
if st.button("Get Answer"):
    if user_question:
        if not st.session_state.chunks:
            st.error("❌ Please load PDFs first!")
        else:
            results = []

            # 🔥 SMART SEARCH (word-based)
            query_words = user_question.lower().split()

            for chunk in st.session_state.chunks:
                content = chunk.page_content.lower()

                if any(word in content for word in query_words):
                    results.append(chunk.page_content)

            st.subheader("📄 Answer:")

            if results:
                combined = " ".join(results[:3])

                # 🔥 Aggregated question detection
                if any(word in user_question.lower() for word in ["total", "count", "sum", "average"]):
                    st.success(f"📊 Aggregated Result: Found {len(results)} relevant records in documents.")
                else:
                    # 🔥 Short clean answer
                    short_answer = " ".join(combined.split("\n")[:3])
                    st.write(short_answer)
            else:
                st.warning("No relevant data found.")
    else:
        st.warning("Please enter a question.")
