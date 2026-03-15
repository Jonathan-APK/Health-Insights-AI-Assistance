import { useState } from "react";
import axios from "axios";

export default function ChatInput({ addMessage }) {

  const [input, setInput] = useState("");

  const sendMessage = async () => {

    if (!input) return;

    addMessage({ role: "user", content: input });

    try {

      const response = await axios.post(
        "http://localhost:8000/chat",
        { message: input }
      );

      addMessage({
        role: "assistant",
        content: response.data.reply
      });

    } catch (error) {

      addMessage({
        role: "assistant",
        content: "Unable to reach server."
      });

    }

    setInput("");

  };

  return (
    <div className="chat-input">

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") sendMessage();
        }}
        placeholder="Type your message..."
      />

      <button onClick={sendMessage}>
        Send
      </button>

    </div>
  );
}