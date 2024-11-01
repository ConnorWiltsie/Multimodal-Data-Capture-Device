import os
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import threading
import logging
logger = logging.getLogger(__name__)

# Libraries for capturing image
from datetime import datetime
from picamera2 import Picamera2
from time import sleep


# Libraries for recording audio
import wave
import pyaudio

from .whisper import transcribe_audio

# Capture image
def capture():
    
    #Create picamera
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()
    sleep(2)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    image_filename = f'image_{timestamp}.jpg'
    image_path = os.path.join(settings.MEDIA_ROOT, image_filename)
    picam2.capture_file(image_path)
    picam2.stop()
    return image_filename

class AudioRecorder:
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.audio_filename = None

    def start_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.frames = []
            self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, 
                                      rate=self.RATE, input=True, 
                                      frames_per_buffer=self.CHUNK)
            self.audio_filename = f'audio_{datetime.now().strftime("%Y%m%d%H%M%S")}.wav'
            threading.Thread(target=self._record_audio, daemon=True).start()
            return True
        return False

    def _record_audio(self):
        while self.is_recording:
            data = self.stream.read(self.CHUNK)
            self.frames.append(data)

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            audio_path = os.path.join(settings.MEDIA_ROOT, self.audio_filename)
            wf = wave.open(audio_path, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            threading.Thread(target=self._transcribe_and_save, args=(audio_path,)).start()
            return self.audio_filename
        return None

    def _transcribe_and_save(self, audio_path):
        transcribe_audio(audio_path)

audio_recorder = AudioRecorder()

def start_recording(request):
    if audio_recorder.start_recording():
        return JsonResponse({"status": "Recording started"})
    return JsonResponse({"status": "Already recording"})

def stop_recording(request):
    filename = audio_recorder.stop_recording()
    if filename:
        return JsonResponse({"status": "Recording stopped", "filename": filename})
    return JsonResponse({"status": "Not recording"})

def start_transcription(request):
    audio_filename = request.POST.get('audio_filename')
    if not audio_filename:
        return JsonResponse({"status": "error", "message": "No audio filename provided"})
    
    audio_path = os.path.join(settings.MEDIA_ROOT, audio_filename)
    transcription_filename = audio_filename.replace('.wav', '.txt')
    transcription_path = os.path.join(settings.MEDIA_ROOT, transcription_filename)
    
    def transcribe_and_save():
        try:
            transcription = transcribe_audio(audio_path)
            with open(transcription_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            logger.info(f"Transcription saved successfully: {transcription_path}")
        except Exception as e:
            logger.error(f"Error in transcribe_and_save: {str(e)}")
    
    threading.Thread(target=transcribe_and_save).start()
    return JsonResponse({"status": "Transcription started"})

def get_transcription(request):
    audio_filename = request.GET.get('audio_filename')
    if not audio_filename:
        return JsonResponse({"status": "error", "message": "No audio filename provided"})
    
    transcription_filename = audio_filename.replace('.wav', '.txt')
    transcription_path = os.path.join(settings.MEDIA_ROOT, transcription_filename)
    
    if os.path.exists(transcription_path):
        try:
            with open(transcription_path, 'r', encoding='utf-8') as f:
                transcription = f.read()
            if transcription.strip():
                return JsonResponse({"status": "completed", "transcription": transcription})
            else:
                return JsonResponse({"status": "error", "message": "Transcription file is empty"})
        except Exception as e:
            logger.error(f"Error reading transcription file: {str(e)}")
            return JsonResponse({"status": "error", "message": "Error reading transcription file"})
    else:
        return JsonResponse({"status": "in_progress"})
    
def index(request):
    if request.method == 'POST':
        if 'capture' in request.POST:
            try:
                capture()
            except Exception as e:
                logger.error(f"Error capturing image: {str(e)}")
        elif request.POST.get('action') == 'start_recording':
            return start_recording(request)
        elif request.POST.get('action') == 'stop_recording':
            return stop_recording(request)

    img_files = os.listdir(settings.MEDIA_ROOT)
    img_paths = [os.path.join(settings.MEDIA_URL, img) for img in img_files if img.startswith('image_')]
    
    audio_files = [f for f in os.listdir(settings.MEDIA_ROOT) if f.startswith('audio_') and f.endswith('.wav')]
    audio_paths = [os.path.join(settings.MEDIA_URL, audio) for audio in audio_files]
    
    transcription_files = [f.replace('.wav', '.txt') for f in audio_files if os.path.exists(os.path.join(settings.MEDIA_ROOT, f.replace('.wav', '.txt')))]
    transcription_paths = [os.path.join(settings.MEDIA_URL, trans) for trans in transcription_files]

    context = {
        'img_paths': img_paths,
        'audio_paths': audio_paths,
        'transcription_paths': transcription_paths,
    }
    return render(request, 'index.html', context)