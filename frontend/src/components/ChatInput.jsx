import { useRef, useState } from "react";

export default function ChatInput({ addMessage, setStreamingMessage, limitReached, setLimitReached }) {

  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const fileRef = useRef();

  // Get API URL from environment variables (with fallback for local development)
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const CHAT_ENDPOINT = `${API_URL}/v1/chat`;

  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB in bytes
  const ALLOWED_TYPE = "application/pdf";
  const SESSION_KEY = "health_insights_session_id";

  const validateFile = (selectedFile) => {
    if (!selectedFile) {
      setFileError("");
      return false;
    }

    // Check file type
    if (selectedFile.type !== ALLOWED_TYPE) {
      setFileError("Only PDF files are allowed");
      return false;
    }

    // Check file size
    if (selectedFile.size > MAX_FILE_SIZE) {
      setFileError("File size must be less than 5MB");
      return false;
    }

    setFileError("");
    return true;
  };

  // Get stored session ID from localStorage
  const getStoredSessionId = () => {
    return localStorage.getItem(SESSION_KEY);
  };

  // Save session ID to localStorage
  const saveSessionId = (sessionId) => {
    if (sessionId) {
      localStorage.setItem(SESSION_KEY, sessionId);
    }
  };

  const sendMessage = async () => {

    if (!input && !file) return;

    // Show user message
    addMessage({
      role: "user",
      content: [
        ...(file ? [`📄 ${file.name}`] : []),
        input
      ]
        .filter(Boolean)
        .join("\n")
    });

    // Prepare FormData
    const formData = new FormData();

    if (file) {
      formData.append("file", file);
    }

    if (input) {
      formData.append("message", input);
    }

    // Start streaming
    startStreaming(formData, { file, input });

    setFile(null);
    setInput("");
  };

  const startStreaming = async (formData, originalInput) => {

    setStreamingMessage("");

    try {
      // Prepare request headers
      const headers = {
        "Accept": "text/event-stream"
      };

      // Get stored session ID and add to headers if it exists
      const storedSessionId = getStoredSessionId();
      if (storedSessionId) {
        headers["X-Session-ID"] = storedSessionId;
      }

      const response = await fetch(
        CHAT_ENDPOINT,
        {
          method: "POST",
          headers: headers,
          body: formData
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Check for session ID in response headers
      const returnedSessionId = response.headers.get("x-session-id");
      if (returnedSessionId && returnedSessionId !== storedSessionId) {
        saveSessionId(returnedSessionId);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";
      let finalResponse = "";
      let hasError = false;
      let limitReachedFlag = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Split by double newlines (SSE message separator)
        let parts = buffer.split("\n\n");

        // Process all complete messages
        for (let i = 0; i < parts.length - 1; i++) {
          const line = parts[i];

          if (line.startsWith("data:")) {
            const json = line.replace("data:", "").trim();

            try {
              const parsed = JSON.parse(json);
              
              // Error message
              if (parsed.type === "error") {
                hasError = true;
                finalResponse = parsed.message;
                setStreamingMessage(finalResponse);
              } 
              // Status message - display in real-time while streaming
              else if (parsed.type === "status") {
                finalResponse = parsed.message;
                setStreamingMessage(finalResponse);
              } 
              // Complete message - finalize and add to chat
              else if (parsed.type === "complete") {
                finalResponse = parsed.message;
                setStreamingMessage(finalResponse);
                
                // Check if limit reached
                if (parsed.limit_reached) {
                  limitReachedFlag = true;
                  setLimitReached(true);
                }
              }
            } catch (e) {
              console.error("Failed to parse JSON:", json, e);
            }
          }
        }

        // Keep incomplete message in buffer
        buffer = parts[parts.length - 1];
      }

      // Add final message to chat history
      addMessage({
        role: "assistant",
        content: finalResponse || "No response received.",
        error: hasError,
        originalInput,
        limitReached: limitReachedFlag
      });

    } catch (error) {
      console.error("Streaming error:", error);

      addMessage({
        role: "assistant",
        content: "Something went wrong. Please try again.",
        error: true,
        originalInput
      });
    }

    // Clear streaming display after message is added to history
    setStreamingMessage("");
  };

  return (
    <div className="chat-input">

      {/* Limit Reached Warning */}
      {limitReached && (
        <div className="limit-reached-banner">
          ⚠️ You have reached the maximum number of messages for this session. Please start a new session.
        </div>
      )}

      <div className="chat-input-controls">
        {/* Upload */}
        <button
          className="upload-btn"
          onClick={() => fileRef.current.click()}
          title={limitReached ? "Session limit reached" : "Upload file"}
          disabled={limitReached}
        >
          ➕
        </button>

      <input
        ref={fileRef}
        type="file"
        accept=".pdf"
        style={{ display: "none" }}
        disabled={limitReached}
        onChange={(e) => {
          const selectedFile = e.target.files?.[0];
          
          if (validateFile(selectedFile)) {
            setFile(selectedFile);
          }

          e.target.value = null;
        }}
      />

      {/* File list wrapper */}
      <div className="input-area">

        {fileError && (
          <div className="file-error">
            {fileError}
          </div>
        )}

        {file && (
          <div className="file-list">
            <div className="file-chip">
              📄 {file.name}
              <span
                className="remove-file"
                onClick={() => setFile(null)}
              >
                ✕
              </span>
            </div>
          </div>
        )}

        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !limitReached) sendMessage();
          }}
          disabled={limitReached}
          placeholder={limitReached ? "Session limit reached" : "Ask about your lab results..."}
        />

      </div>

      <button className="send-btn" onClick={sendMessage} disabled={limitReached}>
        Send
      </button>
      </div>

    </div>
  );
}