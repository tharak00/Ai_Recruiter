import fitz  # PyMuPDF
import docx

def extract_text_from_pdf(file):
    file_bytes = file.read()  
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in pdf:
        text += page.get_text("text")
    file.seek(0)  # Reset pointer so Streamlit can reuse it
    return text.strip()

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    file.seek(0)
    return text.strip()

def parse_resume(file):
    if file.name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif file.name.endswith(".docx"):
        return extract_text_from_docx(file)
    else:
        return ""
