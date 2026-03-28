import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import "./styles.css";

function App() {

  // Get API URL from environment variables (with fallback for local development)
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const CHAT_ENDPOINT = `${API_URL}/v1/chat`;

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! 👋 Upload a medical report or ask a question about your health results.\n\n⚠️ This tool provides informational insights and is not a medical diagnosis."
    }
  ]);

  const [streamingMessage, setStreamingMessage] = useState("");
  const [retryingIndex, setRetryingIndex] = useState(null);
  const [limitReached, setLimitReached] = useState(false);
  const SESSION_KEY = "health_insights_session_id";

  const addMessage = (message) => {
    setMessages(prev => [...prev, message]);
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

  // 🔁 RETRY - Stream message again and replace error message
  const retryMessage = async (originalInput, index) => {
    if (!originalInput) return;

    setRetryingIndex(index);
    setStreamingMessage("");

    try {
      const formData = new FormData();
      
      if (typeof originalInput === 'object' && originalInput.file) {
        formData.append("file", originalInput.file);
        if (originalInput.input) {
          formData.append("message", originalInput.input);
        }
      } else if (typeof originalInput === 'string') {
        formData.append("message", originalInput);
      }

      // Prepare request headers
      const headers = {
        "Accept": "text/event-stream"
      };

      // Get stored session ID and add to headers if it exists
      const storedSessionId = getStoredSessionId();
      if (storedSessionId) {
        headers["X-Session-ID"] = storedSessionId;
      }

      const response = await fetch(CHAT_ENDPOINT, {
        method: "POST",
        headers: headers,
        body: formData
      });

      // Check for session ID in response headers
      const returnedSessionId = response.headers.get("x-session-id");
      if (returnedSessionId && returnedSessionId !== storedSessionId) {
        saveSessionId(returnedSessionId);
        console.log("✅ Session created/updated:", returnedSessionId);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalMessage = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        let parts = buffer.split("\n\n");

        for (let i = 0; i < parts.length - 1; i++) {
          const line = parts[i];
          if (line.startsWith("data:")) {
            const json = line.replace("data:", "").trim();
            try {
              const parsed = JSON.parse(json);
              if (parsed.type === "status") {
                finalMessage = parsed.message;
                setStreamingMessage(finalMessage);
              } else if (parsed.type === "complete") {
                finalMessage = parsed.message;
                setStreamingMessage(finalMessage);
              }
            } catch (e) {
              console.error("Parse error:", e);
            }
          }
        }
        buffer = parts[parts.length - 1];
      }

      // Replace error message with actual response
      setMessages(prev => {
        const updated = [...prev];
        updated[index] = {
          role: "assistant",
          content: finalMessage || "No response received."
        };
        return updated;
      });

    } catch (error) {
      console.error("Retry error:", error);
      setMessages(prev => {
        const updated = [...prev];
        updated[index] = {
          role: "assistant",
          content: "Retry failed. Please try again.",
          error: true,
          originalInput
        };
        return updated;
      });
    }

    setStreamingMessage("");
    setRetryingIndex(null);
  };

  return (
    <div className="app">

      <div className="header">
        🩺 Health Insights AI Assistant
      </div>

      <ChatWindow
        messages={messages}
        streamingMessage={streamingMessage}
        onRetry={retryMessage}
        retryingIndex={retryingIndex}
      />

      <ChatInput
        addMessage={addMessage}
        setStreamingMessage={setStreamingMessage}
        limitReached={limitReached}
        setLimitReached={setLimitReached}
      />

    </div>
  );
}

export default App;