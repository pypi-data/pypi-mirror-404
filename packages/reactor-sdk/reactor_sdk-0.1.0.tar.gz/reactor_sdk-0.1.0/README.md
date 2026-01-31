# Reactor Python SDK

[![PyPI version](https://img.shields.io/pypi/v/reactor-sdk)](https://pypi.org/project/reactor-sdk/)
[![PyPI downloads](https://img.shields.io/pypi/dm/reactor-sdk)](https://pypi.org/project/reactor-sdk/)
[![build](https://img.shields.io/github/actions/workflow/status/reactor-team/py-sdk/ci.yml?branch=main)](https://github.com/reactor-team/py-sdk/actions)
[![license](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

Python SDK for Reactor - Real-time AI video streaming platform.

## Installation

```bash
pip install reactor-sdk
```

## Quick Start

```python
import asyncio
from reactor_sdk import Reactor, ReactorStatus

async def main():
    # Create a Reactor instance with your API key
    reactor = Reactor(
        model_name="my-model",
        api_key="REACTOR_API_KEY",  # SDK automatically fetches JWT token
    )
    
    # Use decorators for clean event handling
    @reactor.on_frame
    def handle_frame(frame):
        print(f"Received frame: {frame.shape}")
    
    @reactor.on_message
    def handle_message(msg):
        print(f"Message: {msg}")
    
    @reactor.on_status(ReactorStatus.READY)
    def handle_ready(status):
        print("Connected and ready!")
    
    @reactor.on_error
    def handle_error(error):
        print(f"Error: {error}")
    
    # Connect to the model (JWT token is fetched automatically)
    await reactor.connect()
    
    # Send commands
    await reactor.send_command("setParameter", {"value": 0.5})
    
    # Keep running
    try:
        while reactor.get_status() == ReactorStatus.READY:
            await asyncio.sleep(0.1)
    finally:
        await reactor.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- **WebRTC video streaming** via aiortc
- **Event-driven API** matching the JavaScript SDK
- **Frame callbacks** for single-frame access
- **Video input** support for sending video to models
- **Local development** mode for testing
- **Full type hints** for IDE support

## API Reference

### Reactor

The main class for connecting to Reactor models.

```python
from reactor_sdk import Reactor

# Production usage with API key
reactor = Reactor(
    model_name="my-model",
    api_key="REACTOR_API_KEY",  # SDK fetches JWT automatically
)

# Local development (no API key needed)
reactor = Reactor(
    model_name="my-model",
    local=True,
)
```

The `Reactor` type can also be used for type annotations:

```python
from reactor_sdk import Reactor

def process_reactor(reactor: Reactor) -> None:
    # reactor has full type hints for all methods
    pass
```

#### Methods

- `await reactor.connect()` - Connect to the model (fetches JWT automatically if API key provided)
- `await reactor.disconnect(recoverable: bool = False)` - Disconnect
- `await reactor.reconnect()` - Reconnect to existing session
- `await reactor.send_command(command: str, data: dict)` - Send a command
- `await reactor.publish_track(track: MediaStreamTrack)` - Send video to model
- `await reactor.unpublish_track()` - Stop sending video
- `reactor.get_status()` - Get current status
- `reactor.get_session_id()` - Get session ID
- `reactor.set_frame_callback(callback)` - Set frame callback

#### Decorators

Use decorators for clean event handling:

```python
@reactor.on_frame
def handle_frame(frame):
    """Called for each video frame (numpy array H,W,3)."""
    pass

@reactor.on_message
def handle_message(message):
    """Called for each message from the model."""
    pass

@reactor.on_status
def handle_any_status(status):
    """Called for all status changes."""
    pass

@reactor.on_status(ReactorStatus.READY)
def handle_ready(status):
    """Called only when status becomes READY."""
    pass

@reactor.on_status([ReactorStatus.READY, ReactorStatus.CONNECTING])
def handle_active(status):
    """Called when status is READY or CONNECTING."""
    pass

@reactor.on_error
def handle_error(error):
    """Called when an error occurs."""
    pass

@reactor.on_stream
def handle_stream(track):
    """Called when video stream/track changes."""
    pass
```

#### Events (alternative to decorators)

- `status_changed` - Status changed (disconnected, connecting, ready)
- `session_id_changed` - Session ID changed
- `new_message` - Message received from model
- `stream_changed` - Video stream changed
- `error` - Error occurred

## Examples

See the `examples/` directory for complete examples:

- `pygame_app/` - Pygame application with dynamic UI controls
- `rtmp_app/` - Stream Reactor video to RTMP servers (Twitch, YouTube, etc.)

## License

MIT License - Copyright (c) 2025 Reactor Technologies, Inc.
