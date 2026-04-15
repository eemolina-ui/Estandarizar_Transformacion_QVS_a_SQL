import base64
import json
import logging

#logger = logging.get#logger(__name__)

def read_json_transcript(file):
    #logger.info(f"Reading JSON transcript from {file}")
    try:
        with open(file, 'r') as f:
            data = json.load(f)
        #logger.info(f"Successfully read JSON transcript from {file}")
        return data
    except Exception as e:
        #logger.error(f"Error reading JSON transcript from {file}: {str(e)}")
        raise

def audio_file_to_base64(file):
    #logger.info(f"Converting audio file to base64: {file}")
    try:
        with open(file, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        #logger.info(f"Successfully converted audio file to base64: {file}")
        return encoded
    except Exception as e:
        #logger.error(f"Error converting audio file to base64 {file}: {str(e)}")
        raise