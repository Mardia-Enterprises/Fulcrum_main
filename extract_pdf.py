import PyPDF2
import sys

def extract_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = ''
        for page in reader.pages:
            full_text += page.extract_text()
        return full_text

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        text = extract_pdf_text(pdf_path)
        print(text[:5000])  # Print first 5000 chars
    else:
        print("Usage: python extract_pdf.py <pdf_path>") 