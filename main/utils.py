from django.utils import translation
from django.conf import settings
import pycountry
from django.http import HttpRequest
from typing import Optional


def detect_user_language(request: HttpRequest) -> str:
    """
    사용자의 국가와 브라우저 언어를 감지하여 적절한 언어를 반환합니다.
    
    Args:
        request: Django HttpRequest 객체
        
    Returns:
        str: 언어 코드 ('ko' 또는 'en')
    """
    # 1. 세션에서 저장된 언어가 있는지 확인
    if 'django_language' in request.session:
        return request.session['django_language']
    
    # 2. 쿠키에서 언어 설정 확인
    if 'django_language' in request.COOKIES:
        return request.COOKIES['django_language']
    
    # 3. Accept-Language 헤더에서 언어 감지
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    if accept_language:
        # 브라우저 언어 설정에서 한국어가 우선순위가 높으면 한국어 선택
        if 'ko' in accept_language.lower() or 'ko-kr' in accept_language.lower():
            return 'ko'
        # 영어가 있으면 영어 선택
        elif 'en' in accept_language.lower():
            return 'en'
    
    # 4. IP 기반 국가 감지 (간단한 방법)
    # 실제로는 GeoIP 데이터베이스를 사용하는 것이 좋습니다
    client_ip = get_client_ip(request)
    country_code = get_country_from_ip(client_ip)
    
    if country_code:
        # 한국이면 한국어, 그 외에는 영어
        if country_code.upper() == 'KR':
            return 'ko'
        else:
            return 'en'
    
    # 5. 기본값은 한국어
    return 'ko'


def get_client_ip(request: HttpRequest) -> str:
    """
    클라이언트의 IP 주소를 가져옵니다.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_country_from_ip(ip: str) -> Optional[str]:
    """
    IP 주소로부터 국가 코드를 추출합니다.
    실제 구현에서는 GeoIP 데이터베이스를 사용해야 합니다.
    """
    # 간단한 예시 - 실제로는 GeoIP 서비스나 데이터베이스 사용
    # 여기서는 기본값으로 None을 반환
    return None


def set_language(request: HttpRequest, language_code: str) -> None:
    """
    사용자의 언어 설정을 세션과 쿠키에 저장합니다.
    """
    if language_code in [lang[0] for lang in settings.LANGUAGES]:
        request.session['django_language'] = language_code
        translation.activate(language_code)


def get_language_name(language_code: str) -> str:
    """
    언어 코드에 해당하는 언어 이름을 반환합니다.
    """
    language_names = {
        'ko': '한국어',
        'en': 'English'
    }
    return language_names.get(language_code, language_code) 