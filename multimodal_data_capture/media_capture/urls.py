from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start_recording/', views.start_recording, name='start_recording'),
    path('stop_recording/', views.stop_recording, name='stop_recording'),
    path('start_transcription/', views.start_transcription, name='start_transcription'),
    path('get_transcription/', views.get_transcription, name='get_transcription'),
    path('get_all_recordings/', views.get_all_recordings, name='get_all_recordings'),
    path('get_all_images/', views.get_all_images, name='get_all_images'),
    path('get_recent_images/', views.get_recent_images, name='get_recent_images'),
    path('delete_audio/', views.delete_audio, name='delete_audio'),
    path('delete_image/', views.delete_image, name='delete_image'),
]