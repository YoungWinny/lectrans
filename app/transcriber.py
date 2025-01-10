import os
from vosk import Model, KaldiRecognizer, SetLogLevel
import wave
import json
import soundfile as sf
from pydub import AudioSegment
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set Vosk logging level to debug
SetLogLevel(0)

class TranscriptionService:
    def __init__(self, model_path="model/vosk-model-small-en-us-0.15"):
        logger.debug(f"Initializing TranscriptionService with model path: {model_path}")
        if not os.path.exists(model_path):
            raise ValueError(f"Model path {model_path} does not exist. Please download the Vosk model.")
        try:
            self.model = Model(model_path)
            logger.info("Vosk model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Vosk model: {str(e)}")
            raise

    def transcribe_file(self, audio_path, output_path):
        """Transcribe an audio file and save the result to a markdown file."""
        logger.info(f"Starting transcription of {audio_path}")
        try:
            # Convert audio to 16kHz mono WAV (Vosk requirement)
            logger.debug("Converting audio to correct format")
            audio = AudioSegment.from_file(audio_path)
            audio = audio.set_frame_rate(16000).set_channels(1)
            
            # Export as temporary WAV file
            temp_wav = audio_path + '.temp.wav'
            audio.export(temp_wav, format='wav')
            logger.debug(f"Temporary WAV file created: {temp_wav}")

            # Open the WAV file
            wf = wave.open(temp_wav, "rb")
            
            # Create recognizer
            rec = KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)

            # Process audio file
            transcription = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    print(rec.Result())
                    if result.get('text', ''):
                        logger.debug(f"Transcribed text: {result['text']}")
                        transcription.append(result['text'])

            # Get final result
            final = json.loads(rec.FinalResult())
            print(rec.FinalResult())
            if final.get('text', ''):
                logger.debug(f"Final transcribed text: {final['text']}")
                transcription.append(final['text'])

            # Clean up temporary file
            wf.close()
            os.remove(temp_wav)
            logger.debug("Temporary WAV file removed")

            # Write to markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('# Lecture Transcription\n\n')
                for text in transcription:
                    if text.strip():  # Only write non-empty lines
                        f.write(f"{text}\n\n")

            logger.info(f"Transcription completed and saved to {output_path}")
            
            # If no transcription was generated, log a warning
            if not transcription:
                logger.warning("No transcription was generated!")
                return False
                
            return True

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}", exc_info=True)
            raise

    def _format_timestamp(self, seconds):
        """Convert seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"