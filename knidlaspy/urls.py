from django.contrib import admin
from django.urls import path, include
from core import views  # Ensure this import is correct

urlpatterns = [
    # --- ADMIN & AUTH ---
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('settings/', views.ConfigView.as_view(), name='settings'),
    path('signup/', views.SignUpView.as_view(), name='signup'), 
    path('update-avatar/', views.UpdateAvatarView.as_view(), name='update_avatar'),

    # --- MAIN HUB ---
    path('', views.HomeView.as_view(), name='home'),    
    
    path('play/', views.GameView.as_view(), name='play'),

    path('switch-game/', views.SwitchGameView.as_view(), name='switch_game'),
    
    path('api/status/', views.GameStatusView.as_view(), name='game_status'),
    
    # --- SPY GAME URLS ---
    path('start/', views.StartRoundView.as_view(), name='start_round'),

    # --- KALAK GAME URLS ---
    path('kalak/start/', views.StartKalakRoundView.as_view(), name='start_kalak'),
    path('kalak/submit/', views.SubmitBluffView.as_view(), name='submit_bluff'),
    path('kalak/vote/', views.VoteKalakView.as_view(), name='vote_kalak'),
    path('kalak/advance/', views.AdvancePhaseView.as_view(), name='advance_phase'),
    path('kalak/config/', views.KalakConfigView.as_view(), name='kalak_config'),

    # --- LOBBY & ROOMS ---
    path('create-room/', views.CreateRoomView.as_view(), name='create_room'),
    path('join-room/', views.JoinRoomView.as_view(), name='join_room'),
    path('lobby/', views.LobbyView.as_view(), name='lobby'),
    path('kick/<int:player_id>/', views.KickPlayerView.as_view(), name='kick_player'),
    path('leave/', views.LeaveRoomView.as_view(), name='leave_room'),

    path('api/game-status/<str:room_code>/', views.game_data_api, name='game_data_api'),

]