from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Game, GameConfig
import random
from django.http import JsonResponse
import google.generativeai as genai
import os
from django.conf import settings
from django.views.generic import UpdateView
from django.urls import reverse_lazy


# 1. Configure the API (Best practice: use Environment Variables)
# For local testing, you can put the string here, but for Heroku use os.environ
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyA0aH_xxpNGGib8hnkzP-xe-FkeV2BSyrs")
genai.configure(api_key=GEMINI_API_KEY)

# Fallback list in case AI fails
# A mix of locations, objects, jobs, and animals
BACKUP_WORDS = [
    "La Tour Eiffel", "Un Kangourou", "Napoléon", "Une Pizza", 
    "Un Chirurgien", "Une Brosse à dents", "Mars (la planète)", 
    "Un Vampire", "Le Titanic", "Une Fourchette", "Un Youtubeur"
]

WORD_LIST = ["Sousmarin","Arbe","Arab"] 

class ConfigView(LoginRequiredMixin, UpdateView):
    model = GameConfig
    fields = ['prompt_template', 'categories']
    template_name = 'core/config.html'
    success_url = reverse_lazy('game')

    def get_object(self):
        obj, created = GameConfig.objects.get_or_create(id=1)
        return obj

def get_ai_word():

    config, _ = GameConfig.objects.get_or_create(id=1)
    
    category_list = config.get_category_list()
    if not category_list:
        category_list = ["Tout et n'importe quoi"] 
    
    chosen_category = random.choice(category_list)

    final_prompt = config.prompt_template.replace("{category}", chosen_category)

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            final_prompt,
            generation_config=genai.types.GenerationConfig(temperature=1.0)
        )
        return response.text.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return random.choice(BACKUP_WORDS)
    

class GameView(LoginRequiredMixin, TemplateView) : 
    
    
    template_name = 'core/game.html'

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game, _ = Game.objects.get_or_create(id=1)

        context['game'] = game
        context['is_spy'] = False
        context['the_word'] = 'Waiting for round to start'

        if game.is_active : 
            if self.request.user == game.spy_user : 
                context['is_spy'] = True
                context['the_word']  = 'You are the spy'
            else : 
                context['the_word'] = game.current_word

        return context
    

class StartRoundView(LoginRequiredMixin, View) : 

    def post(self,request,*args,**kwargs) : 
        game, _ = Game.objects.get_or_create(id=1)

        new_word = random.choice(WORD_LIST)

        from django.contrib.auth.models import User
        all_users = list(User.objects.all())

        if all_users : 
            game.current_word = new_word
            game.spy_user = random.choice(all_users)
            game.is_active = True
            game.save()

        return redirect('game')
    
class StartRoundView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        game, _ = Game.objects.get_or_create(id=1)
        
        new_word = get_ai_word()
        
        new_word = new_word.replace(".", "")
        
        from django.contrib.auth.models import User
        all_users = list(User.objects.all())
        
        if all_users:
            game.current_word = new_word
            game.spy_user = random.choice(all_users)
            game.is_active = True
            game.save()
            
        return redirect('game')

class GameStatusView(View):
    def get(self, request, *args, **kwargs):
        game, _ = Game.objects.get_or_create(id=1)
        
        return JsonResponse({
            'last_updated': game.updated_at.isoformat()
        })