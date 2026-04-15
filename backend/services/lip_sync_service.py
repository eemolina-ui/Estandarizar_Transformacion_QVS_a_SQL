import logging
import subprocess

#logger = logging.get#logger(__name__)

def exec_command(command):
    #logger.info(f"Executing command: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        #logger.error(f"Command failed: {stderr.decode()}")
        raise Exception(f"Command failed: {stderr.decode()}")
    #logger.info(f"Command executed successfully: {stdout.decode()}")
    return stdout.decode()

async def lip_sync_message(message_index: int):
    #logger.info(f"Starting lip sync process for message {message_index}")
    try:
        #logger.info(f"Converting audio for message {message_index}")
        exec_command(f"ffmpeg -y -i audios/message_{message_index}.mp3 audios/message_{message_index}.wav")
        #logger.info(f"Audio conversion complete for message {message_index}")
        
        #logger.info(f"Starting Rhubarb lip sync for message {message_index}")
        exec_command(f'rhubarb -f json -o audios/message_{message_index}.json audios/message_{message_index}.wav -r phonetic')
        #logger.info(f"Lip sync complete for message {message_index}")
    except Exception as e:
        #logger.error(f"Error in lip sync process: {str(e)}")
        raise