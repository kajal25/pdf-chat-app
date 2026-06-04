// PDFUploader.jsx — Component for uploading PDF files
//
// Props:
//   onUploadSuccess: function called when upload succeeds,
//                    receives array of uploaded filenames

import { useState } from "react"
import { uploadPDFs } from "../api"

function PDFUploader({ onUploadSuccess }) {
  // State = data that can change and causes the UI to update
  const [selectedFiles, setSelectedFiles] = useState([])   // Files picked by user
  const [isUploading, setIsUploading] = useState(false)    // Are we uploading right now?
  const [message, setMessage] = useState(null)              // Success or error message

  // Called when user picks files in the file input
  const handleFileChange = (event) => {
    // event.target.files is a FileList (not an array), so we convert it
    const files = Array.from(event.target.files)
    setSelectedFiles(files)
    setMessage(null)  // Clear any previous message
  }

  // Called when user clicks "Upload PDFs"
  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setMessage({ type: "error", text: "Please select at least one PDF file first." })
      return
    }

    setIsUploading(true)
    setMessage(null)

    try {
      const result = await uploadPDFs(selectedFiles)
      
      setMessage({
        type: "success",
        text: `✅ ${result.message}`
      })
      
      // Tell the parent component which files were uploaded
      const uploadedNames = result.results.map((r) => r.filename)
      onUploadSuccess(uploadedNames)
      
      // Reset the file selection
      setSelectedFiles([])
      // Reset the actual file input element
      document.getElementById("pdf-input").value = ""
      
    } catch (error) {
      // Axios wraps error responses in error.response
      const errorMessage = error.response?.data?.detail || error.message || "Upload failed"
      setMessage({ type: "error", text: `❌ ${errorMessage}` })
    } finally {
      // This runs whether it succeeded or failed
      setIsUploading(false)
    }
  }

  // Handle drag-and-drop
  const handleDrop = (event) => {
    event.preventDefault()
    const files = Array.from(event.dataTransfer.files).filter(
      (f) => f.type === "application/pdf"
    )
    setSelectedFiles(files)
  }

  const handleDragOver = (event) => {
    event.preventDefault()  // Required to allow drop
  }

  return (
    <div className="uploader-container">
      <h2 className="section-title">📤 Upload PDFs</h2>
      
      {/* Drag and drop zone */}
      <div
        className="drop-zone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => document.getElementById("pdf-input").click()}
      >
        <p>Drag & drop PDFs here</p>
        <p className="drop-zone-sub">or click to browse</p>
        
        {/* Hidden file input — triggered by clicking the drop zone */}
        <input
          id="pdf-input"
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
      </div>
      
      {/* Show selected files */}
      {selectedFiles.length > 0 && (
        <div className="selected-files">
          <p className="selected-files-title">Selected files:</p>
          {selectedFiles.map((file, i) => (
            <div key={i} className="selected-file">
              📄 {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </div>
          ))}
        </div>
      )}
      
      {/* Upload button */}
      <button
        className="upload-button"
        onClick={handleUpload}
        disabled={isUploading || selectedFiles.length === 0}
      >
        {isUploading ? "⏳ Processing..." : "Upload PDFs"}
      </button>
      
      {/* Status message */}
      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}
    </div>
  )
}

export default PDFUploader