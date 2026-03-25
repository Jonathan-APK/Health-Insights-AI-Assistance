export default function Message({ message, onRetry, index, retryingIndex }) {

  const isRetrying = retryingIndex === index;

  return (
    <div className={`message ${message.role}`}>

      {isRetrying ? (
        "Retrying response..."
      ) : (
        <>
          {/* FILES */}
          <div className="file-row">
            {message.content
              .split("\n")
              .filter(line => line.startsWith("📄"))
              .map((file, i) => (
                <span key={i} className="file-bubble">
                  {file}
                </span>
              ))}
          </div>

          {/* TEXT */}
          <div className="message-text">
            {message.content
              .split("\n")
              .filter(line => !line.startsWith("📄"))
              .map((line, i) => (
                <div key={i}>{line}</div>
              ))}
          </div>
        </>
      )}

      {message.error && !isRetrying && (
        <div>
          <button
            className="retry-btn"
            onClick={() => onRetry(message.originalInput, index)}
          >
            Retry
          </button>
        </div>
      )}

    </div>
  );
}