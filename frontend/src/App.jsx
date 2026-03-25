import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import "./styles.css";

function App() {

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! 👋 Upload a medical report or ask a question about your health results.\n\n⚠️ This tool provides informational insights and is not a medical diagnosis."
    }
  ]);

  const [streamingMessage, setStreamingMessage] = useState("");
  const [retryingIndex, setRetryingIndex] = useState(null);
  const addMessage = (message) => {
    setMessages(prev => [...prev, message]);
  };

  // 🔁 RETRY FUNCTION (NO PAGE RELOAD)
const retryMessage = (originalInput, index) => {
  if (!originalInput) return;

  setRetryingIndex(index); // 👈 START loading
  setStreamingMessage("");

  const eventSource = new EventSource(
    `http://localhost:8000/chat-stream?message=${encodeURIComponent(originalInput)}`
  );

  let accumulated = "";

  eventSource.onmessage = (event) => {
    accumulated += event.data;
    setStreamingMessage(accumulated);
  };

  eventSource.onerror = () => {
    eventSource.close();

    setMessages(prev => {
      const updated = [...prev];

      updated[index] = {
        role: "assistant",
        content: accumulated || "Retry failed again.",
        error: !accumulated,
        originalInput
      };

      return updated;
    });

    setStreamingMessage("");
    setRetryingIndex(null); // 👈 END loading
  };
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
      />

    </div>
  );
}

export default App;