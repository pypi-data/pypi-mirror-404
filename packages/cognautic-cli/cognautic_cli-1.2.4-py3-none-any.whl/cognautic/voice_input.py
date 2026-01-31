"""
Lightweight voice input helper using SpeechRecognition.
"""
from typing import Optional
import os
import sys
import contextlib


@contextlib.contextmanager
def _suppress_stderr():
    """Temporarily redirect low-level C stderr (fd=2) to /dev/null to hide ALSA noise."""
    try:
        fd = sys.stderr.fileno()
    except Exception:
        # If stderr has no fileno, just yield
        yield
        return
    try:
        with open(os.devnull, 'w') as devnull:
            saved = os.dup(fd)
            try:
                os.dup2(devnull.fileno(), fd)
                yield
            finally:
                try:
                    os.dup2(saved, fd)
                finally:
                    os.close(saved)
    except Exception:
        # If anything goes wrong, don't block audio capture
        yield


def transcribe_once(timeout: float = 5.0, phrase_time_limit: float = 20.0, energy_threshold: Optional[int] = None) -> str:
    """
    Capture audio from the default microphone once and return a transcription.

    Args:
        timeout: Seconds to wait for the first phrase to start.
        phrase_time_limit: Max seconds for a single phrase.
        energy_threshold: Optional manual energy threshold.

    Returns:
        Transcribed text.

    Raises:
        RuntimeError: If SpeechRecognition or a microphone is unavailable, or transcription fails.
    """
    try:
        import speech_recognition as sr
    except Exception as e:
        raise RuntimeError("SpeechRecognition is not installed. Install with: pip install SpeechRecognition pyaudio") from e

    try:
        r = sr.Recognizer()
        if energy_threshold is not None:
            r.energy_threshold = energy_threshold
        # Suppress ALSA/libportaudio stderr chatter while opening the mic and listening
        with _suppress_stderr():
            with sr.Microphone() as source:
                try:
                    r.adjust_for_ambient_noise(source, duration=0.5)
                except Exception:
                    pass
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        try:
            # Uses Google Web Speech API (requires internet)
            text = r.recognize_google(audio)
        except sr.UnknownValueError as e:
            raise RuntimeError("Could not understand audio.") from e
        except sr.RequestError as e:
            raise RuntimeError("Speech service unavailable. Check internet connection.") from e
        return text.strip()
    except sr.WaitTimeoutError as e:
        raise RuntimeError("Listening timed out while waiting for phrase to start.") from e
    except OSError as e:
        raise RuntimeError("No default microphone found or microphone is busy.") from e
