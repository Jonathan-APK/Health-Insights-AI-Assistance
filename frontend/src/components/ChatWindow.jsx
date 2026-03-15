import { useEffect, useRef } from "react";
import Message from "./Message";

export default function ChatWindow({ messages }) {

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-window">

      {messages.map((msg, index) => (
        <Message key={index} message={msg} />
      ))}

      <div ref={bottomRef}></div>

    </div>
  );
}