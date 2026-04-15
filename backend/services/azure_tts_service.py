# services/azure_tts_service.py
import os
import base64
import logging
import azure.cognitiveservices.speech as speechsdk

logger = logging.getLogger(__name__)

def azure_t2speech_streaming(text: str):
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    voice = os.getenv("AZURE_SPEECH_VOICE", "es-ES-ElviraNeural")

    if not key or not region:
        raise RuntimeError("Faltan variables AZURE_SPEECH_KEY / AZURE_SPEECH_REGION")

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    # Asegurar salida en MP3 para reproducir fácilmente en frontend
    try:
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
    except Exception as e:
        logger.debug(f"No se pudo establecer formato MP3: {e}")
    # Habilitar animación de visemas (necesario para evento en algunos entornos)
    try:
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_VisemeAnimationEnabled, "true"
        )
    except Exception as e:
        logger.debug(f"No se pudo establecer propiedad VisemeAnimationEnabled: {e}")

    # Crear sintetizador sin audio_config (obtiene bytes en memoria y evita requerir altavoz)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    raw_visemes = []
    def on_viseme(evt):
        raw_visemes.append({
            "time": getattr(evt, "audio_offset", 0) / 10_000_000,  # 100ns -> s
            "value": getattr(evt, "viseme_id", None)
        })
    try:
        synthesizer.viseme_received.connect(on_viseme)
    except Exception as e:
        logger.warning(f"No se pudo adjuntar viseme_received: {e}")

    res = synthesizer.speak_text_async(text).get()
    if res.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"Síntesis falló: {res.reason}")

    audio_bytes = res.audio_data  # bytes PCM según formato por defecto

    # Construir mouthCues con estructura (start, end, value)
    mouth_cues = []
    for i, v in enumerate(raw_visemes):
        start = v["time"]
        end = raw_visemes[i+1]["time"] if i + 1 < len(raw_visemes) else start + 0.15
        value = _map_viseme_id(v.get("value"))
        mouth_cues.append({"start": start, "end": end, "value": value})

    duration = mouth_cues[-1]["end"] if mouth_cues else 0.0
    lipsync = {
        "metadata": {"soundFile": "azure_stream", "duration": duration},
        "mouthCues": mouth_cues
    }

    return audio_bytes, lipsync


def _map_viseme_id(raw_id):
    """Traduce ID numérico de azure a etiqueta compatible con mapping del frontend.
    Tabla heurística: ajustar si se dispone de documentación precisa.
    """
    mapping = {
        0: 'sil',
        1: 'p',
        2: 't',
        3: 'k',
        4: 'f',
        5: 'T',
        6: 's',
        7: 'a',
        8: 'e',
        9: 'i',
        10: 'o',
        11: 'u',
        12: 'r',
    }
    return mapping.get(raw_id, 'sil')
