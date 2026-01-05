from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    avatar_description = forms.CharField(
        max_length=200, 
        required=True,
        help_text="Describe how you want your character to look ",
        widget=forms.TextInput(attrs={'placeholder': 'Describe your avatar...'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('avatar_description',)