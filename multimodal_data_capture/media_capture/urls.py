from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start_recording/', views.start_recording, name='start_recording'),
    path('stop_recording/', views.stop_recording, name='stop_recording'),
    path('start_transcription/', views.start_transcription, name='start_transcription'),
    path('get_transcription/', views.get_transcription, name='get_transcription'),
]
