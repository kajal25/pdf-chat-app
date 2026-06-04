// ChatWindow.jsx — The main chat interface
//
// Shows conversation history and handles sending messages.
// Each AI message shows its source citations.

import { useState, useRef, useEffect } from "react"
import { sendQuestion } from "../api"

// A single message bubble
function Message({ message }) {
  const isUser = message.role === "user"
  
  return (
    <div className={`message-wrapper ${isUser ? "user-message" : "ai-message"}`}>
      
      {/* Avatar */}
      <div className="message-avatar">
        {isUser ? "👤" : "🤖"}
      </div>
      
      {/* Content bubble */}
      <div className="message-bubble">
        
        {/* The actual text */}
        <p className="message-text">{message.content}</p>
        
        {/* Source citations — only shown for AI messages that have sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="sources-section">
            <p className="sources-title">📚 Sources used:</p>
            {message.sources.map((source, i) => (
              <div key={i} className="source-card">
                <div className="source-header">
                  <span className="source-doc">📄 {source.document}</span>
                  <span className="source-page">Page {source.page}</span>
                </div>
                <p className="source-excerpt">"{source.excerpt}"</p>
              </div>
            ))}
          </div>
        )}
        
      </div>
    </div>
  )
}


function ChatWindow({ hasDocuments }) {
  const [messages, setMessages] = useState([])      // Conversation history
  const [input, setInput] = useState("")            // Current input text
  const [isLoading, setIsLoading] = useState(false) // Waiting for AI response?
  
  // Used to auto-scroll to the latest message
  const messagesEndRef = useRef(null)
  
  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])
  
  const handleSend = async () => {
    const question = input.trim()
    
    if (!question || isLoading) return
    
    // Add user's message to the conversation
    const userMessage = { role: "user", content: question, sources: [] }
    setMessages((prev) => [...prev, userMessage])
    setInput("")         // Clear the input box
    setIsLoading(true)
    
    try {
      const result = await sendQuestion(question)
      
      // Add AI's response to the conversation
      const aiMessage = {
        role: "assistant",
        content: result.answer,
        sources: result.sources
      }
      setMessages((prev) => [...prev, aiMessage])
      
    } catch (error) {
      const errorText = error.response?.data?.detail || "Something went wrong. Please try again."
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: `❌ ${errorText}`,
        sources: []
      }])
    } finally {
      setIsLoading(false)
    }
  }
  
  // Allow sending with Enter key (Shift+Enter for newline)
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }
  
  return (
    <div className="chat-container">
      <h2 className="section-title">💬 Chat with your PDFs</h2>
      
      {/* Message area */}
      <div className="messages-area">
        
        {/* Welcome message when no conversation yet */}
        {messages.length === 0 && (
          <div className="welcome-message">
            {hasDocuments 
              ? "Your PDFs are ready! Ask me anything about them."
              : "Upload some PDFs above to get started."
            }
          </div>
        )}
        
        {/* All messages */}
        {messages.map((msg, i) => (
          <Message key={i} message={msg} />
        ))}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="loading-indicator">
            <span>🤖 Thinking</span>
            <span className="dots">...</span>
          </div>
        )}
        
        {/* Invisible element at the bottom — we scroll to this */}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input area */}
      <div className="input-area">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            hasDocuments 
              ? "Ask a question about your PDFs... (Enter to send)"
              : "Upload PDFs first, then ask questions here"
          }
          rows={3}
          disabled={isLoading || !hasDocuments}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={isLoading || !input.trim() || !hasDocuments}
        >
          {isLoading ? "⏳" : "Send"}
        </button>
      </div>
    </div>
  )
}

export default ChatWindow