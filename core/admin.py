from django.contrib import admin
from .models import Game, GameConfig, PlayerScore
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

admin.site.register(Game)

admin.site.register(GameConfig)


admin.site.register(PlayerScore)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    def get_username(self, obj):
        data = obj.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            try:
                return User.objects.get(id=user_id).username
            except User.DoesNotExist:
                return "Unknown User"
        return "Anonymous" 

    get_username.short_description = 'User'
    
    list_display = ['session_key', 'get_username', 'expire_date']
    readonly_fields = ['get_username']