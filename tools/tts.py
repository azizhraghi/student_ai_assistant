"""
Text-to-Speech Tool — converts AI responses to audio using gTTS.
Returns base64-encoded MP3 for browser playback.
"""

import base64
import io
import re


def text_to_speech(text: str, lang: str = "en") -> str:
    """
    Convert text to speech and return base64-encoded MP3.

    Args:
        text: Text to speak
        lang: Language code (en, fr, ar, etc.)

    Returns:
        Base64-encoded MP3 string for HTML audio embedding
    """
    try:
        from gtts import gTTS

        # Clean text — remove markdown symbols for cleaner speech
        clean = re.sub(r'\*+', '', text)          # bold/italic
        clean = re.sub(r'#+\s*', '', clean)        # headers
        clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean)  # links
        clean = re.sub(r'`+[^`]*`+', '', clean)    # code blocks
        clean = re.sub(r'[-•]\s+', '. ', clean)    # bullet points
        clean = re.sub(r'\n+', ' ', clean)          # newlines
        clean = clean.strip()

        # Truncate if too long (keep speech under ~45 seconds)
        max_chars = 600
        if len(clean) > max_chars:
            # Try to cut at sentence boundary
            truncated = clean[:max_chars]
            last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
            if last_period > max_chars // 2:
                clean = truncated[:last_period + 1] + " ... and more."
            else:
                clean = truncated + "..."

        tts = gTTS(text=clean, lang=lang, slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        audio_bytes = mp3_fp.read()
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return b64

    except Exception as e:
        return ""


def get_audio_html(b64_audio: str, autoplay: bool = True) -> str:
    """Generate HTML audio tag for browser playback."""
    if not b64_audio:
        return ""
    autoplay_attr = "autoplay" if autoplay else ""
    return f'''
    <audio {autoplay_attr} style="display:none">
        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
    </audio>
    '''
