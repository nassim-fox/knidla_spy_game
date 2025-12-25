from django.db import models
from django.contrib.auth.models import User

class Game(models.Model):
    # GLOBAL SETTINGS 
    GAME_TYPES = [('SPY', 'Spy Game'), ('KALAK', 'Kalak')]
    current_game = models.CharField(max_length=10, choices=GAME_TYPES, default='SPY')
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Knidla SPY GAME DATA 
    current_word = models.CharField(max_length=100, blank=True)
    spy_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='spy_games')
    # (confirmation logic for both games)
    is_voting = models.BooleanField(default=False)
    confirmed_players = models.ManyToManyField(User, related_name='confirmed_games', blank=True)

    # KALAK DATA 
    kalak_question = models.TextField(blank=True)
    kalak_real_answer = models.CharField(max_length=200, blank=True)
    kalak_round = models.IntegerField(default=0)
    round_players = models.ManyToManyField(User, related_name='finished_step', blank=True)

    # Phases: 'WRITING' (Players write lies) -> 'VOTING' (Pick answer) -> 'RESULTS' (Show points)
    kalak_phase = models.CharField(max_length=20, default='WRITING')

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

    kalak_prompt = models.TextField(default="Donne-moi une question de culture générale obscure et sa réponse.")


    def get_category_list(self):
        return [line.strip() for line in self.categories.split('\n') if line.strip()]

    def __str__(self):
        return "Game Configuration"

        

class PlayerScore(models.Model):
    """Tracks points for a specific player"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}: {self.points}"


class KalakBluff(models.Model):
    """A fake answer written by a player"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    
    # Who voted for this lie?
    voters = models.ManyToManyField(User, related_name='voted_bluffs', blank=True)

    def __str__(self):
        return f"{self.player.username}: {self.text}"
    

class KalakConfig(models.Model):

    system_prompt = models.TextField(
        default=(
            "Donne-moi UNE question de culture générale très surprenante sur le thème : {theme}. "
            "La réponse doit être courte (1 à 4 mots max). "
            "Réponds UNIQUEMENT avec ce format : QUESTION|RÉPONSE"
        ),
        help_text="Use {theme} where you want the random category to appear."
    )
    
    categories = models.TextField(
        default="les animaux étranges, l'histoire, l'espace, le corps humain, les pirates, le cinéma"
    )

    def get_categories_list(self):
        return [x.strip() for x in self.categories.split(',') if x.strip()]

    def __str__(self):
        return "Kalak Configuration"
    