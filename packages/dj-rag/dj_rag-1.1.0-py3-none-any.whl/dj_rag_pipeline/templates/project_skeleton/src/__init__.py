"""
🎧 DJ's RAG Pipeline v1.0.0 - Production RAG Library!
pip install dj-rag → Instant RAG anywhere!

Quickstart:
    from dj_rag_pipeline import PineconeRetriever, RAGChatbot
    retriever = PineconeRetriever()
    chatbot = RAGChatbot()
"""

__version__ = "1.0.0"
__author__ = "DJ"

print("🎧 DJ's RAG Pipeline v1.0.0 for Python 3.13 loaded!")

# 🔥 Export key classes for easy import (users type LESS!)
from src.data_retriver.data_pinecone_retriver import PineconeRetriever
from src.llm.llm_file import RAGChatbot
from src.evaluation.ragas_evaluation import SingleQueryRAGASEvaluator
from src.data_processing.data_chunking_loading import ingest_to_pinecone_
from src.data.markdown_data_pipeline import convert_pdfs_to_md
from src.data_processing.check_pincone_index import list_indexed_files

__all__ = [
    "PineconeRetriever",
    "RAGChatbot", 
    "SingleQueryRAGASEvaluator",
    "ingest_to_pinecone_",
    "convert_pdfs_to_md",
    "list_indexed_files",
]
