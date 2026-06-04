# This file defines the /api/upload endpoint
# It receives PDF files from the browser, saves them, processes them,
# and stores the chunks in ChromaDB

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import aiofiles  # For async file writing
from services.pdf_processor import extract_and_chunk_pdf
from services.vector_store import add_documents, list_documents

router = APIRouter()

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create folder if it doesn't exist


@router.post("/")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Receives one or more PDF files, processes them, and stores in ChromaDB.
    
    The "async def" and "await" keywords mean this runs without blocking
    other requests while files are being saved.
    """
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    
    for file in files:
        # Validate: only accept PDF files
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"'{file.filename}' is not a PDF. "
                    "Only PDF files are accepted."
                )
            )
        
        # Validate: check file size (max 50MB)
        MAX_SIZE = 50 * 1024 * 1024  # 50 MB in bytes
        
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Save the file to disk
        # aiofiles lets us write files without blocking the server
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            
            if len(content) > MAX_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"'{file.filename}' is too large. Max size is 50MB."
                )
            
            await f.write(content)
        
        print(f"💾 Saved file: {file.filename}")
        
        # Extract text and create chunks
        try:
            chunks = extract_and_chunk_pdf(file_path, file.filename)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Could not process '{file.filename}': {str(e)}."
                    "Make sure it's a valid PDF with extractable text."
                )
            )
        
        if not chunks:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"No text found in '{file.filename}'."
                    "The PDF might be a scanned image without OCR text."
                )
            )
        
        # Store chunks in ChromaDB
        num_added = add_documents(chunks)
        
        results.append({
            "filename": file.filename,
            "pages_found": len(set(c["metadata"]["page"] for c in chunks)),
            "chunks_stored": num_added,
            "status": "success"
        })
    
    return {
        "message": f"Successfully processed {len(files)} PDF(s)",
        "results": results,
        "all_documents": list_documents()
    }


@router.get("/documents")
async def get_documents():
    """Returns a list of all uploaded and indexed PDF filenames."""
    return {"documents": list_documents()}