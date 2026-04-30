import React, { useState, useRef, useEffect } from "react";
import "./Chatbot.css";
import { apiUrl } from "../lib/api";

const Chatbot = ({ currentUser }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const chatEndRef = useRef(null);

  // Scroll to bottom on new message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    setMessages([...messages, { type: "user", text: input }]);
    setLoading(true);

    try {
      const res = await fetch(apiUrl("/chatbot/query"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: currentUser.id, query: input }),
      });

      const data = await res.json();
      let botReply = "No recommendations found.";
      let images = [];

      if (data.results && data.results.length > 0) {
        const topResults = data.results.slice(0, 3);
        botReply = `Here are the top ${topResults.length} items I found:`;
        images = topResults.map((r, index) => ({
          url: r.url,
          style: r.style,
          index: index + 1
        }));
      } else {
        botReply =
          "I couldn't find any items matching your query. Try uploading images first or use different terms like 'formal wear' or 'summer outfit'.";
      }

      setMessages((prev) => [...prev, { type: "bot", text: botReply, images }]);
    } catch (err) {
      setMessages((prev) => [...prev, { type: "bot", text: "Error fetching results" }]);
    } finally {
      setInput("");
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-placeholder">
            Ask me anything about fashion! Try: "What should I wear for a job interview?"
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`chat-message ${m.type}`}>
              <div className="chat-text">{m.text}</div>
              {m.images && m.images.length > 0 && (
                <div className="image-grid">
                  {m.images.map((img, idx) => (
                    <div key={idx} className="image-card">
                      <img
                        src={img.url}
                        alt={`Recommendation ${img.index}`}
                        onClick={() => setSelectedImage(img)}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="chat-input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask for dress suggestions..."
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          {loading ? "..." : "Send"}
        </button>
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div className="image-modal-overlay" onClick={() => setSelectedImage(null)}>
          <div className="image-modal" onClick={(e) => e.stopPropagation()}>
            <button className="image-modal-close" onClick={() => setSelectedImage(null)}>
              ✕
            </button>
            <img src={selectedImage.url} alt={`Recommendation ${selectedImage.index}`} />
            <div className="image-modal-info">
              <h3>Style: {selectedImage.style}</h3>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chatbot;
