import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from pinecone import Pinecone
from collections import Counter
from src.embeddings.global_embeddings import embeddings_manager
import time
import torch
from dotenv import load_dotenv
load_dotenv()
import asyncio
import logging
logger = logging.getLogger(__name__)







class PineconeRetriever:
    """
    Advanced retriever with hybrid search and built-in evaluation metrics.
    """
    
    def __init__(self,embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"):
    
        # Initialize Ollama embeddings
        logger.info(f"🧠 Initializing HuggingFace Embeddings with model: {embedding_model}...")
        self.PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
        self.PINECONE_INDEX_HOST=os.getenv("PINECONE_INDEX_HOST")
        self.EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL")

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            self.embedding_models = embedding_model

        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace embeddings: {e}")
            raise RuntimeError(
                "Could not load embedding model."
            )
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.PINECONE_API_KEY)
        self.index = self.pc.Index(host=self.PINECONE_INDEX_HOST)
        
        # Retrieval metrics storage
        self.metrics = {
            "queries": 0,
            "avg_latency": 0,
            "avg_score": 0,
            "source_diversity": []
        }
    
    
    
    async def retrieve_with_hybrid_search(
        self,
        query: str,
        top_k: int = 7,
        score_threshold: float = 0.7,
        metadata_filter: Dict = None,
        use_mmr: bool = False
    ) -> Tuple[List[Dict], Dict]:
        start_time = time.time()
        logging.info(f"🔍 Retrieving for query: {query[:100]}...")
        self.embeddings = await embeddings_manager.get_embeddings(self.EMBEDDING_MODEL)
        
        logger.info("✓ HuggingFace embeddings initialized successfully")
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        logging.info(" ✓ Generated query embedding.")

        initial_k = top_k * 3 if use_mmr else top_k

        search_params = {
            "vector": query_embedding,
            "top_k": initial_k,
            "include_metadata": True
        }

        if metadata_filter:
            search_params["filter"] = metadata_filter

        # results = await self.index.query(**search_params)

        results = self.index.query(**search_params)

        # Apply MMR if requested
        if use_mmr:
            results_mmr = await self._apply_mmr(
                query_embedding,
                results['matches'],
                top_k=top_k,
                lambda_param=0.7
            )
        else:
            results_mmr = results['matches'][:top_k]

        # Filter by score threshold
        filtered_results = [
            r for r in results_mmr
            if r['score'] >= score_threshold
        ]

        latency = time.time() - start_time
        eval_metrics = await self._calculate_metrics(filtered_results, latency, query)

        formatted_results = [
            {
                "text": r['metadata'].get('text', ''),
                "source": r['metadata'].get('source', 'Unknown'),
                "headers": {k: v for k, v in r['metadata'].items() if k.startswith('H')},
                "score": r['score'],
                
            }
            for r in filtered_results
        ]

        logging.info(f" ✓ Retrieved {len(formatted_results)} results in {latency:.2f}s.")
        return formatted_results, eval_metrics
    
    async def _apply_mmr(
        self,
        query_embedding: List[float],
        candidates: List[Dict],
        top_k: int,
        lambda_param: float = 0.7
    ) -> List[Dict]:
        """
        Maximal Marginal Relevance for diverse results.
        """
        selected = []
        remaining = candidates.copy()
        
        while len(selected) < top_k and remaining:
            if not selected:
                # First selection: highest similarity
                selected.append(remaining.pop(0))
                continue
            
            # Calculate MMR scores
            mmr_scores = []
            for candidate in remaining:
                relevance = candidate['score']
                similarities = await asyncio.gather(*[
                    self._cosine_similarity(candidate['values'], s['values'])
                    for s in selected
                ])
                max_similarity = max(similarities)
                
                mmr_score = (
                    lambda_param * relevance -
                    (1 - lambda_param) * max_similarity
                )
                mmr_scores.append((mmr_score, candidate))
            
            # Select candidate with highest MMR score
            best = max(mmr_scores, key=lambda x: x[0])
            selected.append(best[1])
            remaining.remove(best[1])
        
        return selected
    
    async def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        return dot_product / (magnitude1 * magnitude2) if magnitude1 and magnitude2 else 0
    
    async def _calculate_metrics(
        self,
        results: List[Dict],
        latency: float,
        query: str
    ) -> Dict:
        """
        Calculate evaluation metrics for retrieval quality.
        """
        if not results:
            return {
                "precision_at_k": 0.0,
                "avg_score": 0.0,
                "source_diversity": 0.0,
                "latency_ms": latency * 1000,
                "num_results": 0,
                "coverage": 0.0
            }
        
        # Extract metrics
        scores = [r['score'] for r in results]
        sources = [r['metadata'].get('source') for r in results]
        unique_sources = len(set(sources))
        
        # Precision@K (assuming scores > 0.8 are relevant)
        relevant_threshold = 0.8
        relevant_count = sum(1 for s in scores if s >= relevant_threshold)
        precision_at_k = relevant_count / len(results)
        
        # Source diversity (Shannon entropy)
        source_counts = Counter(sources)
        total = len(sources)
        entropy = -sum(
            (count/total) * (count/total)**0.5 
            for count in source_counts.values()
        )
        
        metrics = {
            "precision_at_k": round(precision_at_k, 3),
            "recall_estimate": round(min(len(results) / 10, 1.0), 3),
            "avg_score": round(sum(scores) / len(scores), 3),
            "min_score": round(min(scores), 3),
            "max_score": round(max(scores), 3),
            "source_diversity": round(unique_sources / len(results), 3),
            "unique_sources": unique_sources,
            "latency_ms": round(latency * 1000, 2),
            "num_results": len(results),
            "coverage_score": round(entropy, 3)
        }
        
        # Update running metrics
        self.metrics["queries"] += 1
        self.metrics["avg_latency"] = (
            (self.metrics["avg_latency"] * (self.metrics["queries"] - 1) + latency)
            / self.metrics["queries"]
        )
        
        return metrics
    
    



# # Usage Example
# if __name__ == "__main__":
#     retriever = PineconeRetriever()
    
#     # Example query
#     query = "What are beginner yoga poses for flexibility?"
    
#     results, metrics = retriever.retrieve_with_hybrid_search(
#         query=query,
#         top_k=5,
#         score_threshold=0.75,
#         use_mmr=True  # Use MMR for diverse results
#     )
    
#     print(f"📊 Evaluation Metrics:")
#     print(f"  Precision@K: {metrics['precision_at_k']}")
#     print(f"  Avg Score: {metrics['avg_score']}")
#     print(f"  Source Diversity: {metrics['source_diversity']}")
#     print(f"  Latency: {metrics['latency_ms']}ms")
#     print(f"  Results: {metrics['num_results']}\n")
    
#     print(f"📚 Top Results:")
#     for i, result in enumerate(results, 1):
#         print(f"{i}. [{result['source']}] Score: {result['score']:.3f}")
#         print(f"   {result['text']}\n")
