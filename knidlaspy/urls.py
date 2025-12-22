from django.contrib import admin
from django.urls import path, include
from core import views  # Ensure this import is correct

urlpatterns = [
    # --- ADMIN & AUTH ---
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('settings/', views.ConfigView.as_view(), name='settings'),

    # --- MAIN HUB ---
    # The 'GameView' now acts as a traffic controller (Spy vs Kalak)
    path('', views.GameView.as_view(), name='game'),
    
    # This URL lets you switch between Spy and Kalak
    path('switch-game/', views.SwitchGameView.as_view(), name='switch_game'),
    path('api/status/', views.GameStatusView.as_view(), name='game_status'),

    # --- SPY GAME URLS ---
    path('start/', views.StartRoundView.as_view(), name='start_round'),
    path('api/request-vote/', views.RequestVoteView.as_view(), name='request_vote'),
    path('api/confirm-vote/', views.ConfirmVoteView.as_view(), name='confirm_vote'),

    # --- KALAK GAME URLS (New) ---
    path('kalak/start/', views.StartKalakRoundView.as_view(), name='start_kalak'),
    path('kalak/submit/', views.SubmitBluffView.as_view(), name='submit_bluff'),
    path('kalak/vote/', views.VoteKalakView.as_view(), name='vote_kalak'),
    path('kalak/advance/', views.AdvancePhaseView.as_view(), name='advance_phase'),
]