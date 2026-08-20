import pdfplumber
from docx import Document
from typing import Optional
import io


class DocumentProcessor:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n\n".join(text_parts)
    
    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        doc = Document(io.BytesIO(file_bytes))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        return "\n\n".join(text_parts)
    
    @staticmethod
    def extract_text_from_txt(file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8")
    
    @classmethod
    def extract_text(cls, file_bytes: bytes, content_type: str) -> str:
        if content_type == "application/pdf":
            return cls.extract_text_from_pdf(file_bytes)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return cls.extract_text_from_docx(file_bytes)
        elif content_type == "text/plain":
            return cls.extract_text_from_txt(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {content_type}")
    
    @staticmethod
    def clean_text(text: str) -> str:
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)
        return "\n".join(cleaned_lines)