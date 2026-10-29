"""Speech-to-text engines under test. Each engine: name, supports(lang), transcribe(wav, lang) -> str.

Engines import their SDKs lazily so you only need to install the ones you test:
    uv sync --extra gemini --extra azure --extra mms
"""

import os
import time
from pathlib import Path

from . import LANG_NAMES


class GeminiSTT:
    """Gemini audio understanding. Gets NO language hint (only "South African languages"),
    which is the realistic case for Malume: it won't know in advance what you'll speak."""

    name = "gemini"
    PROMPT = (
        "Transcribe this audio exactly as spoken. The speaker is South African and may use "
        "isiZulu, Setswana, Xitsonga, English, or a mix within one sentence. Write African-language "
        "words in standard orthography and English words in English spelling. Do not translate. "
        "Output only the transcript."
    )

    def __init__(self):
        from google import genai

        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
        self.delay = float(os.environ.get("GEMINI_DELAY", "4"))

    def supports(self, lang: str) -> bool:
        return True

    def transcribe(self, wav: Path, lang: str) -> str:
        from google.genai import types

        audio = types.Part.from_bytes(data=wav.read_bytes(), mime_type="audio/wav")
        for attempt in range(4):
            try:
                resp = self.client.models.generate_content(model=self.model, contents=[audio, self.PROMPT])
                time.sleep(self.delay)
                return (resp.text or "").strip()
            except Exception as e:  # free-tier rate limit -> back off and retry
                if "429" not in str(e) or attempt == 3:
                    raise
                time.sleep(30 * (attempt + 1))
        return ""


class AzureSTT:
    """Azure Speech (free F0 tier). Gets the language code as a hint.
    Only languages listed in LOCALES are attempted; add more if Azure adds them."""

    name = "azure"
    LOCALES = {"en": "en-ZA", "zu": "zu-ZA"}

    def __init__(self):
        import azure.cognitiveservices.speech as speechsdk

        self.sdk = speechsdk
        self.key = os.environ["AZURE_SPEECH_KEY"]
        self.region = os.environ.get("AZURE_SPEECH_REGION", "southafricanorth")

    def supports(self, lang: str) -> bool:
        return lang in self.LOCALES

    def transcribe(self, wav: Path, lang: str) -> str:
        sdk = self.sdk
        cfg = sdk.SpeechConfig(subscription=self.key, region=self.region)
        cfg.speech_recognition_language = self.LOCALES[lang]
        recognizer = sdk.SpeechRecognizer(speech_config=cfg, audio_config=sdk.audio.AudioConfig(filename=str(wav)))
        result = recognizer.recognize_once()
        if result.reason == sdk.ResultReason.RecognizedSpeech:
            return result.text
        if result.reason == sdk.ResultReason.NoMatch:
            return ""
        raise RuntimeError(f"Azure canceled: {result.cancellation_details.error_details}")


class MmsSTT:
    """Meta MMS-1B (open model, runs locally on CPU). Needs the language code as a hint.
    First run downloads ~4 GB."""

    name = "mms"
    CODES = {"en": "eng", "zu": "zul", "tn": "tsn", "ts": "tso"}
    MODEL_ID = "facebook/mms-1b-all"

    def __init__(self):
        import torch
        from transformers import AutoProcessor, Wav2Vec2ForCTC

        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(self.MODEL_ID)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.MODEL_ID)
        self.loaded_lang = None

    def supports(self, lang: str) -> bool:
        return lang in self.CODES

    def transcribe(self, wav: Path, lang: str) -> str:
        import soundfile

        if self.loaded_lang != lang:
            self.processor.tokenizer.set_target_lang(self.CODES[lang])
            self.model.load_adapter(self.CODES[lang])
            self.loaded_lang = lang
        audio, sr = soundfile.read(str(wav), dtype="float32")
        inputs = self.processor(audio, sampling_rate=sr, return_tensors="pt")
        with self.torch.no_grad():
            logits = self.model(**inputs).logits
        return self.processor.decode(self.torch.argmax(logits, dim=-1)[0])


ENGINES = {cls.name: cls for cls in (GeminiSTT, AzureSTT, MmsSTT)}
assert set(MmsSTT.CODES) == set(LANG_NAMES)
