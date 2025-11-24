import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("audio_service")


def extract_audio(input_path: str, output_path: str) -> bool:
    """
    Extract audio (as MP3) from a video using ffmpeg.
    Returns True if extraction succeeded, False otherwise.
    """

    logger.info(
        "Starting audio extraction...",
        extra={"input_path": input_path, "output_path": output_path},
    )

    input_path = str(input_path)
    output_path = str(output_path)

    # Ensure target directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # ffmpeg command
    command = [
        "ffmpeg",
        "-i", input_path,    # input video
        "-vn",               # disable video
        "-acodec", "mp3",    # convert to mp3
        output_path,
        "-y",                # overwrite output
    ]

    logger.info(
        "Running ffmpeg command",
        extra={"command": " ".join(command)},
    )

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # ffmpeg writes most logs to stderr — that's normal.
        logger.info(
            "FFmpeg stderr output",
            extra={"stderr": result.stderr[:500]},  # limit log size
        )

        if result.returncode != 0:
            logger.error(
                "FFmpeg failed with non-zero exit code",
                extra={"returncode": result.returncode, "stderr": result.stderr},
            )
            return False

        logger.info(
            "Audio extraction succeeded",
            extra={"output_path": output_path},
        )

        return True

    except Exception as exc:
        logger.exception(
            "Exception occurred while running ffmpeg",
            extra={"error": str(exc)},
        )
        return False
