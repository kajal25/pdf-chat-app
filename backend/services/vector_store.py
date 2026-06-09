# vector_store.py
# 
# IMPORTANT PATTERN: "Lazy initialization"
# _embeddings_model and _vectorstore start as None.
# They are only created when a function is first CALLED.
# Nothing runs at import time — this prevents all startup crashes.

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# Both are None at startup — created on first use
_embeddings_model = None
_vectorstore = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings_model
    if _embeddings_model is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set!")
        _embeddings_model = OpenAIEmbeddings(
            openai_api_key=api_key,
            model="text-embedding-ada-002"
        )
    return _embeddings_model


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name="pdf_documents",
            embedding_function=_get_embeddings(),
            persist_directory="./chroma_db"
        )
    return _vectorstore


def add_documents(chunks: List[dict]) -> int:
    if not chunks:
        return 0

    vs = _get_vectorstore()

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
        safe_name = (
            chunk["metadata"]["source"]
            .replace(".", "_")
            .replace(" ", "_")
        )
        ids.append(f"{safe_name}_p{chunk['metadata']['page']}_c{i}")

    # Skip duplicates
    existing = vs.get(ids=ids)
    existing_ids = set(existing["ids"])
    new_docs = [d for d, i in zip(documents, ids) if i not in existing_ids]
    new_ids = [i for i in ids if i not in existing_ids]

    if not new_docs:
        print("All chunks already stored — skipping")
        return 0

    vs.add_documents(documents=new_docs, ids=new_ids)
    print(f"Stored {len(new_docs)} new chunks")
    return len(new_docs)


def search_similar(query: str, n_results: int = 5) -> dict:
    vs = _get_vectorstore()
    count = vs._collection.count()

    if count == 0:
        return {"documents": [[]], "metadatas": [[]]}

    results = vs.similarity_search(query, k=min(n_results, count))

    return {
        "documents": [[doc.page_content for doc in results]],
        "metadatas": [[doc.metadata for doc in results]]
    }


def list_documents() -> List[str]:
    vs = _get_vectorstore()
    if vs._collection.count() == 0:
        return []
    all_items = vs.get()
    filenames = {
        m["source"]
        for m in all_items["metadatas"]
        if m and "source" in m
    }
    return sorted(list(filenames))