from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('django.contrib.auth.urls')),

    path('', views.GameView.as_view(), name='game'),
    path('start/', views.StartRoundView.as_view(), name='start_round'),
    path('api/status/', views.GameStatusView.as_view(), name='game_status'),
    path('settings/', views.ConfigView.as_view(), name='settings'),

    
]