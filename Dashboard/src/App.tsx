import { useState } from 'react'
import './App.css'
import {Grid} from '@mui/material'

import ChartsPanel from './components/charts/ChartsPanel'
import ChatsPanel from './components/chats/ChatsPanel'
import LogsPanel from './components/realtimelogs/LogsPanel'

function App() {

  return (
    <>
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
