# log_manager.py
import asyncio
import json

# Configuration
MAX_BUFFER = 1000
FLUSH_INTERVAL_MS = 500  # in ms

# State
log_buffer = []
shutdown_flag = False


def push_log(log):
    """Add a log to the buffer with max length control."""
    global log_buffer
    log_buffer.append(log)
    if len(log_buffer) > MAX_BUFFER:
        log_buffer.pop(0)


async def sse_stream(request):
    """Yield logs to clients using SSE (Server-Sent Events)."""
    last_index = 0
    while not shutdown_flag:
        if last_index < len(log_buffer):
            new_logs = log_buffer[last_index:]
            last_index = len(log_buffer)
            yield f"data: {json.dumps(new_logs)}\n\n"
        else:
            # Heartbeat to keep the connection alive
            yield ":\n\n"

        await asyncio.sleep(FLUSH_INTERVAL_MS / 1000)
        if await request.is_disconnected():
            break


def stop_stream():
    """Mark shutdown to stop all streams."""
    global shutdown_flag
    shutdown_flag = True
