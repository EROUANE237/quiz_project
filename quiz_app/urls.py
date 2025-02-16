from django.urls import path
from . import views

urlpatterns = [
    path('ask-question/', views.ai_quiz_ask_question, name='ask_question'),  # Ajouter cette ligne
    path('answer-question/', views.ai_quiz_answer, name='answer_question'),
    path('', views.index, name='index'),  # Page d'accueil
]