export default function Message({ message }) {

  return (
    <div className={`message ${message.role}`}>
      {message.content}
    </div>
  );

}