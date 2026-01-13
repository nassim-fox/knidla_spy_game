from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Game, GameConfig, KalakBluff, PlayerScore, Profile, User, KalakConfig
import random
from django.http import JsonResponse
import google.generativeai as genai
import os
from django.conf import settings
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from difflib import SequenceMatcher
from django.contrib import messages


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDitd0IfLGc4aUfSrllWm-v8-xchzqprag")
genai.configure(api_key=GEMINI_API_KEY)

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
    success_url = reverse_lazy('play')

    def get_object(self):
        obj, created = GameConfig.objects.get_or_create(id=1)
        return obj
    

#############################################################################################

from django.http import JsonResponse

def game_data_api(request, room_code):
    game = get_object_or_404(Game, room_code=room_code)
    
    # Get leaderboard data
    leaderboard = []
    for ps in game.leaderboard.all().select_related('user__profile'):
        leaderboard.append({
            'username': ps.user.username,
            'points': ps.points,
            'avatar': ps.user.profile.avatar_url,
            'is_ready': ps.user.id in game.ready_player_ids, # Assuming you have this logic
            'user_id': ps.user.id
        })
        
    return JsonResponse({
        'phase': game.kalak_phase,
        'leaderboard': leaderboard,
        'last_updated': game.updated_at.isoformat(),
    })


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
        
       
        config, _ = KalakConfig.objects.get_or_create(id=1)

        model = genai.GenerativeModel(config.model)
        
        
        themes = config.get_categories_list()
        if not themes:
            themes = ["General Knowledge"] # Fallback if list is empty
        
        selected_theme = random.choice(themes)
        
        prompt = config.system_prompt.replace("{theme}", selected_theme)
    
        response = model.generate_content(prompt)
        text = response.text.strip()
        print(f"AI Raw: {text}") 

        lines = text.split('\n')
        
        q = "Question par défaut ?"
        a = "réponse"
        img = "_"


        for line in lines:
            clean_line = line.strip()
            
            if "|" in clean_line:
                parts = clean_line.split("|")
                if len(parts) >= 2:
                    q = parts[0].replace("Question :", "").strip() 
                    a = parts[1].replace("Réponse :", "").strip().lower()
                    
                    if len(parts) >= 3:
                        img = parts[2].strip()
                

                    if q[0].isdigit() and q[1] in ['.', ')']:
                        q = q[2:].strip()
                        
        
        return q, a, img


    except Exception as e:
        print(f" AI Error: {e}")
        return "Erreur technique", "erreur",""
    
#############################################################################################

def get_current_game(request): 
    
    code = request.session.get('room_code')

    if not code:
        return None
    try :
        game = Game.objects.get(room_code=code)
        if request.user not in game.players.all() : 
            del request.session['room_code']
            return None
        return game 
    except game.DoesNotExist : 
        return None
    

#############################################################################################

class CreateRoomView(LoginRequiredMixin, View) : 
    def post(self,request) : 

        game = Game.objects.create(admin=request.user)
        game.players.add(request.user)
        game.save()

        request.session['room_code'] = game.room_code
        
        return redirect('lobby')
    
class JoinRoomView(LoginRequiredMixin, View) :

    def post(self,request):  

        code = request.POST.get('room_code','').upper().strip()

        try :
            game = Game.objects.get(room_code=code)

            #if not game.is_active : 
            game.players.add(request.user)
            request.session['room_code'] = code
            #else: 
            #    messages.error(request,'Game already in progress')
            #    return redirect('home')
            
            PlayerScore.objects.get_or_create(
                user=request.user, 
                game=game
            )

            game.save()

            
            return redirect('lobby')

            
                 
        except Game.DoesNotExist: 
            messages.error(request,'Room not found')
            return redirect('home')
        

class LobbyView(LoginRequiredMixin, TemplateView) : 

    template_name = 'core/lobby.html'

    def get(self,request,*args,**kwargs):
        game = get_current_game(request)
        if not game : 
            return redirect('home')

        if game.is_active : 
            return redirect('play')

        context = {
            'game' : game , 
            'players' : game.players.all(),
            'is_admin' : request.user == game.admin,
            'room_url' : request.build_absolute_uri(f"/?join={game.room_code}")
        }

        return render(request,self.template_name,context)
    
class KickPlayerView(LoginRequiredMixin,View) : 

    def post(self,request, player_id) : 
        game = get_current_game(request)
        if not game or request.user != game.admin : 
            return redirect('home')
        
        user_to_kick = User.object.get(id=player_id)

        if user_to_kick != game.admin : 
            game.players.remove(user_to_kick)

        return redirect('lobby')

class LeaveRoomView(LoginRequiredMixin, View):
    def post(self, request):
        game = get_current_game(request)
        if game:
            game.players.remove(request.user)

            PlayerScore.objects.filter(game=game, user=request.user).delete()

            
            if game.players.count() == 0:
                game.delete() 
            elif game.admin == request.user:
                game.admin = game.players.first()
            
            game.save()
                
        if 'room_code' in request.session:
            del request.session['room_code']
            
        return redirect('home')


class GameView(LoginRequiredMixin, TemplateView) : 
    

    def get(self,request,*args,**kwargs): 

        game = get_current_game(request)
        
        if not game:
            return redirect('home')
            
        if not game.is_active:
            return redirect('lobby')
        
        template_name = 'core/kalak.html' if game.current_game == 'KALAK' else 'core/game.html'
        
        context = {
            'game': game,
        }

        config, _ = KalakConfig.objects.get_or_create(id=1)        
        
        context['leaderboard'] = game.leaderboard.all().order_by('-points')#PlayerScore.objects.all().order_by('-points')
        
        user = self.request.user
        
        context['game'] = game

        # ------ context for spy game 
        if game.current_game == 'SPY' : 
            context['is_spy'] = (user == game.spy_user)
            context['the_word'] = game.current_word if not context['is_spy'] else 'You are the spy'

        # ------- context for kalak

        elif game.current_game == 'KALAK' :

            #score, _ = PlayerScore.objects.get_or_create(user=user)
            
            score, _ = PlayerScore.objects.get_or_create(user=user, game=game)

            context['my_score'] = score.points

            context['ready_player_ids'] = list(game.round_players.values_list('id', flat=True))
            
            context['has_acted'] = game.round_players.filter(id=user.id).exists()
            context['round_num'] = game.kalak_round
            context['max_rounds'] = config.max_rounds
            

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



        return render(request, template_name, context)    
    

class SwitchGameView(LoginRequiredMixin, View):
    def post(self, request):
        game = get_current_game(self.request)
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
            
        return redirect('play')
        
class StartKalakRoundView(LoginRequiredMixin, View) : 

    def post(self,request,*args,**kwargs) : 
        game = get_current_game(request)
        if not game or request.user != game.admin:
            return redirect('home')
        
        config = KalakConfig.objects.get(id=1)
        
        game.current_game = 'KALAK'
        
        if game.kalak_round >= config.max_rounds:
            game.kalak_phase = 'GAME_OVER'
            game.save()
            return redirect('play')
        
        q, a, img = get_kalak_question()        
        game.kalak_question = q
        game.kalak_real_answer = a 
        game.kalak_image_url = img
        
        game.is_active = True

        game.kalak_round += 1
        
        # reset round
        game.kalak_phase = 'WRITING'
        KalakBluff.objects.filter(game=game).delete()
        game.round_players.clear()

        game.save()

        return redirect('play')
    
class StartRoundView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        
        game = get_current_game(request)
        
        if not game:
            return redirect('home')
       
        game.current_game = 'SPY'
    
        new_word = get_ai_word()
        
        new_word = new_word.replace(".", "")
        
        from django.contrib.auth.models import User
        all_users = list(User.objects.all())
        
        if all_users:
            game.current_word = new_word
            game.spy_user = random.choice(all_users)
            game.is_active = True
            game.save()
            
        return redirect('play')

class GameStatusView(View):
    def get(self, request, *args, **kwargs):
        game = get_current_game(self.request)        

        return JsonResponse({
            'last_updated': game.updated_at.isoformat()
        })
    

class SubmitBluffView(LoginRequiredMixin, View): 
    def post(self, request) : 
        game = get_current_game(self.request)

        text = request.POST.get('bluff_text','').strip().lower()


        # close to real answer
        similarity = SequenceMatcher(None, text, game.kalak_real_answer).ratio()
        if similarity > 0.7 :
            messages.error(request, "Too close to the real answer! Be more creative.")
            return redirect('play')
        
        KalakBluff.objects.create(game=game, player= request.user, text= text)


        game.round_players.add(request.user)
        game.save()

        total_players = User.objects.count()
        ready_players = game.round_players.count()
        
        if ready_players >= total_players:
            game.kalak_phase = 'VOTING'
            game.round_players.clear() # reset for next phase
            game.save()

        return redirect('play')
    

class VoteKalakView(LoginRequiredMixin, View): 
    def post(self, request) : 

        game = get_current_game(self.request)
        choice_id = int(request.POST.get('choice_id'))

        if game.round_players.filter(id=request.user.id).exists():
            messages.warning(request, "You cannot change your vote!")
            return redirect('play')
        
        
        #user_score , _ = PlayerScore.objects.get_or_create(user=request.user)
        user_score, _ = PlayerScore.objects.get_or_create(user=request.user, game=game)
        
        if choice_id == 0 : 
            user_score.points += 2 
        else : 
            bluff = KalakBluff.objects.get(id=choice_id)
            bluff.voters.add(request.user)

            #author of bluff get points

            #liar_score , _ = PlayerScore.objects.get_or_create(user=bluff.player)
            liar_score, _ = PlayerScore.objects.get_or_create(user=bluff.player, game=game)
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
        return redirect('play')
    

class AdvancePhaseView(LoginRequiredMixin,View) : 

    def post(self, request): 

        game = Game.objects.get(id=1)
        if game.kalak_phase == 'WRITING' : 
            game.kalak_phase = 'VOTING'
        elif game.kalak_phase == 'VOTING' : 
            game.kalak_phase = 'RESULTS'
        game.save()
        return redirect('play')
    
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'

    def get(self, request, *args, **kwargs):
        if 'room_code' in request.session:
            game = get_current_game(request)
            if game:
                return redirect('lobby')
            
        return super().get(request, *args, **kwargs)

class KalakConfigView(LoginRequiredMixin, View):
    def get(self, request):
        config, _ = KalakConfig.objects.get_or_create(id=1)
        return render(request, 'core/kalak_config.html', {'config': config})

    def post(self, request):
        config, _ = KalakConfig.objects.get_or_create(id=1)
        
        config.system_prompt = request.POST.get('system_prompt')
        config.categories = request.POST.get('categories')
        config.model = request.POST.get('model_choice')
        config.max_rounds = request.POST.get('max_rounds')
        config.save()
        
        messages.success(request, " Configuration Saved!")
        return redirect('play')
    





#########################################################################################
## users views

from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import SignUpForm
import urllib.parse
from django.contrib.auth import login 


class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()

        user_description = form.cleaned_data.get('avatar_description')        
        encoded_prompt = urllib.parse.quote(user_description)
        avatar_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=300&height=300&nologo=true&seed={user.id}"

        Profile.objects.create(user=user, avatar_url=avatar_url)

        login(self.request, user)

        return super().form_valid(form)
    
    def form_invalid(self, form):
      
        print("FORM IS INVALID") 
        print(form.errors) 
        return super().form_invalid(form)
    



import time



class UpdateAvatarView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        new_desc = request.POST.get('new_desc')
        method = request.POST.get('method') # 'dicebear' or 'ai'
        style = request.POST.get('style')   # 'pixel-art', 'bottts', etc.

        if new_desc:
            encoded_val = urllib.parse.quote(new_desc)
            
            if method == 'ai':
                # AI Beta (Pollinations)
                new_url = f"https://image.pollinations.ai/prompt/{encoded_val}?width=300&height=300&nologo=true&seed={time.time()}"
            else:
                # DiceBear (Instant)
                new_url = f"https://api.dicebear.com/7.x/{style}/svg?seed={encoded_val}"
            
            # Update the model
            profile, created = Profile.objects.get_or_create(user=request.user)            
            profile.avatar_url = new_url
            profile.save()
            
        return redirect('play')