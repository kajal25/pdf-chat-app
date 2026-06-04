// App.jsx — The root component that holds everything together
//
// Structure:
//   App
//   ├── Header
//   ├── PDFUploader  (left panel)
//   ├── DocumentList (shows uploaded docs)
//   └── ChatWindow   (right panel)

import { useState, useEffect } from "react"
import PDFUploader from "./components/PDFUploader"
import ChatWindow from "./components/ChatWindow"
import { getDocuments } from "./api"
import "./App.css"

function App() {
  // List of all uploaded document names
  const [uploadedDocs, setUploadedDocs] = useState([])
  
  // Load existing documents when the app first opens
  // (in case you refreshed the page — documents persist in ChromaDB)
  useEffect(() => {
    async function loadDocuments() {
      try {
        const data = await getDocuments()
        setUploadedDocs(data.documents)
      } catch (error) {
        console.log("Could not load documents (server might not be running):", error.message)
      }
    }
    loadDocuments()
  }, [])  // Empty array = run only once when component mounts
  
  // Called by PDFUploader after a successful upload
  const handleUploadSuccess = (newFilenames) => {
    setUploadedDocs((prev) => {
      // Merge new filenames with existing ones, avoiding duplicates
      const allDocs = [...new Set([...prev, ...newFilenames])]
      return allDocs
    })
  }
  
  return (
    <div className="app">
      
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">📚 Dive in PDF</h1>
          <p className="app-subtitle">Upload documents · Ask questions · Get answers with citations</p>
        </div>
      </header>
      
      {/* Main content */}
      <main className="app-main">
        
        {/* Left panel: Upload + Document List */}
        <div className="left-panel">
          <PDFUploader onUploadSuccess={handleUploadSuccess} />
          
          {/* Show list of uploaded documents */}
          {uploadedDocs.length > 0 && (
            <div className="document-list">
              <h3 className="document-list-title">📂 Loaded Documents ({uploadedDocs.length})</h3>
              {uploadedDocs.map((doc, i) => (
                <div key={i} className="document-item">
                  📄 {doc}
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Right panel: Chat */}
        <div className="right-panel">
          <ChatWindow hasDocuments={uploadedDocs.length > 0} />
        </div>
        
      </main>
    </div>
  )
}

export default App