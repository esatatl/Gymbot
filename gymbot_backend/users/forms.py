from django import forms
from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField  # Doğru olan bu

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Kullanıcı Adı'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Şifre'}))
    captcha = CaptchaField()  # Basit kullanımı bu
