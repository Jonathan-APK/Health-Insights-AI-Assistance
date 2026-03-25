import { useEffect, useRef } from "react";
import Message from "./Message";

export default function ChatWindow({ messages, streamingMessage, onRetry, retryingIndex }) {

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  return (
    <div className="chat-window">

      {messages.map((msg, index) => (
        <Message
          key={index}
          message={msg}
          onRetry={onRetry}
          index={index}
          retryingIndex={retryingIndex}
        />
      ))}

      {/* ⏳ THINKING */}
      {!streamingMessage && messages.length > 0 && messages[messages.length - 1].role === "user" && (
        <div className="message assistant thinking">
          AI is thinking...
        </div>
      )}

      {/* ⚡ STREAM */}
      {streamingMessage && (
        <div className="message assistant">
          {streamingMessage}
        </div>
      )}

      <div ref={bottomRef}></div>

    </div>
  );
}