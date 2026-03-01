import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Optional
from docling.document_converter import DocumentConverter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from src.llm_factory import get_llm

# Cache for RAG objects to avoid redundant processing
_rag_cache = {}

def get_rag(pdf_path: str) -> Optional['DocumentRAG']:
    """Helper to get or create a RAG object for a PDF. Synchronous."""
    if pdf_path in _rag_cache:
        return _rag_cache[pdf_path]
        
    if not Path(pdf_path).exists():
        return None
        
    print(f"Initializing RAG for {pdf_path}...")
    converter = DocumentConverter()
    try:
        result = converter.convert(pdf_path)
        markdown = result.document.export_to_markdown()
        _rag_cache[pdf_path] = DocumentRAG(markdown)
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return None
    return _rag_cache[pdf_path]

@tool
def query_pdf_report(pdf_path: str, question: str) -> str:
    """
    Queries a PDF report using RAG. Use this to find specialized architectural 
    explanations or mentioned features in the documentation.
    """
    rag = get_rag(pdf_path)
    if not rag:
        return f"Error: Could not process PDF at {pdf_path}"
    return rag.query(question)

@tool
def extract_paths_from_pdf(pdf_path: str) -> str:
    """
    Extracts all mentioned file paths from a PDF report. 
    Returns them as a comma-separated list.
    """
    rag = get_rag(pdf_path)
    if not rag:
        return f"Error: Could not process PDF at {pdf_path}"
    
    # We'll use the existing extract_file_paths logic but adapted for a tool
    text = rag.document_text[:8000] # Use a larger chunk for path extraction
    llm = get_llm()
    prompt = f"""
    You are a forensic document analyst. Extract all unique file paths mentioned in the following text.
    Return ONLY a valid Python list of strings. No explanation.
    
    Text: {text}
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if "```" in content:
            content = re.sub(r"```(python)?", "", content).strip("`").strip()
        paths = ast.literal_eval(content)
        result = ", ".join(paths) if isinstance(paths, list) else "None found."
        if len(result) > 4000:
            return result[:4000] + "\n... [TRUNCATED FOR CONTEXT SAFETY] ..."
        return result
    except Exception as e:
        return f"Error extracting paths: {str(e)}"

class DocumentRAG:
    """RAG system for a single document with flexible LLM and local embeddings."""
    def __init__(self, document_text: str):
        self.document_text = document_text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.create_documents([document_text])
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = InMemoryVectorStore.from_documents(docs, embeddings)
        self.llm = get_llm()

    def query(self, question: str) -> str:
        """Queries the document using RAG."""
        relevant_docs = self.vectorstore.similarity_search(question, k=5)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        prompt = ChatPromptTemplate.from_template("""
        You are a forensic document analyst. Answer the question based ONLY on the provided context.
        Context: {context}
        Question: {question}
        """)
        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": question})
        return response.content
