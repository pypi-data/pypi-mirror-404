# RTMP Streaming Example

Stream Reactor video output to any RTMP server (Twitch, YouTube Live, etc.).

## Prerequisites

1. **Python 3.10+**
2. **ffmpeg** installed and available in PATH:
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt install ffmpeg

   # Windows - download from https://ffmpeg.org/download.html
   ```

## Installation

```bash
cd examples/rtmp_app
pip install -r requirements.txt
```

## Usage

### Local Development

```bash
python main.py --local --rtmp-url rtmp://localhost/live/stream
```

### Stream to Twitch

```bash
python main.py --api-key REACTOR_API_KEY --model your-model \
    --rtmp-url rtmp://live.twitch.tv/app/TWITCH_STREAM_KEY
```

### Stream to YouTube Live

```bash
python main.py --api-key REACTOR_API_KEY --model your-model \
    --rtmp-url rtmp://a.rtmp.youtube.com/live2/YOUTUBE_STREAM_KEY
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--model`, `-m` | Model name (default: example-model) |
| `--api-key`, `-k` | Reactor API key |
| `--local`, `-l` | Connect to local coordinator |
| `--rtmp-url`, `-r` | RTMP server URL (required) |
| `--rtmp-key` | Stream key (appended to URL) |
| `--width`, `-W` | Output width (default: 1280) |
| `--height`, `-H` | Output height (default: 720) |
| `--fps`, `-f` | Frame rate (default: 30) |
| `--verbose`, `-v` | Enable debug logging |

## How It Works

1. Connects to Reactor and receives video frames via WebRTC
2. Pipes frames to ffmpeg which encodes and streams to RTMP
3. Uses H.264 encoding with low-latency settings

## Extending This Example

This is a minimal example. For production use, consider:

- **Better resize**: Use OpenCV or PIL for higher quality scaling
- **Audio**: Add audio track from Reactor or external source
- **Reconnection**: Handle network issues gracefully
- **Monitoring**: Add health checks and metrics

```python
# Example: Add OpenCV resize for better quality
import cv2

def _send_frame(self, frame: NDArray[np.uint8]) -> None:
    if frame.shape[:2] != (self.height, self.width):
        frame = cv2.resize(frame, (self.width, self.height))
    # ... rest of send logic
```

## Troubleshooting

### ffmpeg not found
Make sure ffmpeg is installed and in your PATH:
```bash
ffmpeg -version
```

### Stream not appearing
- Check your stream key is correct
- Verify the RTMP URL format for your platform
- Check ffmpeg stderr output with `--verbose`

### High latency
Try reducing resolution or using faster encoding:
```bash
python main.py --local --rtmp-url ... --width 854 --height 480
```
