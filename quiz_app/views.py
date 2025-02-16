# quiz_app/views.py
import json
import openai
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.conf import settings  # Importation de settings pour récupérer la clé API
from .models import DocGPTAnswer

# Assure-toi que ta clé OpenAI est bien définie dans settings.py
openai.api_key = settings.OPENAI_API_KEY



def index(request):
    """ Affiche la page principale """
    return render(request, "quiz_app/index.html")


@csrf_exempt
def ai_quiz_ask_question(request):
    """ Génère une question en fonction des paramètres fournis par l'utilisateur """
    
    question = None

    if request.method == "POST":
        difficulty = request.POST.get("difficulty", "facile")
        language = request.POST.get("language", "python")
        theme = request.POST.get("theme", "")
        quiz_type = request.POST.get("type", "qcm")
        gpt_model = request.POST.get("gpt", "gpt-3.5-turbo")

        # Construction de la question
        question = f"Pose-moi une question de niveau {difficulty} en {language}"
        if theme:
            question += f" sur le thème {theme}"

        if quiz_type == "qcm":
            question += " et fais un QCM avec 3 à 6 choix de réponses."
        elif quiz_type == "code":
            question += " et donne-moi un exercice où je dois écrire du code."
        elif quiz_type == "error":
            question += " contenant une erreur que je dois identifier."

        # Envoi à OpenAI
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": "Tu es un assistant éducatif."},
                {"role": "user", "content": question},
            ]
        )

        question = response.choices[0].message['content']

    return render(request, "quiz_app/index.html", {"question": question})


@csrf_exempt
def ai_quiz_answer(request):
    """ Vérifie la réponse de l'utilisateur et fournit une explication """
    
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    data = json.loads(request.body)
    category = data.get("category", "Programmation")
    difficulty = data.get("difficulty", "facile")
    language = data.get("language", "python")
    theme = data.get("theme", "")
    user_answer = data.get("answer", "Aucune réponse fournie.")
    gpt_model = data.get("gpt", "gpt-3.5-turbo")

    ai_question = request.session.get("ai_question", "Aucune question disponible.")

    def event_stream():
        full_completion = []

        messages = [
            {"role": "system", "content": "Tu es un assistant éducatif qui corrige les réponses et explique pourquoi."},
            {"role": "assistant", "content": ai_question},
            {"role": "user", "content": user_answer},
        ]

        completion = openai.ChatCompletion.create(
            model=gpt_model,
            messages=messages,
            stream=True,
        )

        for chunk in completion:
            content = chunk['choices'][0]['delta'].get('content')
            if content:
                full_completion.append(content)
                yield f"data: {json.dumps(content)}\n\n"

        # Sauvegarde de l'explication en base de données si non existante
        if not DocGPTAnswer.objects.filter(question=ai_question).exists():
            DocGPTAnswer.objects.create(
                question=ai_question,
                explanation="".join(full_completion),
                category=category,
                difficulty={"facile": "easy", "intermédiaire": "medium", "difficile": "hard", "expert": "expert"}.get(difficulty, "easy"),
                language=language,
                theme=theme,
            )

        # Nettoyage des sessions
        request.session.pop("ai_question", None)

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')