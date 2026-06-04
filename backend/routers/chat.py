# This file defines the /api/chat endpoint
# It receives a question, runs guardrails, runs the RAG pipeline,
# and returns an answer with sources

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag import generate_answer
from services.guardrails import check_input, check_output

router = APIRouter()


# Pydantic models define what data we expect to receive
class ChatRequest(BaseModel):
    question: str


class Source(BaseModel):
    document: str
    page: int
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    Receives: { "question": "What is the contract value?" }
    Returns: { "answer": "The contract value is...", "sources": [...] }
    """
    
    # ─── GUARDRAIL: Check Input ───
    input_check = check_input(request.question)
    if not input_check["is_safe"]:
        raise HTTPException(
            status_code=400,
            detail=input_check["reason"]
        )
    
    # ─── RAG PIPELINE ───
    try:
        result = generate_answer(request.question)
    except Exception as e:
        print(f"❌ Error generating answer: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate an answer. Please try again."
        )
    
    # ─── GUARDRAIL: Check Output ───
    output_check = check_output(result["answer"])
    if not output_check["is_safe"]:
        raise HTTPException(
            status_code=500,
            detail=output_check["reason"]
        )
    
    return {
        "answer": result["answer"],
        "sources": result["sources"]
    }