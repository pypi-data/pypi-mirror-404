from pinecone import Pinecone
from collections import Counter
from dotenv import load_dotenv
import os
load_dotenv()

def list_indexed_files(index_name: str, embedding_dimension: int = 768):
    """
    Lists all source files indexed in Pinecone with chunk counts.
    
    Args:
        index_name: Name of the Pinecone index
        embedding_dimension: Dimension of your embeddings (default: 768 for nomic-embed-text)
    
    Returns:
        dict: Dictionary with source filenames as keys and chunk counts as values
    """
    
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY key not found in environment variables")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index(index_name)
    
    # Get index stats
    stats = index.describe_index_stats()
    print(f"📊 Total vectors in index: {stats['total_vector_count']}")
    print(f"📏 Dimension: {stats['dimension']}\n")
    
    # Query with high topK to get all vectors
    dummy_vector = [0.0] * embedding_dimension
    
    results = index.query(
        vector=dummy_vector,
        top_k=10000,  # Higher than your total vector count
        include_metadata=True
    )
    
    # Extract all unique source files
    sources = []
    for match in results['matches']:
        if 'source' in match['metadata']:
            sources.append(match['metadata']['source'])
    
    # Count vectors per source file
    source_counts = Counter(sources)
    
    # Display results
    print("📚 Indexed Source Files:\n")
    print(f"{'File Name':<50} {'Chunks':<10}")
    print("-" * 60)
    
    for source, count in sorted(source_counts.items()):
        print(f"{source:<50} {count:<10}")
    
    print("-" * 60)
    print(f"\n✅ Total unique files: {len(source_counts)}")
    print(f"✅ Total chunks: {sum(source_counts.values())}")
    
    return dict(source_counts)

