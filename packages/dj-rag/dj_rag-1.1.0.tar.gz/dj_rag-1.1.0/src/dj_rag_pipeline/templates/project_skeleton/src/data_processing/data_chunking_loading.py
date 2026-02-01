import os
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import MarkdownHeaderTextSplitter,RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
load_dotenv()

import logging
logger = logging.getLogger(__name__)




def ingest_to_pinecone_(md_folder: str = "src/data/markdown_data_sources"):

    PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
    INDEX_NAME=os.getenv("INDEX_NAME")
    EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL") 
    MAX_CHUNK_SIZE=int(os.getenv("MAX_CHUNK_SIZE"))
    CHUNK_OVERLAP=os.getenv("CHUNK_OVERLAP",400)
    
    logger.info(f"🧠 Loading HUGGING FACE model: {EMBEDDING_MODEL}...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu", "trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 32}
    )
    
    test_embed = embeddings.embed_query("test")
    dimension = len(test_embed)
    logger.info(f"📏 Embedding dimension: {dimension}")
    
    # ✅ 1. CHECK EXISTING PINECCONE INDEX FIRST
    logger.info("🔍 Checking existing Pinecone index...")
    from src.data_processing.check_pincone_index import list_indexed_files
    existing_files = list_indexed_files(INDEX_NAME)
    logger.info(f"📊 Currently indexed: {len(existing_files)} files, {sum(existing_files.values())} vectors")
    
    # 2. Setup chunking
    headers_to_split_on = [("#", "H1"), ("##", "H2"), ("###", "H3")]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
        length_function=len, separators=["\n\n", "\n", " ", ""]
    )
    
    # ✅ 3. ONLY NEW VECTORS
    new_vectors = []
    md_files = list(Path(md_folder).glob("*.md"))
    
    if not md_files:
        return "⚠️ No markdown files found"
    
    # ✅ 4. PROCESS ONLY NEW/MISSING FILES
    for md_file in md_files:
        file_name = md_file.name
        
        # ✅ SKIP if already in Pinecone!
        if file_name in existing_files:
            logger.info(f"⏭️ Skipping existing: {file_name} ({existing_files[file_name]} chunks)")
            continue
        
        logger.info(f"📄 Processing NEW file: {file_name}")
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                header_docs = markdown_splitter.split_text(f.read())
            
            final_chunks = []
            for doc in header_docs:
                if len(doc.page_content) > MAX_CHUNK_SIZE:
                    sub_chunks = text_splitter.split_text(doc.page_content)
                    for chunk in sub_chunks:
                        final_chunks.append({"content": chunk, "metadata": doc.metadata})
                else:
                    final_chunks.append({"content": doc.page_content, "metadata": doc.metadata})
            
            # ✅ NO UUIDs - Deterministic IDs
            for i, chunk_data in enumerate(final_chunks):
                try:
                    embedding = embeddings.embed_query(chunk_data["content"])
                    metadata = chunk_data["metadata"].copy()
                    metadata["text"] = chunk_data["content"]
                    metadata["source"] = file_name
                    metadata["chunk_index"] = i
                    
                    # ✅ FIXED ID: filename_chunkindex
                    new_vectors.append({
                        "id": f"{file_name.replace('.md', '')}_{i}",
                        "values": embedding,
                        "metadata": metadata
                    })
                except Exception as e:
                    logger.info(f"   ⚠️ Skip chunk {i}: {e}")
                    continue
        
        except Exception as e:
            logger.info(f"❌ Error processing {file_name}: {e}")
            continue
    
    if not new_vectors:
        logger.info("✨ No new files - index up to date!")
        return "✨ No new vectors to upload"
    
    # 5. Upsert ONLY new vectors
    logger.info(f"🔌 Connecting to Pinecone...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if INDEX_NAME not in pc.list_indexes().names():
        logger.info(f"🏗️ Creating index '{INDEX_NAME}'")
        pc.create_index(name=INDEX_NAME, dimension=dimension, metric="cosine",
                       spec=ServerlessSpec(cloud="aws", region="us-east-1"))
    
    index = pc.Index(INDEX_NAME)
    logger.info(f"🚀 Upserting {len(new_vectors)} NEW vectors...")
    
    for i in range(0, len(new_vectors), 100):
        batch = new_vectors[i:i + 100]
        index.upsert(vectors=batch)
        logger.info(f"   ✓ Batch {i//100 + 1}/{len(new_vectors)//100 + 1}")
    
    logger.info(f"✨ Added {len(new_vectors)} new vectors!")
    return f"✨ Added {len(new_vectors)} new vectors"

