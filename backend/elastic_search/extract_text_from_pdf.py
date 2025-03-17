#AUTHOR - RAJ MEHTA

import os
import fitz  # PyMuPDF for PDF text extraction
import re
import spacy
import json

# Load spaCy NLP model (download if missing)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Folder Paths
RAW_FOLDER = "raw-files"
PROCESSED_FOLDER = "processed-files"

# Ensure processed-files directory exists
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return text

def preprocess_text(text):
    """Preprocess text: lowercase, remove special characters, stopwords, and lemmatization."""
    text = text.lower()  # Lowercasing
    text = re.sub(r'\W+', ' ', text)  # Remove special characters
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc if not token.is_stop])  # Lemmatization & Stopword Removal

def chunk_text(text, chunk_size=512):
    """Split text into fixed-size chunks."""
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def process_pdfs():
    """Process all PDFs from 'raw-files', save processed text chunks as JSON in 'processed-files'."""
    for pdf_file in os.listdir(RAW_FOLDER):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(RAW_FOLDER, pdf_file)
            print(f"Processing {pdf_file}...")

            # Extract and preprocess text
            text = extract_text_from_pdf(pdf_path)
            cleaned_text = preprocess_text(text)
            chunks = chunk_text(cleaned_text)

            # Save processed chunks as JSON file
            processed_data = [{"file_name": pdf_file, "chunk_id": i, "text": chunk} for i, chunk in enumerate(chunks)]
            json_filename = pdf_file.replace(".pdf", ".json")
            json_path = os.path.join(PROCESSED_FOLDER, json_filename)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, indent=4)

            print(f"✔ Processed and saved: {json_filename} ({len(chunks)} chunks)")

# Run the processing
process_pdfs()
print("✅ All PDFs processed and saved successfully!")
