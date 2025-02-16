from django.db import models

class DocGPTAnswer(models.Model):
    question = models.TextField()
    explanation = models.TextField()
    category = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=50)
    language = models.CharField(max_length=50)
    theme = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question: {self.question}, Difficulty: {self.difficulty}"