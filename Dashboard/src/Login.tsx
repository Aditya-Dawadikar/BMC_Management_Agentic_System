import React, { useState } from "react";
import { Box, Button, TextField, Typography, Paper } from "@mui/material";
import { useAuth } from "./AuthContext";

export default function Login() {
  const { login } = useAuth();
  const [user_id, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id, password }),
      });
      if (res.ok) {
        login(user_id);
      } else {
        setError("Invalid credentials");
      }
    } catch {
      setError("Server error");
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
      <Paper sx={{ p: 4, minWidth: 320 }}>
        <Typography variant="h6" mb={2}>Login</Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="User ID"
            value={user_id}
            onChange={e => setUserId(e.target.value)}
            fullWidth
            margin="normal"
            required
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            fullWidth
            margin="normal"
            required
          />
          {error && <Typography color="error">{error}</Typography>}
          <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }}>
            Login
          </Button>
        </form>
      </Paper>
    </Box>
  );
}