import React, { useEffect, useState, useRef } from "react";
import {
  Box,
  Paper,
  Divider,
  Typography,
  LinearProgress,
  TextField,
  IconButton,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import axios from "axios";
import ReactMarkdown from "react-markdown";


const ChatsPanel = () => {
  const [input, setInput] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessage] = useState<Array<any>>([]);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const fetchMessages = async () => {
      setIsLoading(true);
      try {
        const res = await axios.get("/api/chat_messages/recent");
        console.log("API response:", res.data);
        const logs = Array.isArray(res.data)
          ? res.data
          : res.data.messages || [];
        // Flatten each log into user and bot messages
        const chatMessages = logs.flatMap((log: any) => [
          {
            text: log.user_message,
            sender: "user",
            timestamp: log.timestamp,
            _id: log._id + "_user",
          },
          {
            text: log.ai_response,
            sender: "bot",
            timestamp: log.timestamp,
            _id: log._id + "_bot",
          },
        ]);
        // Sort by timestamp
        chatMessages.sort(
          (a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        );
        setMessage(chatMessages);
      } catch (err) {
        console.error("Error fetching messages:", err);
      }
      setIsLoading(false);
    };
    fetchMessages();
  }, []);

  async function handleSend() {
    if (!input?.trim()) return;
    const newUserMessage = { text: input, sender: "user" };
    setMessage((prev) => [...prev, newUserMessage]);
    setIsLoading(true);
    setInput("");

    try {
      const res = await fetch(`${import.meta.env.VITE_SERVER_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await res.json();

      // Add bot response
      const newBotMessage = { text: data.response, sender: "bot" };
      setMessage((prev) => [...prev, newBotMessage]);
    } catch (error) {
      const errMsg = {
        text: "Failed to get response. Please try again.",
        sender: "bot",
      };
      setMessage((prev) => [...prev, errMsg]);
      console.error(error);
    } finally {
      setIsLoading(false);
    }
    // fetchMessages();
  }

  // Scroll to bottom when messages change
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  //   function handleSend() {}

  return (
    <Paper
      elevation={2}
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        maxHeight: "calc(100vh - 30px)",
        backgroundColor: "var(--color-card)",
        color: "var(--color-text-primary)",
        padding: "1em",
      }}
    >
      <Box
        sx={{
          flexGrow: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 1,
          p: 2,
          backgroundColor: "var(--color-surface)",
        }}
      >
        {messages.map((msg, idx) => (
          <Box
            key={idx}
            sx={{
              display: "flex",
              flexDirection: "column",
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              alignItems: msg.sender === "user" ? "flex-end" : "flex-start",
            }}
          >
            {/* Message Bubble */}
            <Box
              sx={{
                bgcolor: msg.sender === "user" ? "#91e5ff" : "#f1f1f1",
                // color: msg.sender === 'user' ? 'white' : 'black',
                color: "black",
                px: 2,
                py: 1,
                borderRadius: 2,
                maxWidth: "75%",
              }}
            >
              {/* <Typography variant="body2">{msg.text}</Typography> */}
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            </Box>
          </Box>
        ))}
        <div ref={chatEndRef} />
      </Box>
      <Divider />
      {isLoading ? <LinearProgress sx={{ margin: 1, height: 10 }} /> : <></>}
      <Box
        sx={{
          display: "flex",
          gap: 1,
          mt: 1,
          p: 1,
        }}
      >
        <TextField
          fullWidth
          size="small"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
        />
        <IconButton color="primary" onClick={handleSend}>
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  );
};

export default ChatsPanel;
