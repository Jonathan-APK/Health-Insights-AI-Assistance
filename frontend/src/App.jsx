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
  
  const addMessage = (message) => {
    setMessages(prev => [...prev, message]);
  };

  return (
    <div className="app">

      <div className="header">
        🩺 Health Insights AI Assistant
      </div>

      <ChatWindow messages={messages} />

      <ChatInput addMessage={addMessage} />

    </div>
  );
}

export default App;