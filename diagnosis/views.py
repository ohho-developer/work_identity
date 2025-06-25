import random
import json
import uuid
import os

# Django imports
from django.shortcuts import render, redirect, get_object_or_404 # Keep render for other views
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse # Import reverse for URL lookups
from django.contrib.auth.decorators import login_required

# Model imports
from .models import Question, Result, Axis

# Language detection imports
from main.utils import detect_user_language, set_language, get_language_name

# Firebase related imports and initialization removed as Firebase is not used.
print("Firebase is not configured or used in this application.")

db = None # Ensure db is None


def index(request):
    """Renders the landing page."""
    # 사용자 언어 감지
    user_language = detect_user_language(request)
    set_language(request, user_language)
    
    context = {
        'current_language': user_language,
        'language_name': get_language_name(user_language),
    }
    
    # Use render to display the index.html template
    return render(request, 'diagnosis/home.html', context)


def survey_start(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        newsletter_consent = request.POST.get('newsletter_consent') == 'on'
        # 기존 설문 결과가 있으면 해당 UUID로 결과 페이지 이동
        result = Result.objects.filter(user_email=email).order_by('-created_at').first()
        if result:
            return redirect(reverse('diagnosis:result', args=[result.id]))
        # 없으면 새 설문 생성 후 설문 시작
        new_result = Result.objects.create(
            user_email=email,
            responses_json={},
            scores_json=None,
            newsletter_consent=newsletter_consent,
            final_type_axis=Axis.objects.first()
        )
        return redirect(reverse('diagnosis:survey', args=[new_result.id]))
    # 언어 context 기본값 처리
    user_language = request.session.get('django_language', 'ko')
    return render(request, 'diagnosis/survey_start.html', {'current_language': user_language})


def survey(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    user_language = detect_user_language(request)
    questions = list(Question.objects.all())
    context = {
        'questions': questions,
        'result_id': result_id,
        'current_language': user_language,
    }
    return render(request, 'diagnosis/survey.html', context)


@require_POST
def submit_survey(request):
    try:
        data = json.loads(request.body)
        responses = data.get('responses', {})
        result_id = data.get('result_id')
        if not responses or not result_id:
            return JsonResponse({'status': 'error', 'message': '응답 또는 result_id가 없습니다.'}, status=400)
        result = get_object_or_404(Result, id=result_id)
        # 점수 계산 및 저장
        scores = {'P': 0, 'I': 0, 'D': 0, 'N': 0, 'C': 0, 'H': 0, 'T': 0, 'R': 0}
        question_ids = [int(q_id) for q_id in responses.keys()]
        all_questions = Question.objects.in_bulk(question_ids)
        for q_id_str, answer_value in responses.items():
            q_id = int(q_id_str)
            question = all_questions.get(q_id)
            if question:
                valid_values = {question.option_a_value, question.option_b_value}
                if answer_value in valid_values:
                    scores[answer_value] += 1
        final_type = ''
        final_type += 'P' if scores['P'] >= scores['I'] else 'I'
        final_type += 'D' if scores['D'] >= scores['N'] else 'N'
        final_type += 'C' if scores['C'] >= scores['H'] else 'H'
        final_type += 'T' if scores['T'] >= scores['R'] else 'R'
        axis_object = Axis.objects.filter(code=final_type).first()
        result.responses_json = responses
        result.scores_json = json.dumps(scores)
        result.final_type_axis = axis_object
        result.save()
        result_url = reverse('diagnosis:result', args=[result.id])
        return JsonResponse({'status': 'success', 'redirect_url': result_url})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def result(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    # 언어 감지
    user_language = detect_user_language(request)
    # 결과가 없거나 설문이 끝나지 않은 경우 예외 처리
    if not result.scores_json or not result.final_type_axis:
        return render(request, 'diagnosis/result.html', {'result': result, 'no_result': True, 'current_language': user_language})

    scores = result.scores_json if isinstance(result.scores_json, dict) else json.loads(result.scores_json)
    final_type = result.final_type_axis.code if result.final_type_axis else "Unknown"
    type_title = result.final_type_axis.name if result.final_type_axis else ""
    type_description = result.final_type_axis.description if result.final_type_axis else ""
    work_style = result.final_type_axis.work_style if result.final_type_axis else ""
    work_condition = result.final_type_axis.work_condition if result.final_type_axis else ""
    work_develop = result.final_type_axis.work_develop if result.final_type_axis else ""
    work_communication = result.final_type_axis.work_communication if result.final_type_axis else ""

    # 축별 점수 계산
    axis_data = {}
    # PI
    p_score = scores.get('P', 0)
    i_score = scores.get('I', 0)
    total_pi = p_score + i_score
    p_percentage = (p_score / total_pi) * 100 if total_pi > 0 else 50
    axis_data['PI'] = {'i_percentage': 100-round(p_percentage)}
    # DN
    d_score = scores.get('D', 0)
    n_score = scores.get('N', 0)
    total_dn = d_score + n_score
    d_percentage = (d_score / total_dn) * 100 if total_dn > 0 else 50
    axis_data['DN'] = {'n_percentage': 100-round(d_percentage)}
    # CH
    c_score = scores.get('C', 0)
    h_score = scores.get('H', 0)
    total_ch = c_score + h_score
    c_percentage = (c_score / total_ch) * 100 if total_ch > 0 else 50
    axis_data['CH'] = {'h_percentage': 100-round(c_percentage)}
    # TR
    t_score = scores.get('T', 0)
    r_score = scores.get('R', 0)
    total_tr = t_score + r_score
    t_percentage = (t_score / total_tr) * 100 if total_tr > 0 else 50
    axis_data['TR'] = {'r_percentage': 100-round(t_percentage)}

    context = {
        'result': result,
        'final_type': final_type,
        'type_title': type_title,
        'type_description': type_description,
        'work_style': work_style,
        'work_condition': work_condition,
        'work_develop': work_develop,
        'work_communication': work_communication,
        'axis_data': axis_data,
        'no_result': False,
        'current_language': user_language,
    }
    return render(request, 'diagnosis/result.html', context)


def retry_survey(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    email = result.user_email
    # 기존 설문 삭제
    result.delete()
    # 설문 시작 페이지로 이동 (이메일을 쿼리 파라미터로 전달)
    return redirect(f"{reverse('diagnosis:survey_start')}?email={email}")


def contact_view(request):
    """Handles contact form submission and renders the contact page."""
    # 사용자 언어 감지
    user_language = detect_user_language(request)
    set_language(request, user_language)
    
    context = {
        'current_language': user_language,
        'language_name': get_language_name(user_language),
    }
    
    if request.method == 'POST':
        user_email = request.POST.get('user_email', '')
        inquiry_content = request.POST.get('inquiry_content', '')

        # Basic validation
        if not user_email or not inquiry_content:
            # Render contact page with an error message
            error_message = '이메일 주소와 문의 내용을 모두 입력해주세요.' if user_language == 'ko' else 'Please enter both email address and inquiry content.'
            context.update({
                'error_message': error_message,
                'user_email': user_email,
                'inquiry_content': inquiry_content
            })
            return render(request, 'diagnosis/contact.html', context)

        # Define email parameters (similar to send_inquiry_email)
        subject = '[업무 정체성 진단] 문의 접수' if user_language == 'ko' else '[Work Identity Diagnosis] Inquiry Received'
        message = f'''보낸 사람: {user_email}

                        문의 내용:
                        {inquiry_content}''' if user_language == 'ko' else f'''From: {user_email}

                        Inquiry Content:
                        {inquiry_content}'''
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['info@designusplus.com']

        try:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
            # Render contact page with a success message
            success_message = '문의 메일이 성공적으로 발송되었습니다.' if user_language == 'ko' else 'Inquiry email has been sent successfully.'
            context['success_message'] = success_message
            return render(request, 'diagnosis/contact.html', context)

        except Exception as e:
            print(f"Error sending contact email: {e}")
            # Render contact page with an error message
            error_message = '문의 메일 발송에 실패했습니다.' if user_language == 'ko' else 'Failed to send inquiry email.'
            context.update({
                'error_message': error_message,
                'user_email': user_email, 
                'inquiry_content': inquiry_content
            })
            return render(request, 'diagnosis/contact.html', context)

    else: # Handle GET requests
        return render(request, 'diagnosis/contact.html', context)

@require_POST
def request_report(request):
    """Receives result ID and email, updates the Result object, and triggers email sending."""
    try:
        data = json.loads(request.body)
        result_id_str = data.get('result_id')
        user_email = data.get('email')
        newsletter_consent = data.get('newsletter_consent', False)

        # Basic validation
        if not result_id_str or not user_email:
            return JsonResponse({'status': 'error', 'message': 'Result ID and email are required.'}, status=400)

        try:
            # Retrieve the Result object
            result = Result.objects.get(id=result_id_str)
            # Update email and newsletter consent
            result.user_email = user_email
            result.newsletter_consent = newsletter_consent
            result.save()
 # Email sending is not implemented here

            return JsonResponse({'status': 'success'})

        except Result.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Result not found.'}, status=404)
        except Exception as e:
            print(f"Error processing report request: {e}")
            return JsonResponse({'status': 'error', 'message': 'An internal server error occurred.'}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        print(f"Unexpected error in request_report: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'}, status=500)

@login_required
def diagnosis_list(request):
    """사용자의 진단 결과 목록을 보여줍니다."""
    results = Result.objects.filter(user_email=request.user.email).order_by('-created_at')
    return render(request, 'diagnosis/diagnosis_list.html', {'results': results})

@login_required
def start_diagnosis(request):
    """새로운 진단을 시작합니다."""
    if request.method == 'POST':
        # 새로운 Result 객체 생성
        result = Result.objects.create(
            user_email=request.user.email,
            responses_json={},
            scores_json={},
            newsletter_consent=request.POST.get('newsletter_consent', False)
        )
        return redirect('diagnosis:question_view', question_id=1)
    return render(request, 'diagnosis/start_diagnosis.html')

@login_required
def question_view(request, question_id):
    """질문을 보여주고 답변을 받습니다."""
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        result_id = request.POST.get('result_id')
        result = get_object_or_404(Result, id=result_id, user_email=request.user.email)
        
        # 답변 저장
        responses = json.loads(result.responses_json)
        responses[str(question_id)] = request.POST.get('answer')
        result.responses_json = json.dumps(responses)
        result.save()
        
        # 다음 질문으로 이동
        next_question = Question.objects.filter(id__gt=question_id).first()
        if next_question:
            return redirect('diagnosis:question_view', question_id=next_question.id)
        else:
            # 모든 질문이 완료되면 결과 계산
            calculate_result(result)
            return redirect('diagnosis:result_view', result_id=result.id)
    
    return render(request, 'diagnosis/question.html', {
        'question': question,
        'result_id': request.GET.get('result_id')
    })

@login_required
def result_view(request, result_id):
    """진단 결과를 보여줍니다."""
    result = get_object_or_404(Result, id=result_id, user_email=request.user.email)
    return render(request, 'diagnosis/result.html', {'result': result})

def calculate_result(result):
    """응답을 기반으로 결과를 계산합니다."""
    responses = json.loads(result.responses_json)
    scores = {}
    
    # 각 축별 점수 계산
    for question_id, answer in responses.items():
        question = Question.objects.get(id=question_id)
        if answer == 'A':
            value = question.option_a_value
        else:
            value = question.option_b_value
        scores[value] = scores.get(value, 0) + 1
    
    # 최종 유형 결정
    final_type = determine_final_type(scores)
    result.scores_json = json.dumps(scores)
    result.final_type_axis = final_type
    result.save()

def determine_final_type(scores):
    """점수를 기반으로 최종 유형을 결정합니다."""
    # 여기에 유형 결정 로직 구현
    # 예시: 가장 높은 점수를 가진 축을 선택
    max_score = max(scores.items(), key=lambda x: x[1])
    return Axis.objects.get(code__startswith=max_score[0])
