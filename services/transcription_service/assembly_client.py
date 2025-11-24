import requests
import time
from logger_config import logger

class AssemblyAIClient:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("AssemblyAI API Key is missing")
        
        self.base_url = "https://api.assemblyai.com/v2"
        self.headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }

    def upload_file(self, file_path):
        """
        Uploads a local file to AssemblyAI servers.
        This is necessary because AssemblyAI cannot access our local MinIO.
        Returns the upload_url.
        """
        logger.info(f"Uploading file to AssemblyAI: {file_path}")
        
        def read_file(filename, chunk_size=5242880):
            with open(filename, 'rb') as _file:
                while True:
                    data = _file.read(chunk_size)
                    if not data:
                        break
                    yield data

        try:
            response = requests.post(
                f"{self.base_url}/upload",
                headers=self.headers,
                data=read_file(file_path)
            )
            response.raise_for_status()
            upload_url = response.json()["upload_url"]
            return upload_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to AssemblyAI: {e}")
            raise

    def transcribe(self, audio_url):
        """
        Starts the transcription job.
        Enables Speaker Diarization to distinguish between speakers.
        """
        logger.info("Starting transcription job...")
        
        json_data = {
            "audio_url": audio_url,
            "speaker_labels": True,  # <--- Critical for identifying Therapist vs Patient
            "language_code": "en"    # Assuming English for now
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/transcript",
                json=json_data,
                headers=self.headers
            )
            response.raise_for_status()
            transcript_id = response.json()["id"]
            logger.info(f"Transcription started. ID: {transcript_id}")
            return transcript_id
            
        except Exception as e:
            logger.error(f"Failed to start transcription: {e}")
            raise

    def get_result(self, transcript_id):
        """
        Polls the API every few seconds until the job is completed.
        Returns the full text and the list of utterances (speaker segments).
        """
        logger.info(f"Polling for results (ID: {transcript_id})...")
        
        while True:
            try:
                response = requests.get(
                    f"{self.base_url}/transcript/{transcript_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                status = data["status"]
                
                if status == "completed":
                    logger.info("Transcription completed successfully!")
                    # Return both the full text and the separated speaker lines (utterances)
                    return data["text"], data["utterances"]
                
                elif status == "error":
                    error_msg = data.get("error")
                    raise Exception(f"Transcription failed: {error_msg}")
                
                else:
                    # Still processing... wait 3 seconds and try again
                    time.sleep(3)

            except Exception as e:
                logger.error(f"Error while polling results: {e}")
                raise