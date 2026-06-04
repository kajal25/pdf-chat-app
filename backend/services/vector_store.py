# This file manages ChromaDB — our vector database
# It stores text chunks as embeddings and searches for similar ones

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from the .env file

# Create a ChromaDB client that saves data to disk
# "PersistentClient" means data survives even after you restart the server
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Set up OpenAI's embedding function
# This function converts text → numbers (embeddings)
openai_embedding_fn = OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-ada-002"  # OpenAI's best embedding model
)


def get_collection():
    """
    Gets or creates our ChromaDB collection.
    A "collection" is like a table in a regular database.
    We use one collection for all PDF chunks.
    """
    return chroma_client.get_or_create_collection(
        name="pdf_documents",
        embedding_function=openai_embedding_fn,
        metadata={"hnsw:space": "cosine"}  
        # Use cosine similarity for searching
    )


def add_documents(chunks: List[dict]) -> int:
    """
    Adds text chunks to ChromaDB.
    ChromaDB automatically converts text → embeddings using OpenAI.
    
    Returns the number of chunks added.
    """
    collection = get_collection()
    
    texts = []      # The actual text content
    metadatas = []  # Source info (filename, page number)
    ids = []        # Unique ID for each chunk (ChromaDB requires this)
    
    for i, chunk in enumerate(chunks):
        texts.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        
        # Create a unique ID using filename + page + chunk index
        # Replace spaces/dots with underscores for safety
        safe_name = chunk["metadata"]["source"].replace(
            ".", "_"
            ).replace(" ", "_")
        ids.append(f"{safe_name}_page{chunk['metadata']['page']}_chunk{i}")
    
    # Check if these IDs already exist (to avoid duplicates when re-uploading)
    existing = collection.get(ids=ids)
    existing_ids = set(existing["ids"])
    
    # Filter out chunks that already exist
    new_texts, new_metadatas, new_ids = [], [], []
    for text, metadata, doc_id in zip(texts, metadatas, ids):
        if doc_id not in existing_ids:
            new_texts.append(text)
            new_metadatas.append(metadata)
            new_ids.append(doc_id)
    
    if new_texts:
        # This single call sends all texts to OpenAI for embedding
        # then stores the embeddings in ChromaDB
        collection.add(
            documents=new_texts,
            metadatas=new_metadatas,
            ids=new_ids
        )
        print(f"✅ Added {len(new_texts)} new chunks to ChromaDB")
    else:
        print("ℹ️  All chunks already exist in the database")
    
    return len(new_texts)


def search_similar(query: str, n_results: int = 5) -> dict:
    """
    Finds the most relevant chunks for a given question.
    
    ChromaDB converts the query to an embedding, then finds the
    stored embeddings that are most similar (closest in vector space).
    
    Returns up to n_results chunks.
    """
    collection = get_collection()
    
    # Check if collection has any documents
    count = collection.count()
    if count == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    # Don't request more results than we have
    actual_results = min(n_results, count)
    
    results = collection.query(
        query_texts=[query],    # ChromaDB will embed this automatically
        n_results=actual_results
    )
    
    return results


def list_documents() -> List[str]:
    """Returns a list of all unique PDF filenames in the database."""
    collection = get_collection()
    
    if collection.count() == 0:
        return []
    
    # Get all stored metadata
    all_items = collection.get()
    
    # Extract unique filenames
    filenames = set()
    for metadata in all_items["metadatas"]:
        filenames.add(metadata["source"])
    
    return sorted(list(filenames))