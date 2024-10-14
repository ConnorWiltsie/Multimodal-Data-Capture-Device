import os
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import logging
logger = logging.getLogger(__name__)

# Libraries for capturing image
from datetime import datetime
from picamera2 import Picamera2
from time import sleep


# Libraries for recording audio
import wave
import pyaudio

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

# Record audio
p = pyaudio.PyAudio()
# Audio recording setup
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
p = pyaudio.PyAudio()
stream = None
frames = []
is_recording = False
audio_filename = None

def start_recording(request):
    global stream, frames, is_recording, audio_filename
    if not is_recording:
        is_recording = True
        frames = []
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        audio_filename = f'audio_{datetime.now().strftime("%Y%m%d%H%M%S")}.wav'
        
        # Start a background thread to collect audio data
        import threading
        threading.Thread(target=record_audio, daemon=True).start()
        
        return JsonResponse({"status": "Recording started"})
    return JsonResponse({"status": "Already recording"})

def record_audio():
    global frames, is_recording, stream
    while is_recording:
        data = stream.read(CHUNK)
        frames.append(data)

def stop_recording(request):
    global stream, frames, is_recording, audio_filename
    if is_recording:
        is_recording = False
        if stream:
            stream.stop_stream()
            stream.close()
        
        wf = wave.open(os.path.join(settings.MEDIA_ROOT, audio_filename), 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return JsonResponse({"status": "Recording stopped", "filename": audio_filename})
    return JsonResponse({"status": "Not recording"})

def index(request):
    global stream, frames, is_recording

    if request.method == 'POST':
        if 'capture' in request.POST:
            capture()
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

    context = {
        'img_paths': img_paths,
        'audio_paths': audio_paths,
    }
    return render(request, 'index.html', context)
