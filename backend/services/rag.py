# This is the heart of the application — the RAG pipeline.
# 
# RAG = Retrieve context → Augment the prompt → Generate an answer
#
# Steps:
# 1. Take the user's question
# 2. Find the most relevant PDF chunks in ChromaDB
# 3. Build a prompt: "Given these chunks, answer this question"
# 4. Send to OpenAI GPT
# 5. Return the answer + which sources it came from

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from services.vector_store import search_similar
import os
from dotenv import load_dotenv

load_dotenv()


def generate_answer(question: str) -> dict:
    """
    Main RAG function: takes a question, returns an answer with sources.
    
    Returns:
    {
        "answer": "The contract expires on December 31st...",
        "sources": [
            {
                "document": "contract.pdf",
                "page": 4,
                "excerpt": "This agreement shall terminate on..."
            },
            ...
        ]
    }
    """
    
    # ─── STEP 1: RETRIEVE ───
    # Find the most relevant chunks from ChromaDB
    
    print(f"🔍 Searching for relevant chunks for: '{question[:50]}...'")
    results = search_similar(question, n_results=5)
    
    # Check if we got any results
    if not results["documents"] or not results["documents"][0]:
        return {
            "answer": "I couldn't find any relevant information "
            "in the uploaded documents. "
            "Please make sure you've uploaded PDFs and that they contain text "
            "(not just scanned images).",
            "sources": []
        }
    
    # ─── STEP 2: AUGMENT ───
    # Build the context string from retrieved chunks
    
    context_parts = []
    sources = []
    
    chunks = results["documents"][0]      # List of text chunks
    metadatas = results["metadatas"][0]   # List of corresponding metadata
    
    for i, (chunk_text, metadata) in enumerate(zip(chunks, metadatas)):
        source_label = f"[Source {i+1}: {metadata['source']}," 
        f" Page {metadata['page']}]"
        context_parts.append(f"{source_label}\n{chunk_text}")
        
        sources.append({
            "document": metadata["source"],
            "page": metadata["page"],
            # Show first 300 chars as excerpt, add "..." if longer
            "excerpt": chunk_text[:300] + 
            ("..." if len(chunk_text) > 300 else "")
        })
    
    # Join all context chunks into one big string
    context = "\n\n---\n\n".join(context_parts)
    
    # ─── STEP 3: BUILD THE PROMPT ───
    # This is what we'll actually send to GPT
    
    system_prompt = """You are a helpful assistant that answers questions 
    based ONLY on the provided document excerpts. 

Your rules:
1. Only use information from the provided context to answer
2. Always mention which document and page your answer comes from
3. If the context doesn't contain enough information to answer, clearly say so
4. Be concise and direct
5. Do not make up information that isn't in the context"""
    
    user_prompt = f"""Here are relevant excerpts from the uploaded documents:

{context}

---

Question: {question}

Please answer the question based on the document excerpts above. 
Mention which document(s) and page(s) the information comes from."""
    
    # ─── STEP 4: GENERATE ───
    # Send to OpenAI and get the answer
    
    print("🤖 Sending to OpenAI GPT...")
    
    # Initialize the LLM (Language Model)
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",              # Cost-effective model
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.1,          # Lower = more factual, less creative
        max_tokens=1000                     # Limit response length
    )
    
    # Create the messages (OpenAI uses a conversation format)
    messages = [
        HumanMessage(content=f"{system_prompt}\n\n{user_prompt}")
    ]
    
    # Call the API
    response = llm.invoke(messages)
    
    print(f"✅ Got answer ({len(response.content)} chars)")
    
    return {
        "answer": response.content,
        "sources": sources
    }