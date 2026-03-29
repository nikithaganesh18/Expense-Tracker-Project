from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email',
            'class': 'auth-input',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Choose a username',
                'class': 'auth-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a username',
            'class': 'auth-input',
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Create a password',
            'class': 'auth-input',
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm your password',
            'class': 'auth-input',
        })


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your username',
            'class': 'auth-input',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'auth-input',
        })
    )