import os
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse,HttpResponse,HttpResponseNotFound
import shutil 
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
import threading
import logging
from datetime import datetime
from picamera2 import Picamera2
import wave, pyaudio, time
from .whisper import transcribe_audio

from django.core.mail import EmailMessage

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

#Capture image
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
        self.p = None
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.audio_filename = None

    def start_recording(self):
        if not self.is_recording:
            logger.info("Starting recording")
            self.is_recording = True
            self.frames = []
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, 
                                      rate=self.RATE, input=True, 
                                      frames_per_buffer=self.CHUNK)
            self.audio_filename = f'audio_{datetime.now().strftime("%Y%m%d%H%M%S")}.wav'
            threading.Thread(target=self._record_audio, daemon=True).start()
            return True
        return False

    def _record_audio(self):
        logger.info("Recording thread started")
        while self.is_recording:
            try:
                data = self.stream.read(self.CHUNK)
                self.frames.append(data)
            except Exception as e:
                logger.error(f"Error during recording: {str(e)}")
                self.is_recording = False
        logger.info("Recording thread ended")

    def stop_recording(self):
        if self.is_recording:
            logger.info("Stopping recording")
            self.is_recording = False
            time.sleep(0.5)  
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()
            
            audio_path = os.path.join(settings.MEDIA_ROOT, self.audio_filename)
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.frames))
            
            logger.info(f"Audio saved to {audio_path}")
            return self.audio_filename
        return None

audio_recorder = AudioRecorder()

def start_recording(request):
    if audio_recorder.start_recording():
        logger.info("Recording started successfully")
        return JsonResponse({"status": "Recording started"})
    logger.warning("Attempted to start recording while already recording")
    return JsonResponse({"status": "Already recording"})

def stop_recording(request):
    try:
        filename = audio_recorder.stop_recording()
        if filename:
            logger.info(f"Recording stopped successfully. File: {filename}")
            return JsonResponse({"status": "Recording stopped", "filename": filename})
        else:
            logger.warning("Stop recording called but no recording was in progress")
            return JsonResponse({"status": "Not recording"})
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}", exc_info=True)
        return JsonResponse({"status": "Error", "message": str(e)}, status=500)

def start_transcription(request):
    audio_filename = request.POST.get('audio_filename')
    if not audio_filename:
        logger.error("No audio filename provided")
        return JsonResponse({"status": "error", "message": "No audio filename provided"})

    audio_path = os.path.join(settings.MEDIA_ROOT, audio_filename)
    transcription_filename = audio_filename.replace('.wav', '.txt')
    transcription_path = os.path.join(settings.MEDIA_ROOT, transcription_filename)

    def transcribe_and_save():
        logger.info(f"Starting transcription for: {audio_path}")
        try:
            transcription = transcribe_audio(audio_path) 
            with open(transcription_path, 'w', encoding='utf-8') as f:
                f.write(transcription) 
            logger.info(f"Transcription saved successfully: {transcription_path}")
        except Exception as e:
            logger.error(f"Error in transcribe_and_save: {str(e)}", exc_info=True)

    threading.Thread(target=transcribe_and_save, daemon=True).start()
    return JsonResponse({"status": "in_progress"})

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
    img_files = os.listdir(settings.MEDIA_ROOT)
    img_paths = [os.path.join(settings.MEDIA_URL, img) for img in img_files if img.startswith('image_')]
    
    audio_data = get_audio_data() 

    context = {
        'img_paths': img_paths,
        'audio_data': audio_data,
    }
    
    return render(request, 'media_capture/index.html', context)

def get_audio_data():
    audio_files = [f for f in os.listdir(settings.MEDIA_ROOT) if f.startswith('audio_') and f.endswith('.wav')]
    audio_files.sort(key=lambda x: os.path.getmtime(os.path.join(settings.MEDIA_ROOT, x)), reverse=True)

    audio_data = []
    for audio_file in audio_files:
        audio_path = os.path.join(settings.MEDIA_URL, audio_file)
        transcription_file = audio_file.replace('.wav', '.txt') 
        transcription_path = os.path.join(settings.MEDIA_URL, transcription_file)  

        if os.path.exists(os.path.join(settings.MEDIA_ROOT, transcription_file)):
            with open(os.path.join(settings.MEDIA_ROOT, transcription_file), 'r', encoding='utf-8') as f:
                transcription = f.read()
        else:
            transcription = None

        audio_data.append({
            'audio_path': audio_path,
            'transcription': transcription,
            'transcription_path': transcription_path 
        })

    return audio_data

def get_all_recordings(request):
    audio_data = get_audio_data()  
    for item in audio_data:
        item['transcription_path'] = item['audio_path'].replace('.wav', '.txt')  
    html = render_to_string('media_capture/all_audios.html', {'audio_data': audio_data})
    return JsonResponse({'html': html})

def get_all_images(request):
    img_paths = get_image_paths()  
    html = render_to_string('media_capture/all_images.html', {'img_paths': img_paths})
    return JsonResponse({'html': html})

def get_image_paths():
    img_files = os.listdir(settings.MEDIA_ROOT)
    img_paths = [os.path.join(settings.MEDIA_URL, img) for img in img_files if img.startswith('image_')]
    return img_paths

def get_recent_images(request):
    img_paths = get_image_paths()[:3]  
    html = render_to_string('media_capture/recent_images.html', {'img_paths': img_paths})
    return JsonResponse({'html': html})

@require_POST
def delete_audio(request):
    audio_filename = request.POST.get('audio_filename')
    if not audio_filename:
        return JsonResponse({"status": "error", "message": "No audio filename provided"})

    try:
        audio_path = os.path.join(settings.MEDIA_ROOT, audio_filename)
        transcription_filename = audio_filename.replace('.wav', '.txt')
        transcription_path = os.path.join(settings.MEDIA_ROOT, transcription_filename)

        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(transcription_path):
            os.remove(transcription_path)

        return JsonResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Error deleting audio: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_POST
def delete_image(request):
    image_filename = request.POST.get('image_filename')
    if not image_filename:
        return JsonResponse({"status": "error", "message": "No image filename provided"})

    try:
        image_path = os.path.join(settings.MEDIA_ROOT, image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
        return JsonResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
def get_file_paths(file_type):
    """Retrieve file paths for audio or image files."""
    file_paths = []

    if file_type == 'audio':
        media_files = [f for f in os.listdir(settings.MEDIA_ROOT) if f.startswith('audio_')]
    elif file_type == 'image':
        media_files = [f for f in os.listdir(settings.MEDIA_ROOT) if f.startswith('image_')]
    else:
        return None 

    for media_file in media_files:
        media_path = os.path.join(settings.MEDIA_URL, media_file)  
        absolute_path = os.path.join(settings.MEDIA_ROOT, media_file)
        file_paths.append({'media_path': media_path, 'absolute_path': absolute_path})

    return file_paths

@require_POST
def email_file(request):
    email_address = request.POST.get('email_address')
    file_type = request.POST.get('file_type')  

    logger.info(f"Received parameters: file_type={file_type}, email_address={email_address}")

    if not email_address or not file_type:
        logger.error("Missing parameters.")
        return JsonResponse({"status": "error", "message": "Missing parameters."})

    file_paths = get_file_paths(file_type)

    if file_paths is None:
        logger.error("Invalid file type.")
        return JsonResponse({"status": "error", "message": "Invalid file type."})

    if not file_paths:
        logger.error("No files found for the specified type.")
        return JsonResponse({"status": "error", "message": "No files found."})

    email = EmailMessage(
        subject=f"Your {file_type} files",
        body=f"Attached are your {file_type} files.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email_address],
    )

    for file in file_paths:
        if os.path.exists(file['absolute_path']):
            email.attach_file(file['absolute_path'])
        else:
            logger.error(f"File does not exist: {file['absolute_path']}")

    try:
        email.send()
        return JsonResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)})
    
@require_POST
def generate_pdf(request):
    file_paths = get_file_paths('image')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="images.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    for file in file_paths:
        image_path = file['absolute_path']
        if os.path.exists(image_path):
            p.drawImage(image_path, 0, height - 400, width=width, height=400)  
            p.showPage()  
        else:
            logger.error(f"Image does not exist: {image_path}")

    p.save()

    return response