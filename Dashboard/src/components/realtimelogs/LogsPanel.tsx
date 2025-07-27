import React, { useEffect, useState, useRef } from 'react';
import {
  Card,
  List,
  ListItem,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  TextField,
  Stack,
  Chip,
  Box
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const LogsPanel = () => {
  const listRef = useRef<HTMLUListElement | null>(null);

  const [logs, setLogs] = useState<any[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<any[]>([]);

  // Filter states
  const [actorFilter, setActorFilter] = useState<string>('');
  const [endpointFilter, setEndpointFilter] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('');
  const [endTime, setEndTime] = useState<string>('');

  // Unique dropdown options
  const [actors, setActors] = useState<string[]>([]);
  const [endpoints, setEndpoints] = useState<string[]>([]);

  const [isQuery, setIsQuery] = useState<boolean>(true);

  const POOL_INTERVAL = 5;

  // useEffect(()=>{
  //   fetchActionLogs()
  // },[])

  useEffect(() => {
    if (!isQuery) return;

    const interval = setInterval(() => {
      fetchActionLogs();
    }, POOL_INTERVAL*1000); // 2 seconds

    return () => clearInterval(interval);
  }, [isQuery, actorFilter, endpointFilter, startTime, endTime]);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }, [filteredLogs]); // triggers every time filteredLogs changes


  // useEffect(() => {
  //   const eventSource = new EventSource('http://localhost:8002/logs');

  //   eventSource.onmessage = (event) => {
  //     try {
  //       const parsed = JSON.parse(event.data);
  //       const newLogs = Array.isArray(parsed) ? parsed : [parsed];

  //       console.log(newLogs)

  //       setLogs((prevLogs) => [
  //         ...newLogs.map((l) => ({ ...l, isNew: true })),
  //         ...prevLogs
  //       ]);
  //     } catch (err) {
  //       console.error('Failed to parse log:', err, event.data);
  //     }
  //   };

  //   eventSource.onerror = (err) => {
  //     console.error('SSE connection error:', err);
  //     eventSource.close();
  //   };

  //   return () => eventSource.close();
  // }, []);


  useEffect(() => {
    if (logs.some((l) => l.isNew)) {
      const timer = setTimeout(() => {
        setLogs((prev) =>
          prev.map((log) => ({ ...log, isNew: false }))
        );
      }, 1500); // matches the animation duration
      return () => clearTimeout(timer);
    }
  }, [logs]);


  // Update filter options dynamically
  useEffect(() => {
    setActors(Array.from(new Set(logs.map((l) => l.actor))));
    setEndpoints(Array.from(new Set(logs.map((l) => l.endpoint))));
  }, [logs]);

  // Apply filters
  useEffect(() => {
    let fl = [...logs];
    if (actorFilter) fl = fl.filter((l) => l.actor === actorFilter);
    if (endpointFilter) fl = fl.filter((l) => l.endpoint === endpointFilter);
    if (startTime)
      fl = fl.filter((l) => new Date(l.timestamp) >= new Date(startTime));
    if (endTime)
      fl = fl.filter((l) => new Date(l.timestamp) <= new Date(endTime));
    setFilteredLogs(fl);
  }, [logs, actorFilter, endpointFilter, startTime, endTime]);


  async function fetchActionLogs() {
    const query: any = {};
    if (actorFilter) query.actor = actorFilter;
    if (endpointFilter) query.endpoint = endpointFilter;
    if (startTime && endTime) query.timestamp = {
      ...(startTime && { "$gte": startTime }),
      ...(endTime && { "$lte": endTime })
    };

    const url = `http://localhost:8002/api/action_logs?query=${encodeURIComponent(JSON.stringify(query))}&limit=100`;
    try {
      const res = await fetch(url);
      const data = await res.json();
      // Extract the array from the response object
      setFilteredLogs(Array.isArray(data.action_logs) ? data.action_logs : []);
    } catch (err) {
      console.error("Failed to fetch action logs:", err);
      setFilteredLogs([]);
    }
  }

  function runQuery() {
    setIsQuery(true);
    fetchActionLogs();
  }

  function clearQuery() {
    setIsQuery(false);
    setFilteredLogs([]);
  }

  return (
    <div>
      <Card
        variant="outlined"
        sx={{
          backgroundColor: 'var(--color-card)',
          color: 'var(--color-text-primary)',
          padding: '1em',
          maxHeight: '500px',
          // overflowY: 'auto',
          border: '1px solid var(--color-divider)',
        }}
      >
        {/* <Typography variant="h6" gutterBottom  className="logs-title">
          Logs Panel
        </Typography> */}

        {/* Filters */}
        <Stack direction="row" spacing={2} sx={{ mb: 2, mt: 2 }}>
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel sx={{ color: 'var(--color-text-secondary)' }}>
              Actor
            </InputLabel>
            <Select
              value={actorFilter}
              onChange={(e) => setActorFilter(e.target.value)}
              sx={{
                color: 'var(--color-text-primary)',
                backgroundColor: 'var(--color-surface)',
                '& .MuiSvgIcon-root': { color: 'var(--color-primary-accent)' },
              }}
            >
              <MenuItem value="">All</MenuItem>
              {actors.map((actor) => (
                <MenuItem key={actor} value={actor}>
                  {actor}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel sx={{ color: 'var(--color-text-secondary)' }}>
              Endpoint
            </InputLabel>
            <Select
              value={endpointFilter}
              onChange={(e) => setEndpointFilter(e.target.value)}
              sx={{
                color: 'var(--color-text-primary)',
                backgroundColor: 'var(--color-surface)',
                '& .MuiSvgIcon-root': { color: 'var(--color-primary-accent)' },
              }}
            >
              <MenuItem value="">All</MenuItem>
              {endpoints.map((ep) => (
                <MenuItem key={ep} value={ep}>
                  {ep}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Start Time"
            type="datetime-local"
            InputLabelProps={{ shrink: true }}
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            sx={{
              backgroundColor: 'var(--color-surface)',
              input: { color: 'var(--color-text-primary)' },
              label: { color: 'var(--color-text-secondary)' },
            }}
          />

          <TextField
            label="End Time"
            type="datetime-local"
            InputLabelProps={{ shrink: true }}
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            sx={{
              backgroundColor: 'var(--color-surface)',
              input: { color: 'var(--color-text-primary)' },
              label: { color: 'var(--color-text-secondary)' },
            }}
          />

          <Button
            variant="contained"
            sx={{ backgroundColor: 'var(--color-primary-accent)', color: '#000' }}
            onClick={runQuery}
          >
            Run Query
          </Button>

          <Button
            variant="outlined"
            sx={{ borderColor: 'var(--color-warning)', color: 'var(--color-warning)' }}
            onClick={clearQuery}
          >
            Clear Query
          </Button>

          {
            isQuery ? <>
              <Button
                variant="outlined"
                sx={{
                  borderColor: 'var(--color-primary-accent)',
                  color: 'var(--color-primary-accent)',
                }}
                onClick={fetchActionLogs}
              >
                Refresh
              </Button>
            </> : <></>
          }
        </Stack>

        <List style={{ height: "50vh", overflowY: "auto" }} ref={listRef}>
          {filteredLogs.map((log, index) => (
            <ListItem
              // className="log-item"
              className={`log-item ${log.isNew ? 'new-log' : ''}`}
              key={`${log.timestamp}-${index}`}
              sx={{
                display: 'block',
                borderBottom: '1px solid var(--color-divider)',
                borderRadius: 1,
                '&:hover': { backgroundColor: 'var(--color-hover)' },
              }}
            >
              <Accordion
                sx={{
                  backgroundColor: 'transparent',
                  color: 'var(--color-text-primary)',
                  boxShadow: 'none',
                }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  sx={{
                    minHeight: '32px',
                    padding: '0 8px',               // Reduce horizontal padding
                    '& .MuiAccordionSummary-content': {
                      margin: '4px 0',
                    },
                    '&.Mui-expanded': {
                      minHeight: '32px',
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body2">
                      [{new Date(log.timestamp.replace(/(\.\d{3})\d+/, "$1")).toLocaleString()}]
                    </Typography>
                    <Chip label={(log.actor ? log.actor.toUpperCase() : "UNKNOWN")} color="primary" size="small" />
                    <Chip
                      label={`${log.method ? log.method.toUpperCase() : "METHOD"}:${log.status ?? "?"}`}
                      color={log.status === 200 ? "success" : "error"}
                      size="small"
                    />
                    <Typography variant="body2" component="span">
                      {log.endpoint}
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Accordion>
                    <AccordionSummary
                      expandIcon={<ExpandMoreIcon />}
                      sx={{
                        minHeight: '32px',             // Reduce minimum height
                        '& .MuiAccordionSummary-content': {
                          margin: '4px 0',             // Reduce vertical margin
                        },
                        '&.Mui-expanded': {
                          minHeight: '32px',           // Keep height small when expanded
                        }
                      }}
                    >
                      <Typography style={{ color: 'var(--color-light)' }}>Payload</Typography>
                    </AccordionSummary>
                    <AccordionDetails style={{ background: 'var(--color-surface)' }} sx={{ m: 1, p: 0 }}>
                      <pre style={{ color: 'var(--color-light)', padding: "0.5em" }}>
                        {JSON.stringify(log.payload, null, 2)}
                      </pre>
                    </AccordionDetails>
                  </Accordion>

                  <Accordion>
                    <AccordionSummary
                      expandIcon={<ExpandMoreIcon />}
                      sx={{
                        minHeight: '32px',             // Reduce minimum height
                        '& .MuiAccordionSummary-content': {
                          margin: '4px 0',             // Reduce vertical margin
                        },
                        '&.Mui-expanded': {
                          minHeight: '32px',           // Keep height small when expanded
                        }
                      }}
                    >
                      <Typography style={{ color: 'var(--color-light)' }}>Response</Typography>
                    </AccordionSummary>
                    <AccordionDetails style={{ background: 'var(--color-surface)' }} sx={{ m: 1, p: 0 }}>
                      <pre style={{ color: 'var(--color-light)', padding: "0.5em" }}>
                        {JSON.stringify(log.response, null, 2)}
                      </pre>
                    </AccordionDetails>
                  </Accordion>
                </AccordionDetails>
              </Accordion>
            </ListItem>
          ))}
        </List>
      </Card>
    </div>
  );
};

export default LogsPanel;
