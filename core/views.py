from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Game, GameConfig, KalakBluff, PlayerScore, User
import random
from django.http import JsonResponse
import google.generativeai as genai
import os
from django.conf import settings
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from difflib import SequenceMatcher
from django.contrib import messages


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "apikey")
genai.configure(api_key='AIzaSyBtnQNnoTiI8zrTEuBSR1qxJwESVIMutJA')

# Fallback list in case AI fails
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

#############################################################################################

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
    
#############################################################################################

def get_kalak_question():
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 1. THE STRICT PROMPT
        prompt = (
            "Donne-moi UNE SEULE question de culture générale insolite. "
            "La réponse doit être courte (1 à 3 mots). "
            "Réponds UNIQUEMENT avec ce format : QUESTION|RÉPONSE "
            "Ne mets pas de numéros, pas de liste, pas d'intro."
        )
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        print(f"AI Raw: {text}") 

        lines = text.split('\n')
        
        for line in lines:
            clean_line = line.strip()
            
            if "|" in clean_line:
                parts = clean_line.split("|")
                if len(parts) >= 2:
                    q = parts[0].replace("Question :", "").strip() 
                    a = parts[1].replace("Réponse :", "").strip().lower()
                    
                    if q[0].isdigit() and q[1] in ['.', ')']:
                        q = q[2:].strip()
                        
                    return q, a

        return "Quel est le comble pour un électricien ?", "ne pas être au courant"

    except Exception as e:
        print(f" AI Error: {e}")
        return "Erreur technique", "erreur"
    
#############################################################################################

class GameView(LoginRequiredMixin, TemplateView) : 
    

    def get_template_names(self):
        game, _ = Game.objects.get_or_create(id=1)
        
        if game.current_game == 'KALAK':
            return ['core/kalak.html']
        
        return ['core/game.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game, _ = Game.objects.get_or_create(id=1)
        
        user = self.request.user
        
        context['game'] = game

        # ------ context for spy game 
        if game.current_game == 'SPY' : 
            context['is_spy'] = (user == game.spy_user)
            context['the_word'] = game.current_word if not context['is_spy'] else 'You are the spy'

        # ------- context for kalak

        elif game.current_game == 'KALAK' :

            score, _ = PlayerScore.objects.get_or_create(user=user)
            context['my_score'] = score.points

            context['has_acted'] = game.round_players.filter(id=user.id).exists()
            context['round_num'] = game.kalak_round

            # if wrote bluff
            context['my_bluff'] = KalakBluff.objects.filter(game=game,player=user).first

            # if voting
            if game.kalak_phase == 'VOTING': 
                bluffs = list(KalakBluff.objects.filter(game=game))
                # add real answer with bluffs
                options = [{'text':b.text,'id':b.id,'type':'bluff'} for b in bluffs]
                options.append({'text':game.kalak_real_answer,'id':0,'type':'real'})
                random.shuffle(options)
                context['options'] = options

            # results
            if game.kalak_phase == 'RESULTS' : 
                context['all_bluffs'] = KalakBluff.objects.filter(game=game)



        return context
    


class SwitchGameView(LoginRequiredMixin, View):
    def post(self, request):
        game, _ = Game.objects.get_or_create(id=1)
        target = request.POST.get('game_type')
        
        if target in ['SPY', 'KALAK']:
            game.current_game = target
            game.is_active = False  
            
            # reset spy
            game.current_word = ""
            game.spy_user = None
            game.is_voting = False
            game.confirmed_players.clear()
            
            # reset kalak
            game.kalak_phase = 'WRITING'
            game.kalak_question = ""  # Clear old question
            game.kalak_real_answer = ""
            game.kalak_round = 0

            PlayerScore.objects.all().update(points=0) # reset scores

            # Delete all old bluffs from the previous round
            KalakBluff.objects.filter(game=game).delete()
            game.round_players.clear() # clear ready players

            game.save()
            
        return redirect('game')
        
class StartKalakRoundView(LoginRequiredMixin, View) : 

    def post(self,request,*args,**kwargs) : 
        game, _ = Game.objects.get_or_create(id=1)

        if game.kalak_round >= 20:
            game.kalak_phase = 'GAME_OVER'
            game.save()
            return redirect('game')
        
        q, a = get_kalak_question()
        game.kalak_question = q
        game.kalak_real_answer = a 

        game.is_active = True

        game.kalak_round += 1
        
        # reset round
        game.kalak_phase = 'WRITING'
        KalakBluff.objects.filter(game=game).delete()
        game.round_players.clear()

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
    

class SubmitBluffView(LoginRequiredMixin, View): 
    def post(self, request) : 
        game = Game.objects.get(id = 1)
        text = request.POST.get('bluff_text','').strip().lower()


        # close to real answer
        similarity = SequenceMatcher(None, text, game.kalak_real_answer).ratio()
        if similarity > 0.7 :
            messages.error(request, "Too close to the real answer! Be more creative.")
            return redirect('game')
        
        KalakBluff.objects.create(game=game, player= request.user, text= text)


        game.round_players.add(request.user)
        game.save()

        total_players = User.objects.count()
        ready_players = game.round_players.count()
        
        if ready_players >= total_players:
            game.kalak_phase = 'VOTING'
            game.round_players.clear() # reset for next phase
            game.save()

        return redirect('game')
    

class VoteKalakView(LoginRequiredMixin, View): 
    def post(self, request) : 

        game  = Game.objects.get(id=1)
        choice_id = int(request.POST.get('choice_id'))

        if game.round_players.filter(id=request.user.id).exists():
            messages.warning(request, "You cannot change your vote!")
            return redirect('game')
        
        
        user_score , _ = PlayerScore.objects.get_or_create(user=request.user)

        if choice_id == 0 : 
            user_score.points += 2 
        else : 
            bluff = KalakBluff.objects.get(id=choice_id)
            bluff.voters.add(request.user)

            #author of bluff get points

            liar_score , _ = PlayerScore.objects.get_or_create(user=bluff.player)
            liar_score.points += 1 
            liar_score.save()
            
        game.round_players.add(request.user)
        game.save()

        total_players = User.objects.count()
        ready_players = game.round_players.count()
        
        if ready_players >= total_players:
            game.kalak_phase = 'RESULTS'
            # We clear the ready list so it's clean for the next round
            game.round_players.clear() 
            game.save()
            
            
        user_score.save()
        return redirect('game')
    

class AdvancePhaseView(LoginRequiredMixin,View) : 

    def post(self, request): 

        game = Game.objects.get(id=1)
        if game.kalak_phase == 'WRITING' : 
            game.kalak_phase = 'VOTING'
        elif game.kalak_phase == 'VOTING' : 
            game.kalak_phase = 'RESULTS'
        game.save()
        return redirect('game')
    
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        game, _ = Game.objects.get_or_create(id=1)
        context['current_game'] = game.current_game
        return context