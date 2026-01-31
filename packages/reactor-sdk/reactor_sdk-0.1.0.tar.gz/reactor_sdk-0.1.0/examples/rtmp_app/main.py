#!/usr/bin/env python3
"""
RTMP streaming example for the Reactor Python SDK.

A simple script that streams Reactor video output to an RTMP server.

Requirements:
    - ffmpeg must be installed and available in PATH

Usage:
    python main.py --local --rtmp-url rtmp://localhost/live/stream
    python main.py --api-key REACTOR_API_KEY --model your-model --rtmp-url rtmp://...
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import shutil
import subprocess
import sys
import warnings

import numpy as np
from numpy.typing import NDArray

# Add parent directories to path for development
sys.path.insert(0, str(__file__).rsplit("/", 3)[0] + "/src")

from reactor_sdk import Reactor, ReactorStatus
from reactor_sdk.types import ReactorError

# =============================================================================
# Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress noisy warnings
logging.getLogger("aiortc.codecs.vpx").setLevel(logging.ERROR)
logging.getLogger("aiortc.codecs.h264").setLevel(logging.ERROR)
logging.getLogger("aioice.ice").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# =============================================================================
# Parse arguments
# =============================================================================

parser = argparse.ArgumentParser(description="Stream Reactor video to RTMP")
parser.add_argument("--model", "-m", default="example-model", help="Model name")
parser.add_argument("--api-key", "-k", help="Reactor API key")
parser.add_argument("--local", "-l", action="store_true", help="Use local coordinator")
parser.add_argument("--rtmp-url", "-r", required=True, help="RTMP URL with stream key")
parser.add_argument("--fps", "-f", type=int, default=30, help="Frame rate")
parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
args = parser.parse_args()

if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

if not args.local and not args.api_key:
    logger.error("Either --local or --api-key must be provided")
    sys.exit(1)

if shutil.which("ffmpeg") is None:
    logger.error(
        "ffmpeg not found! Please install ffmpeg and ensure it's in your PATH.\n"
        "  Windows: winget install ffmpeg\n"
        "  macOS: brew install ffmpeg\n"
        "  Linux: apt install ffmpeg"
    )
    sys.exit(1)

# =============================================================================
# Initialize Reactor
# =============================================================================

reactor = Reactor(
    model_name=args.model,
    api_key=args.api_key,
    local=args.local,
)

# =============================================================================
# Event handlers (using decorators)
# =============================================================================

frames_sent = 0
streaming = False
ffmpeg_process: subprocess.Popen[bytes] | None = None
should_exit = False


@reactor.on_status
def on_status(status: ReactorStatus) -> None:
    logger.info(f"Status: {status.value}")


@reactor.on_message
def on_message(message: object) -> None:
    logger.info(f"Message: {message}")


@reactor.on_error
def on_error(error: ReactorError) -> None:
    logger.error(f"Error: {error}")


@reactor.on_stream
def on_stream(track: object) -> None:
    logger.info(f"Stream received: {track}")


@reactor.on_frame
def on_frame(frame: NDArray[np.uint8]) -> None:
    """Send each frame to ffmpeg for RTMP streaming."""
    global frames_sent, ffmpeg_process, streaming, should_exit

    if not streaming or should_exit:
        return

    # Start ffmpeg on first frame (now we know input dimensions)
    if ffmpeg_process is None:
        h, w = frame.shape[:2]
        try:
            ffmpeg_process = start_ffmpeg(w, h)
            logger.info(f"ffmpeg started ({w}x{h})")
        except Exception as e:
            logger.error(f"Failed to start ffmpeg: {e}")
            should_exit = True
            return

    if ffmpeg_process.stdin is None or ffmpeg_process.poll() is not None:
        return

    try:
        ffmpeg_process.stdin.write(frame.tobytes())
        frames_sent += 1
        if frames_sent % 100 == 0:
            logger.info(f"Frames sent: {frames_sent}")
    except (BrokenPipeError, OSError):
        pass  # ffmpeg exited, will be handled in main loop


# =============================================================================
# Main
# =============================================================================


def start_ffmpeg(input_width: int, input_height: int) -> subprocess.Popen[bytes]:
    """Start ffmpeg process for RTMP streaming."""
    logger.info(f"Starting ffmpeg -> {args.rtmp_url}")

    # Find ffmpeg executable (helps on Windows where PATH lookup can be tricky)
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise FileNotFoundError("ffmpeg executable not found in PATH")

    cmd = [
        ffmpeg_path, "-y",
        # Video input from stdin
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{input_width}x{input_height}",
        "-r", str(args.fps),
        "-i", "-",
        # Generate silent audio (required by YouTube/Twitch)
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        # Video encoding
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-pix_fmt", "yuv420p",
        "-g", "60",  # Keyframe every 2 seconds at 30fps
        "-b:v", "2500k",
        "-maxrate", "3000k",
        "-bufsize", "5000k",
        # Audio encoding
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        # Output
        "-shortest",  # Stop when video ends
        "-f", "flv",
        args.rtmp_url,
    ]

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


async def main() -> None:
    global ffmpeg_process, streaming

    logger.info("Connecting to Reactor...")
    await reactor.connect()
    logger.info("Connected! Waiting for first frame to start ffmpeg...")
    streaming = True

    try:
        while reactor.get_status() != ReactorStatus.DISCONNECTED and not should_exit:
            if ffmpeg_process is not None and ffmpeg_process.poll() is not None:
                if ffmpeg_process.stderr:
                    stderr = ffmpeg_process.stderr.read().decode()
                    if stderr:
                        logger.error(f"ffmpeg error:\n{stderr[-1000:]}")
                break
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass

    streaming = False
    logger.info("Stopping...")
    if ffmpeg_process is not None:
        if ffmpeg_process.stdin:
            ffmpeg_process.stdin.close()
        ffmpeg_process.terminate()
    await reactor.disconnect()
    logger.info(f"Done. Total frames sent: {frames_sent}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted")
