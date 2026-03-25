import { useRef, useState } from "react";
import axios from "axios";

export default function ChatInput({ addMessage, setStreamingMessage }) {

  const [input, setInput] = useState("");
  const [files, setFiles] = useState([]);
  const fileRef = useRef();

  const sendMessage = async () => {

    if (!input && !file) return;

    // FILE UPLOAD
    if (files.length > 0) {
      // Show user message
      addMessage({
        role: "user",
        content: [
          ...files.map(f => `📄 ${f.name}`),
          input
        ]
          .filter(Boolean) // removes empty input
          .join("\n")
      });

      const formData = new FormData();

      files.forEach((file) => {
        formData.append("files", file); // backend must support this
      });

      if (input) {
        formData.append("message", input);
      }

      try {
        const res = await axios.post(
          "http://localhost:8000/analyze-report",
          formData
        );

        addMessage({
          role: "assistant",
          content: res.data.summary
        });

      } catch {
        addMessage({
          role: "assistant",
          content: "Upload failed. Try again.",
          error: true,
          originalInput: { files, input } // 👈 important for retry later
        });
      }

      setFiles([]);
      setInput("");
      return;
    }

    // CHAT STREAM
    addMessage({ role: "user", content: input });
    startStreaming(input);
    setInput("");
  };

  const startStreaming = (message) => {

    setStreamingMessage("");

    const eventSource = new EventSource(
      `http://localhost:8000/chat-stream?message=${encodeURIComponent(message)}`
    );

    let accumulated = "";

    eventSource.onmessage = (event) => {
      accumulated += event.data;
      setStreamingMessage(accumulated);
    };

    eventSource.onerror = () => {
      eventSource.close();

      addMessage({
        role: "assistant",
        content: accumulated || "Something went wrong.",
        error: !accumulated,
        originalInput: message
      });

      setStreamingMessage("");
    };
  };

  return (
<div className="chat-input">

  {/* 📎 Upload */}
  <button
    className="icon-btn"
    onClick={() => fileRef.current.click()}
    title="Upload file"
  >
    📎
  </button>

  <input
    ref={fileRef}
    type="file"
    multiple
    style={{ display: "none" }}
    onChange={(e) => {
      const selectedFiles = Array.from(e.target.files);
      if (!selectedFiles.length) return;

      setFiles((prev) => [...prev, ...selectedFiles]);

      e.target.value = null;
    }}
  />

  {/* 👇 NEW WRAPPER */}
    <div className="input-area">

      {files.length > 0 && (
        <div className="file-list">
          {files.map((file, i) => (
            <div key={i} className="file-chip">
              📄 {file.name}
              <span
                className="remove-file"
                onClick={() =>
                  setFiles(files.filter((_, index) => index !== i))
                }
              >
                ✕
              </span>
            </div>
          ))}
        </div>
      )}

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") sendMessage();
        }}
        placeholder="Ask about your lab results..."
      />

    </div>

    <button onClick={sendMessage}>
      Send
    </button>

  </div>
  );
}