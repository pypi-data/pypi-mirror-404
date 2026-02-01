import os
from typing import List, Dict
from dotenv import load_dotenv
from ragas.metrics.collections import (
    ContextRecall,
    ContextRelevance, 
    Faithfulness,AnswerRelevancy
)
from ragas.cache import DiskCacheBackend
from ragas.embeddings import embedding_factory
from ragas.metrics.collections.context_precision import ContextPrecisionWithoutReference
from ragas.llms import llm_factory
from ragas import SingleTurnSample
from openai import AsyncOpenAI

load_dotenv()
import logging
logger = logging.getLogger(__name__)








class SingleQueryRAGASEvaluator:
    def __init__(self):
        """Simple evaluator using specified RAGAS metric classes."""
        logger.info("🔄 Initializing RAGAS evaluator...")
        self._API_KEY = os.getenv("_API_KEY")
        self.LLM_MODEL = os.getenv("LLM_MODEL")
        self.LLM_BASE_URL= os.getenv("LLM_BASE_URL")
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER")
        self.LLM_MAX_TOKENS=int(os.getenv("LLM_MAX_TOKENS"),"16384")
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
        self.client1 = AsyncOpenAI(
                api_key=self._API_KEY,
                base_url=self.LLM_BASE_URL,
                
            )
        
        logger.info(f"🤖 LLM client initialized.")
        self.llm = llm_factory(model=self.LLM_MODEL,client=self.client1,provider=self.LLM_PROVIDER,adapter="auto",max_tokens=self.LLM_MAX_TOKENS )
        logger.info(f"🤖 LLM initialized for RAGAS evaluation.")

        self.embeddings = embedding_factory(
                "huggingface", 
                model=self.EMBEDDING_MODEL,
                cache=DiskCacheBackend(),
                trust_remote_code= True ,
                model_kwargs={
                    "device": "mps",
                    "trust_remote_code": True   # only if needed for very specific models
                }
                
            )
    async def ragas_evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str]
    ) -> Dict[str, float]:
        """
        Evaluate a *SINGLE* RAG response using specified RAGAS metrics.
        """
        # Create the RAGAS SingleTurnSample
        sample = SingleTurnSample(
            user_input=question,
            response=answer
        )

       
        try:
            context_precision_score = ContextPrecisionWithoutReference(llm=self.llm)
            context_recall_score = ContextRecall(llm=self.llm)
            context_revelance_score = ContextRelevance(llm=self.llm)
            faithfulness_score = Faithfulness(llm=self.llm)
            answer_relevancy_score = AnswerRelevancy(llm=self.llm,embeddings=self.embeddings)

            context_precisionscore = await context_precision_score.ascore(user_input=question,response=answer,retrieved_contexts=contexts)
            context_Recall = await context_recall_score.ascore(user_input=question,retrieved_contexts=contexts,reference=answer)
            context_Relevance = await context_revelance_score.ascore(user_input=question,retrieved_contexts=contexts)
            faithfullness = await faithfulness_score.ascore(user_input=question,response=answer,retrieved_contexts=contexts)
            answer_Relevancy = await answer_relevancy_score.ascore(user_input=question,response=answer)
            logger.info(f"this the are the actal values : \n {context_precisionscore} \n {context_Recall} \n {faithfullness} \n {answer_Relevancy} ")
            
            scores = {
                "context_precision": float(context_precisionscore.value),
                "context_recall": float(context_Recall.value),
                "context_relevance": float(context_Relevance.value),
                "faithfulness": float(faithfullness.value),
                "answer_relevancy": float(answer_Relevancy.value),
            }
            comments = []
        
            # Context Precision: 0.9999 ✅ PERFECT
            if scores["context_precision"] > 0.95:
                comments.append("🎯 Context Precision EXCELLENT - Retrieved most relevant chunks first")
            elif scores["context_precision"] > 0.8:
                comments.append("✅ Context Precision GOOD - Relevant chunks mostly prioritized")
            else:
                comments.append("⚠️  Context Precision LOW - Needs better retrieval ranking")
            
            # Context Recall: 1.0 ✅ PERFECT  
            if scores["context_recall"] == 1.0:
                comments.append("📚 Context Recall PERFECT - All needed info retrieved")
            elif scores["context_recall"] > 0.85:
                comments.append("✅ Context Recall STRONG - Good coverage of relevant info")
            else:
                comments.append("⚠️  Context Recall LOW - Missing some relevant content")
            
            # Context Relevance: 0.988 ✅ EXCELLENT
            if scores["context_relevance"] > 0.95:
                comments.append("✨ Context Relevance OUTSTANDING - Minimal noise in retrieved docs")
            elif scores["context_relevance"] > 0.85:
                comments.append("✅ Context Relevance EXCELLENT - Very little irrelevant content")
            else:
                comments.append("⚠️  Context Relevance NEEDS WORK - Too much noise")
            
            # Faithfulness: 0.798 ✅ GOOD (room for improvement)
            if scores["faithfulness"] > 0.9:
                comments.append("✅ Faithfulness EXCELLENT - Answer strictly follows retrieved facts")
            elif scores["faithfulness"] > 0.75:
                comments.append("⚠️  Faithfulness GOOD - Minor hallucinations possible")
            else:
                comments.append("🔴 Faithfulness POOR - Significant hallucination risk")
            
            # Answer Relevancy: ? (awaiting value)
            if scores["answer_relevancy"] > 0.9:
                comments.append("🎯 Answer Relevancy PERFECT - Answer directly addresses question")
            elif scores["answer_relevancy"] > 0.8:
                comments.append("✅ Answer Relevancy STRONG - Good question focus")
            else:
                comments.append("⚠️  Answer Relevancy LOW - Answer drifts off-topic")

            scores["comments"] = comments
            # result is an EvaluationResult obj — convert to dict
            return scores

        except Exception as e:
            return {"error": f"RAGAS evaluation failed: {e}"}
    
   