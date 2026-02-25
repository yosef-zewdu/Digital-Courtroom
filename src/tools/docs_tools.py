import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from docling.document_converter import DocumentConverter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.llm_factory import get_llm
import ast
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

def ingest_pdf(path: str) -> str:
    """Parses a PDF file and returns its content as Markdown text."""
    if not Path(path).exists():
        return ""
    try:
        converter = DocumentConverter()
        result = converter.convert(path)
        return result.document.export_to_markdown()
    except Exception as e:
        print(f"Error parsing PDF {path}: {e}")
        return ""

class DocumentRAG:
    """RAG system for a single document with flexible LLM and local embeddings."""
    def __init__(self, document_text: str):
        if not document_text:
            self.vectorstore = None
            return
            
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.create_documents([document_text])
        
        # Initialize Local Embeddings to avoid Gemini quota limits
        print("Initializing local HuggingFace embeddings...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Use InMemoryVectorStore from langchain-core
        self.vectorstore = InMemoryVectorStore.from_documents(docs, embeddings)
        
        # Load LLM from factory (defaults to OpenRouter if set in .env)
        self.llm = get_llm()

    def query(self, question: str) -> str:
        """Queries the document using RAG."""
        if not self.vectorstore:
            return "No document content available."
            
        relevant_docs = self.vectorstore.similarity_search(question, k=5)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        prompt = ChatPromptTemplate.from_template("""
        You are a forensic document analyst. Answer the question based ONLY on the provided context.
        If the information is not in the context, say "Information not found in report."
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:""")
        
        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": question})
        return response.content



def extract_file_paths(text: str) -> List[str]:
    """Extracts potential file paths from text using LLM and AST parsing."""
    if not text:
        return []

    llm = get_llm()
    prompt = f"""
    You are a forensic document analyst. Extract all unique file paths mentioned in the following text.
    Return ONLY a valid Python list of strings. No explanation, no markdown blocks.
    
    Example: ["src/graph.py", "src/state.py"]
    
    Text:
    {text[:4000]}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = re.sub(r"```(python)?", "", content).strip("`").strip()
            
        # Use ast.literal_eval for safe parsing of the list
        paths = ast.literal_eval(content)
        if isinstance(paths, list):
            return [str(p) for p in paths]
        return []
    except Exception as e:
        print(f"Error extracting paths with AST: {e}")
        # Fallback to empty list or basic regex if needed, but user asked for AST.
        return []
