import { useState } from 'react'
import './App.css'
import { Grid, AppBar, Toolbar, Typography } from '@mui/material';

import ChartsPanel from './components/charts/ChartsPanel'
import ChatsPanel from './components/chats/ChatsPanel'
import LogsPanel from './components/realtimelogs/LogsPanel'

function App() {

  return (
    <>
      <AppBar position="static" sx={{ backgroundColor: 'var(--color-primary-accent)' }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, color: '#000' }}>
            Axiado Observability Platform
          </Typography>
        </Toolbar>
      </AppBar>
      <Grid container spacing={2}
        sx={{
          margin: "1em"
        }}
      >
        <Grid size={4}>
          <ChatsPanel/>
        </Grid>
        <Grid size={8}>
          <ChartsPanel/>
          <br/>
          <LogsPanel/>
        </Grid>
      </Grid>
    </>
  )
}

export default App
