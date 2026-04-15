import streamlit as st
import os
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Page Configuration
st.set_page_config(page_title="AI RAG App", layout="wide")

st.title("📄 AI RAG Application")
st.header("💬 Ask Questions from Your PDFs")

# Initialize Session state
if "chunks" not in st.session_state:
    st.session_state.chunks = []

# 2. PDF Loading & Processing
def load_pdfs():
    documents = []
    data_path = "data"

    if not os.path.exists(data_path):
        st.error("❌ 'data' folder not found!")
        return []

    pdf_files = [f for f in os.listdir(data_path) if f.endswith(".pdf")]
    
    for file in pdf_files:
        loader = PyPDFLoader(os.path.join(data_path, file))
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_documents(documents)

# Load Button
if st.button("Load PDFs"):
    with st.spinner("Processing documents..."):
        chunks = load_pdfs()
        if chunks:
            st.session_state.chunks = chunks
            st.success(f"✅ Loaded {len(chunks)} chunks from your PDFs.")
        else:
            st.warning("No PDF files found.")

# 3. Search Input
user_question = st.text_input("Enter your question:", placeholder="e.g., What is the average value?")

# 4. Answer Logic
if st.button("Get Answer"):
    if not user_question:
        st.warning("Please enter a question.")
    elif not st.session_state.chunks:
        st.error("Please load the PDFs first.")
    else:
        query = user_question.lower()
        results = []

        # --- 🔥 AGGREGATED: TOTAL & COUNT ---
        if any(keyword in query for keyword in ["total purchase", "count", "how many"]):
            unique_pos = set(os.path.basename(chunk.metadata['source']) for chunk in st.session_state.chunks)
            st.success(f"📊 Total Purchase Orders: {len(unique_pos)}")
            st.write("Documents: " + ", ".join(unique_pos))

        # --- 🔥 AGGREGATED: AVERAGE VALUE ---
        elif "average" in query:
            all_values = []
            # This pattern looks for currency amounts like 26,224.00 or 7,380.00
            value_pattern = r"(?:Total|Cost|MRC|Amount).*?([\d,]+\.\d{2})"
            
            for chunk in st.session_state.chunks:
                matches = re.findall(value_pattern, chunk.page_content, re.IGNORECASE)
                for m in matches:
                    # Remove commas and convert to float
                    clean_val = float(m.replace(",", ""))
                    all_values.append(clean_val)
            
            if all_values:
                # Use set to avoid counting the same value multiple times from different chunks
                unique_values = list(set(all_values))
                avg_val = sum(unique_values) / len(unique_values)
                st.success(f"📊 Average Value: {avg_val:,.2f} INR")
                st.write(f"Calculated from {len(unique_values)} unique values found.")
            else:
                st.warning("No numerical values found to calculate average.")

        # --- 🔥 NON-AGGREGATED: SPECIFIC FACTS ---
        else:
            # GST Number
            if "gst" in query:
                pattern = r"GSTIN:?\s*([0-9A-Z]{15})"
                for chunk in st.session_state.chunks:
                    matches = re.findall(pattern, chunk.page_content)
                    for m in matches:
                        results.append(f"✅ GSTIN: **{m}** ({os.path.basename(chunk.metadata['source'])})")

            # PO Number
            elif "number" in query:
                pattern = r"(?:PO No|Ref\. No|Order No|Lr\. No):?\s*([A-Z0-9/\-\.]+)"
                for chunk in st.session_state.chunks:
                    matches = re.findall(pattern, chunk.page_content, re.IGNORECASE)
                    for m in matches:
                        results.append(f"🔢 PO Number: **{m}**")

            # Supplier
            elif any(keyword in query for keyword in ["supplier", "vendor", "who is"]):
                for chunk in st.session_state.chunks:
                    if "To" in chunk.page_content or "VENDOR" in chunk.page_content:
                        lines = chunk.page_content.split("\n")
                        for i, line in enumerate(lines):
                            if "to" == line.strip().lower() or "vendor" in line.upper():
                                if i + 1 < len(lines):
                                    results.append(f"🏢 Supplier: **{lines[i+1].strip()}**")
                                    break

            if results:
                st.subheader("Results found:")
                for r in list(set(results)):
                    st.write(r)
            else:
                st.warning("No specific answer found. Try 'GSTIN', 'Vendor', or 'Average'.")
