from fastapi import FastAPI ,File, UploadFile, HTTPException ,BackgroundTasks,status
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
# Your existing imports
from src.data.markdown_data_pipeline import convert_pdfs_to_md
from src.data_processing.data_chunking_loading import *
from src.data_retriver.data_pinecone_retriver import PineconeRetriever 
from src.llm.llm_file import RAGChatbot
from src.evaluation.ragas_evaluation import SingleQueryRAGASEvaluator
from src.data_processing.check_pincone_index import list_indexed_files
from src.embeddings.global_embeddings import embeddings_manager
import uuid
from contextlib import asynccontextmanager
import shutil
# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | [%(filename)s:%(lineno)d] | %(message)s",
)
logger = logging.getLogger(__name__)
# INDEX_NAME=os.getenv("INDEX_NAME")
# EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup logic ----
    logger.info("Starting up the RAG API...")
    await embeddings_manager.get_embeddings(os.getenv("EMBEDDING_MODEL"))

    yield  # 👈 app runs while paused here

    # ---- Shutdown logic ----
    logger.info("Shutting down the  RAG API...")
    scheduler.shutdown()

# FastAPI app
app = FastAPI(title="DJ RAG API", version="1.0.5",lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
scheduler = AsyncIOScheduler()


# Global instances


 
# Pydantic models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 7
    score_threshold: float = 0.7
    use_mmr: bool = True

class QueryResponse(BaseModel):
    answer: str
    retrieval_metrics: Dict[str, Any]
    ragas_scores: Dict[str, float]
    evaluation_summary: Dict[str, Any]
    sources: List[Dict[str, Any]]
    indexed_files: Dict[str, int]

class PDFUploadResponse(BaseModel):
    success: bool
    message: str
    uploaded_files: List[str]
    data_source_path: str
    processing_status: str
    indexed_files: Dict[str, int] = {}

class EvaluateRagasRequest(BaseModel):
    question: str
    answer: str
    contexts: List[str]

retriever = PineconeRetriever()
logger.info("Retriever initialized.")
chatbot = RAGChatbot()
logger.info("Chatbot initialized.")


@app.post("/chat", response_model=Dict[str, Any])
async def chat_with_evaluation(request: QueryRequest) -> Dict[str, Any]:
    """
    Route 1: User query → Retrieve → Generate → Evaluate (Full RAG pipeline)
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        
        # 1. Retrieve
        retrieved_docs, retrieval_metrics = await retriever.retrieve_with_hybrid_search(
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            use_mmr=request.use_mmr
        )
        logger.info(f"Retrieved {len(retrieved_docs)} documents.")
        if not retrieved_docs:
            logger.warning("No documents retrieved. Skipping generation.")

            return {
                "success": True,
                "data": {
                    "user_query": request.query,
                    "answer": "I'm not sure based on the provided information.",
                    "retrieval_metrics": retrieval_metrics,
                    "sources": retrieved_docs,
                    "context_for_evlauation": [],
                    "eval_endpoint": "/evaluate-ragas"
                }
            }
        # 2. Generate
        chat_result = await chatbot.chat(
            user_query=request.query,
            retrieved_docs=retrieved_docs,
            retrieval_metrics=retrieval_metrics
        )
        logger.info(f"Generated answer: {chat_result['answer'][:100]}...")
       
        contexts = [doc["text"] for doc in retrieved_docs]
          
        # Get indexed files info
        return {
            "success": True,
            "data": {
                "user_query" :request.query,
                "answer": chat_result["answer"],
                "retrieval_metrics": retrieval_metrics,
                "sources": retrieved_docs,
                "context_for_evlauation":contexts,
                "eval_endpoint": "/evaluate-ragas"
            }
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/evaluate-ragas")
async def evaluate_with_ragas(payload: EvaluateRagasRequest):
    try:
        evaluator = SingleQueryRAGASEvaluator()
        logger.info("Evaluator initialized.")

        logger.info("Starting RAGAS evaluation...")
        ragas_scores = await evaluator.ragas_evaluate(
            question=payload.question,
            answer=payload.answer,
            contexts=payload.contexts
        )
        logger.info("RAGAS evaluation completed.")

        return ragas_scores
    except Exception as e:
        logger.error(f"Ragas evaluation failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/index-status")
async def get_index_status() -> Dict[str, Any]:
    """
    Route 2: List all indexed files in Pinecone with chunk counts
    """
    try:
        logger.info("Fetching Pinecone index status...")
        indexed_files = list_indexed_files(os.getenv("INDEX_NAME"))
        
        return {
            "success": True,
            "data": {
                "total_vectors": sum(indexed_files.values()),
                "total_files": len(indexed_files),
                "indexed_files": indexed_files
            }
        }
        
    except Exception as e:
        logger.error(f"Index status error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/full-pipeline")
async def full_pipeline(
    files: List[UploadFile] = File(None, description="Optional: PDFs to upload first"),
):
    """
    Route 5: COMPLETE Pipeline - Upload PDFs → Convert → Ingest → Index
    Single endpoint for end-to-end processing
    """
    try:
        logger.info("🚀 Starting FULL RAG Pipeline...")
        
        # Step 1: Upload PDFs (if provided)
        if files:
            logger.info(f"📤 Uploading {len(files)} PDFs first...")
            # Call upload logic (reuse upload code or call upload endpoint internally)
            data_source_path = Path("src/data/data_source")
            data_source_path.mkdir(parents=True, exist_ok=True)
            
            uploaded_files = []
            for file in files:
                if file.filename.lower().endswith('.pdf'):
                    file_path = data_source_path / file.filename
                    with file_path.open("wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    uploaded_files.append(file.filename)
        
        # Step 2: Convert PDFs to Markdown
        logger.info("🔄 Converting PDFs to Markdown...")
        convert_pdfs_to_md()
        
        # Step 3: Ingest Markdown to Pinecone
        ingest_to_pinecone_()
        
        # Step 4: Final status
        indexed_files = list_indexed_files(os.getenv("INDEX_NAME"))
        
        return {
            "success": True,
            "message": "✅ FULL PIPELINE COMPLETED: PDFs → Markdown → Pinecone",
            "uploaded_files": uploaded_files if files else [],
            "indexed_files": indexed_files,
            "total_vectors": sum(indexed_files.values())
        }
        
    except Exception as e:
        logger.error(f"❌ Full pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_server():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)

def run_dev():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)