import os
import fitz  # PyMuPDF
import re
import spacy

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Paths
RAW_FOLDER = "raw-files"
PROCESSED_FOLDER = "processed-files-vector"

os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return text

def preprocess_text(text):
    """Cleans and preprocesses text."""
    text = text.lower()  # Lowercasing
    text = re.sub(r'\W+', ' ', text)  # Remove special characters
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc if not token.is_stop])  # Lemmatization & Stopword Removal

def chunk_text(text, chunk_size=512):
    """Splits text into fixed-size chunks."""
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def process_pdfs():
    """Processes all PDFs in 'raw-files' and saves processed text chunks."""
    for pdf_file in os.listdir(RAW_FOLDER):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(RAW_FOLDER, pdf_file)
            print(f"Processing {pdf_file}...")

            text = extract_text_from_pdf(pdf_path)
            cleaned_text = preprocess_text(text)
            chunks = chunk_text(cleaned_text)

            # Save processed chunks as text files
            txt_filename = pdf_file.replace(".pdf", ".txt")
            txt_path = os.path.join(PROCESSED_FOLDER, txt_filename)

            with open(txt_path, "w", encoding="utf-8") as f:
                for chunk in chunks:
                    f.write(chunk + "\n\n")

            print(f"✔ Processed: {pdf_file} ({len(chunks)} chunks)")

# Run preprocessing
process_pdfs()
