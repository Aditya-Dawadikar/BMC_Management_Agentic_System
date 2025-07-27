import React, { useEffect, useState } from 'react'
import { Card } from '@mui/material'


const ChartsPanel = () => {

  const [dashboard, setDashboard] = useState(null)

  useEffect(() => {
    setDashboard(import.meta.env.VITE_GRAFANA_DASHBOARD)
  }, [])

  // console.log(import.meta.env.VITE_GRAFANA_DASHBOARD)
  return (
    <div>
      <Card variant='outlined'
        sx={{
          backgroundColor: 'var(--color-card)',
          color: 'var(--color-text-primary)',
          padding: "1em",
            height:"50vh"
        }}
      >
        {
          dashboard ? <iframe
            src={dashboard}
            width="100%"
            height="100%"
          >
          </iframe> : <></>
        }

      </Card>
    </div>
  )
}

export default ChartsPanel