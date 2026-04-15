import boto3
from concurrent.futures import ThreadPoolExecutor
import base64
import logging 

from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())

#logger = logging.get#logger(__name__)

def synthesize_audio(polly_client, input_text, voice_id='Mia'):
    return polly_client.synthesize_speech(
        OutputFormat='mp3',
        VoiceId=voice_id,
        TextType='text',
        Text=input_text,
        Engine='neural'
    )['AudioStream']

import json

def synthesize_speech_marks(polly_client, input_text, voice_id='Mia'):
    # Inicializar la estructura de salida
    result = {
        "metadata": {
            "soundFile": "sound_file_path",
            "duration": 0
        },
        "mouthCues": []
    }

    # Obtener la respuesta de Polly en streaming
    response = polly_client.synthesize_speech(
        OutputFormat='json',
        VoiceId=voice_id,
        TextType='text',
        Text=input_text,
        SpeechMarkTypes=['viseme']# Polly solo está disponible en esta región
    )

    # Procesar el stream de visemas
    audio_stream = response['AudioStream']
    previous_time = 0  # Para calcular el tiempo final de cada visema
    error_events = []  # Para almacenar eventos de error
    for chunk in audio_stream:
        # Dividir los mensajes JSON si hay múltiples en el mismo chunk
        chunk_str = chunk.decode('utf-8').strip()
        if chunk_str:
            viseme_events = chunk_str.split("\n")
            for event in viseme_events:
                try:
                    # Parsear el JSON del visema
                    viseme_data = json.loads(event)
                    if viseme_data['type'] == 'viseme':
                        # Calcular el inicio y fin en segundos
                        start_time = previous_time
                        end_time = viseme_data['time'] / 1000.0  

                        # Agregar el nuevo visema
                        result["mouthCues"].append({
                            "start": start_time,
                            "end": end_time,  # Se ajustará con el siguiente visema
                            "value": viseme_data["value"]
                        })
                        previous_time = end_time
                        
                except json.JSONDecodeError:
                    # Manejo de error si un chunk no puede ser decodificado
                    error_events.append(event)
                    if len(error_events)==2:
                        try:                            
                            viseme_data = json.loads(''.join(error_events))

                            if viseme_data['type'] == 'viseme':
                                # Calcular el inicio y fin en segundos
                                start_time = previous_time
                                end_time = viseme_data['time'] / 1000.0 
                                # Agregar el nuevo visema
                                result["mouthCues"].append({
                                    "start": start_time,
                                    "end": end_time,  # Se ajustará con el siguiente visema
                                    "value": viseme_data["value"]
                                })
                                previous_time = end_time
                            error_events = []
                        except json.JSONDecodeError:
                            print("Error decoding new joined event: ", ''.join(error_events))
                            error_events = []
    if len(result["mouthCues"]) > 0:
        # actualizar duration en metadata
        result["metadata"]["duration"] = result["mouthCues"][-1]["end"]

    return result

import io

def handle_audio_chunk(audio_chunk):
    # Convertir el chunk de audio en un objeto BytesIO para manejar como un archivo
    audio_io = io.BytesIO(audio_chunk)

    # Imprimir detalles sobre el tamaño del chunk y contenido (por ejemplo, los primeros 100 bytes)
    chunk_size = len(audio_chunk)
    print(f"Received audio chunk of size: {chunk_size} bytes")

    # Opcional: Leer y mostrar los primeros 100 bytes del chunk para depuración
    preview = audio_io.read(100)  # Lee los primeros 100 bytes del chunk
    print(f"Preview of audio chunk: {preview}")

    # Si quieres, puedes guardar el chunk en un archivo para escuchar el progreso
    with open('output_audio_chunk.wav', 'ab') as f:
        f.write(audio_chunk)
        print("Chunk written to output_audio_chunk.wav")

def polly_t2speech_streaming(input_text):
    polly_client = boto3.client('polly' , region_name='us-east-1')

    with ThreadPoolExecutor(max_workers=2) as executor:
        audio_future = executor.submit(synthesize_audio, polly_client, input_text)
        marks_future = executor.submit(synthesize_speech_marks, polly_client, input_text)

        audio_stream = audio_future.result()
        speech_marks = marks_future.result()
    return audio_stream,speech_marks

