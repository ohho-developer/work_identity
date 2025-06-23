from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm, ProfileUpdateForm
from django.http import HttpResponse
from django.utils import translation
from django.conf import settings
from .utils import detect_user_language, set_language, get_language_name
from django.utils.translation import gettext as _

# Create your views here.

def set_language_view(request):
    """
    언어 전환을 위한 뷰
    """
    if request.method == 'POST':
        language_code = request.POST.get('language')
        if language_code in [lang[0] for lang in settings.LANGUAGES]:
            set_language(request, language_code)
            # 현재 페이지로 리다이렉트
            next_url = request.POST.get('next', '/')
            response = redirect(next_url)
            response.set_cookie('django_language', language_code)
            return response
    
    return redirect('/')

def home(request):
    """
    홈페이지 뷰 - 언어 감지 기능 포함
    """
    # 사용자 언어 감지
    user_language = detect_user_language(request)
    set_language(request, user_language)
    
    context = {
        'current_language': user_language,
        'available_languages': settings.LANGUAGES,
        'language_name': get_language_name(user_language),
    }
    
    return render(request, 'main/home.html', context)

def about(request):
    """
    소개 페이지 뷰
    """
    user_language = detect_user_language(request)
    set_language(request, user_language)
    
    context = {
        'current_language': user_language,
        'available_languages': settings.LANGUAGES,
        'language_name': get_language_name(user_language),
    }
    
    return render(request, 'main/about.html', context)

def contact(request):
    """
    연락처 페이지 뷰
    """
    user_language = detect_user_language(request)
    set_language(request, user_language)
    
    context = {
        'current_language': user_language,
        'available_languages': settings.LANGUAGES,
        'language_name': get_language_name(user_language),
    }
    
    return render(request, 'main/contact.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, '로그인되었습니다.')
            return redirect('home')
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    
    return render(request, 'accounts/login.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '회원가입이 완료되었습니다.')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, '로그아웃되었습니다.')
    return redirect('home')

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'accounts/profile.html', context)
