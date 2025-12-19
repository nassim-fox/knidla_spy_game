from django.db import models
from django.contrib.auth.models import User

class Game(models.Model):
    current_word = models.CharField(max_length=100, blank=True)
    spy_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Game Word: {self.current_word}"
    


class GameConfig(models.Model):
    prompt_template = models.TextField(
        default=(
            "Je joue à 'Spyfall'. Génère un mot secret en Français appartenant à cette catégorie : '{category}'. "
            "Sois imaginatif. Réponds UNIQUEMENT par le mot, sans article ni ponctuation."
        ),
        help_text="Use {category} where you want the random category to appear."
    )
    
    categories = models.TextField(
        default=(
            "Un objet du quotidien\n"
            "Un animal\n"
            "Un métier\n"
            "Un personnage célèbre\n"
            "Un lieu"
        ),
        help_text="Put each category on a new line."
    )

    def get_category_list(self):
        return [line.strip() for line in self.categories.split('\n') if line.strip()]

    def __str__(self):
        return "Game Configuration"