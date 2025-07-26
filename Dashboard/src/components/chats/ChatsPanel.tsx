import React from "react";
import { Card, Box, Paper, Divider } from "@mui/material";
import { Typography } from "@mui/material";
import { useState } from "react";
import { LinearProgress } from "@mui/material";
import { TextField } from "@mui/material";
import { IconButton } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";

const ChatsPanel = () => {
  const [messages, setMessage] = useState<Array<any>>([
    {
      text: "Hello! how can I help you today?",
      sender: "bot",
    },
    {
      text: "Help me analyse the device status",
      sender: "user",
    },
  ]);
  const [input, setInput] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSend() {
    if (!input?.trim()) return;

    // Add user message to chat
    const newUserMessage = { text: input, sender: "user" };
    setMessage((prev) => [...prev, newUserMessage]);
    setIsLoading(true);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/chat", {
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
  }

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
              <Typography variant="body2">{msg.text}</Typography>
            </Box>
          </Box>
        ))}
      </Box>
      <Divider />
      {isLoading ? <LinearProgress sx={{ margin: 1, height: 10 }} /> : <></>}
      <Box
        sx={{
          display: "flex",
          gap: 1,
          mt: 1,
          backgroundColor: "var(--color-light)",
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
