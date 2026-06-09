# vector_store.py — Rewritten to use LangChain's Chroma wrapper
#
# WHY THE CHANGE:
# ChromaDB's built-in OpenAIEmbeddingFunction passes a "proxies" argument
# to openai.OpenAI(), but newer versions of openai removed that argument.
# → Fix: use LangChain's OpenAIEmbeddings + LangChain's Chroma wrapper instead.
# LangChain handles embeddings separately, completely avoiding the conflict.

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# LangChain's OpenAIEmbeddings — works fine with openai 1.16.2
embeddings_model = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-ada-002"
)

# LangChain's Chroma wrapper
# persist_directory = where ChromaDB saves its data on disk
vectorstore = Chroma(
    collection_name="pdf_documents",
    embedding_function=embeddings_model,
    persist_directory="./chroma_db"
)


def add_documents(chunks: List[dict]) -> int:
    """
    Stores text chunks in ChromaDB via LangChain.
    LangChain's Chroma wrapper handles the embedding automatically.
    """

    if not chunks:
        return 0

    # Convert our chunk dicts into LangChain Document objects
    # LangChain uses Document(page_content=..., metadata=...) format
    documents = []
    ids = []

    for i, chunk in enumerate(chunks):
        documents.append(
            Document(
                page_content=chunk["text"],
                metadata={
                    "source": chunk["metadata"]["source"],
                    "page": chunk["metadata"]["page"]
                }
            )
        )

        # Unique ID for each chunk
        safe_name = chunk["metadata"]["source"].replace(".", "_").replace(
            " ", "_"
            )
        ids.append(f"{safe_name}_p{chunk['metadata']['page']}_c{i}")

    # Check for existing IDs to avoid duplicates
    existing = vectorstore.get(ids=ids)
    existing_ids = set(existing["ids"])

    # Filter to only new documents
    new_docs = []
    new_ids = []
    for doc, doc_id in zip(documents, ids):
        if doc_id not in existing_ids:
            new_docs.append(doc)
            new_ids.append(doc_id)

    if not new_docs:
        print("ℹ️  All chunks already in the database — skipping")
        return 0

    # This sends texts to OpenAI for embedding, then stores in ChromaDB
    vectorstore.add_documents(documents=new_docs, ids=new_ids)

    print(f"✅ Stored {len(new_docs)} new chunks in ChromaDB")
    return len(new_docs)


def search_similar(query: str, n_results: int = 5) -> dict:
    """
    Finds the most relevant chunks for a query using similarity search.
    Returns results in the same format as before so rag.py 
    doesn't need changes.
    """

    # Check if the collection has anything in it
    count = vectorstore._collection.count()
    if count == 0:
        return {"documents": [[]], "metadatas": [[]]}

    # Don't ask for more results than we have stored
    actual_results = min(n_results, count)

    # LangChain similarity search — returns list of Document objects
    results = vectorstore.similarity_search(query, k=actual_results)

    # Convert back to the same dict format that rag.py expects
    documents = [doc.page_content for doc in results]
    metadatas = [doc.metadata for doc in results]

    return {
        "documents": [documents],
        "metadatas": [metadatas]
    }


def list_documents() -> List[str]:
    """Returns all unique PDF filenames stored in the database."""

    count = vectorstore._collection.count()
    if count == 0:
        return []

    # Get all stored items and extract unique source filenames
    all_items = vectorstore.get()

    filenames = set()
    for metadata in all_items["metadatas"]:
        if metadata and "source" in metadata:
            filenames.add(metadata["source"])

    return sorted(list(filenames))