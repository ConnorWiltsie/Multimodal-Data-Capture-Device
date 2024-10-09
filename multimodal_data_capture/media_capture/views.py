import os
from django.shortcuts import render
from django.conf import settings

# Libraries for capturing image
import cv2
from datetime import datetime
# from picamera import PiCamera

# Libraries for recording audio
import wave
import pyaudio

# Capture image
def capture():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    image_filename = f'image_{timestamp}.jpg'
    image_path = os.path.join(settings.MEDIA_ROOT, image_filename)
    cv2.imwrite(image_path, frame)
    cap.release()
    return image_filename

# Record audio
p = pyaudio.PyAudio()
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
stream = None
frames = []

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
