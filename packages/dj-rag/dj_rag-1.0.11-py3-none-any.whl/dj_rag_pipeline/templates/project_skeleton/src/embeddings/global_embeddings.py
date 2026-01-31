# src/embeddings/global_embeddings.py
import logging
from typing import Optional
import asyncio
import torch
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class GlobalEmbeddings:
    """Singleton cache for embeddings - loads ONCE forever."""
    
    _instance: Optional['GlobalEmbeddings'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize instance variables (only once)."""
        if not self._initialized:
            self.model_name: Optional[str] = None
            self.embeddings: Optional[HuggingFaceEmbeddings] = None
            self.device: Optional[str] = None
            self._initialized = True
    
    async def get_embeddings(
        self, 
        model_name: str,
        force_reload: bool = False
    ) -> HuggingFaceEmbeddings:
        """
        Get cached embeddings or create new ones.
        
        Args:
            model_name: HuggingFace model identifier
            force_reload: Force reload even if cached
            
        Returns:
            Loaded embeddings model
            
        Raises:
            RuntimeError: If model loading fails
        """
        # Fast path: already cached and same model
        if (
            not force_reload 
            and self.embeddings is not None 
            and self.model_name == model_name
        ):
            logger.info("⚡ Using cached embeddings (instant)")
            return self.embeddings
        
        # Slow path: load model (with lock to prevent concurrent loads)
        async with self._lock:
            # Double-check after acquiring lock
            if (
                not force_reload 
                and self.embeddings is not None 
                and self.model_name == model_name
            ):
                logger.info("⚡ Using cached embeddings (waited for lock)")
                return self.embeddings
            
            try:
                logger.info(f"🔄 Loading embeddings: {model_name} (one-time)")
                
                # Detect device
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"📍 Using device: {device}")
                
                # Load embeddings (runs in executor to avoid blocking event loop)
                embeddings = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._load_embeddings_sync,
                    model_name,
                    device
                )
                
                # Cache globally
                self.model_name = model_name
                self.embeddings = embeddings
                self.device = device
                
                logger.info("✅ Embeddings cached globally!")
                return embeddings
                
            except Exception as e:
                logger.error(f"❌ Failed to load embeddings: {e}", exc_info=True)
                raise RuntimeError(f"Embedding load failed for {model_name}") from e
    
    def _load_embeddings_sync(
        self, 
        model_name: str, 
        device: str
    ) -> HuggingFaceEmbeddings:
        """Synchronous embedding loading (run in thread pool)."""
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device, "trust_remote_code": True},
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": 32,
            }
        )
    
    def clear_cache(self) -> None:
        """Clear cached embeddings to free memory."""
        logger.info("🧹 Clearing embeddings cache")
        self.model_name = None
        self.embeddings = None
        self.device = None
        
        # Force garbage collection
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def is_loaded(self, model_name: Optional[str] = None) -> bool:
        """Check if embeddings are loaded (optionally for specific model)."""
        if model_name:
            return self.embeddings is not None and self.model_name == model_name
        return self.embeddings is not None


# Global singleton instance (only way to access)
embeddings_manager = GlobalEmbeddings()