// api.js — All communication with the backend API
// 
// Instead of writing fetch() calls scattered everywhere,
// we centralize all API calls here. Easy to change later.

import axios from "axios"

// This reads from your .env file: VITE_API_URL=http://localhost:8000
// In production, you'll set this to your Railway URL
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

// Create a configured axios instance (base URL pre-set)
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
})


/**
 * Upload multiple PDF files
 * @param {File[]} files - Array of File objects from the file input
 */
export async function uploadPDFs(files) {
  // FormData is needed for file uploads (like an HTML form with enctype="multipart/form-data")
  const formData = new FormData()
  
  files.forEach((file) => {
    formData.append("files", file)  // "files" must match the FastAPI parameter name
  })
  
  const response = await api.post("/api/upload/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",  // Override for file uploads
    },
  })
  
  return response.data
}


/**
 * Fetch all uploaded document names
 */
export async function getDocuments() {
  const response = await api.get("/api/upload/documents")
  return response.data
}


/**
 * Send a question and get an AI-powered answer with sources
 * @param {string} question - The user's question
 */
export async function sendQuestion(question) {
  const response = await api.post("/api/chat/", { question })
  return response.data
}