import whisper
import os
import torch

model = whisper.load_model("base")

def transcribe_audio(audio_path):
    print(f"Attempting to transcribe: {audio_path}")
    
    try:
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return None
        
        res = model.transcribe(audio_path)
        text = res["text"]
        
        transcript_file = os.path.splitext(audio_path)[0] + ".txt"
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Transcription completed: {transcript_file}")
        return text  
    
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        import traceback
        traceback.print_exc()
        return None