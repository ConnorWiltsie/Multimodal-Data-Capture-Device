import os
from django.shortcuts import render
from django.conf import settings

# Libraries for capturing image
from datetime import datetime
from picamera2 import Picamera2
from time import sleep


# Libraries for recording audio
import wave
#import pyaudio

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
#p = pyaudio.PyAudio()
#CHUNK = 1024
#FORMAT = pyaudio.paInt16
#CHANNELS = 1
#RATE = 44100
#stream = None
#frames = []

#def start_record():
#    global stream, frames
#    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
#    frames = []
#
#def stop_record():
#    global stream, frames
#    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
#    audio_filename = f'audio_{timestamp}.wav'
#    audio_path = os.path.join(settings.MEDIA_ROOT, audio_filename)
#    
#    stream.stop_stream()
#    stream.close()
#    print("Recording stopped")
#
#    wf = wave.open(audio_path, 'wb')
#    wf.setnchannels(CHANNELS)
#    wf.setsampwidth(p.get_sample_size(FORMAT))
#    wf.setframerate(RATE)
#    wf.writeframes(b''.join(frames))
#    wf.close()
#
#    frames = []  # Clear frames after saving
#    return audio_filename

def index(request):
#    global frames 

    if request.method == 'POST':
        if 'capture' in request.POST:
            capture()
#        elif 'start_recording' in request.POST:
#            start_record()
#        elif 'stop_recording' in request.POST:
#            audio_filename = stop_record()
#        else:
#            audio_filename = None

    img_files = os.listdir(settings.MEDIA_ROOT)
    img_paths = [os.path.join(settings.MEDIA_URL, img) for img in img_files if img.startswith('image_')]
#    audio_files = [os.path.join(settings.MEDIA_URL, audio) for audio in img_files if audio.startswith('audio_')]
    context = {
        'img_paths': img_paths,
#        'audio_paths': audio_files
    }
    return render(request, 'index.html', context)
