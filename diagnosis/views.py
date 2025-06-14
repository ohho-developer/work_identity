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

# Firebase related imports and initialization removed as Firebase is not used.
print("Firebase is not configured or used in this application.")

db = None # Ensure db is None


def index(request):
    """Renders the landing page."""
    # Use render to display the index.html template
    return render(request, 'diagnosis/home.html')


def survey(request):
    """Retrieves questions and returns survey data as JSON."""
    # Fetch questions and select related axis for efficiency using Django ORM
    questions = list(Question.objects.all())
    random.shuffle(questions) # Shuffle questions
    # For temporary testing with 5 questions, you might slice the list here
    # questions = questions[:5]

    # Prepare questions data as a list of dictionaries
    questions_data = [
        {
            'id': q.id,
            'text': q.text,
            'option_a': q.option_a,
            'option_a_value': q.option_a_value,
            'option_b': q.option_b,
            'option_b_value': q.option_b_value,
        }
        for q in questions
    ]

    # Prepare axis information as a list of dictionaries
    axes_data = [
        {
            'code': axis.code,
            'name': axis.name,
        }
        for axis in Axis.objects.all()
    ]

    # Return data as JSON response
    # The frontend JavaScript will fetch this data and populate the survey page
    return render(request, 'diagnosis/survey.html', {
 'questions': questions_data, # Send questions_data directly
 'axes': axes_data,         # Send axes_data directly
    })



@require_POST
def submit_survey(request):
    """Receives survey responses, calculates and saves to Django DB, and redirects to result page."""

    try:
        data = json.loads(request.body)
        responses = data.get('responses', {}) # Should be a dict like {'q_id_1': 'P', 'q_id_2': 'D', ...}

        # Basic validation
        if not responses: # Only responses are required for initial save
            return JsonResponse({'status': 'error', 'message': 'No responses received.'}, status=400)

        # Validate response data format: keys are integers, values are single characters
        valid_response_values = set('PIDNCHTR') # Set of all possible single-character values
        for q_id_str, answer_value in responses.items():
            try:
                # Check if key is a valid integer
                int(q_id_str)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': f'Invalid question ID format: {q_id_str}. Question IDs must be integers.'}, status=400)
            
            # Check if value is a single character and one of the expected values
            if not isinstance(answer_value, str) or len(answer_value) != 1 or answer_value not in valid_response_values:
                return JsonResponse({'status': 'error', 'message': f'Invalid answer value for question ID {q_id_str}: {answer_value}. Answer values must be a single character from {list(valid_response_values)}.'}, status=400)


        # --- Save to Django Result Model ---
        try:
            # Recalculate scores using validated responses
            scores = {'P': 0, 'I': 0, 'D': 0, 'N': 0, 'C': 0, 'H': 0, 'T': 0, 'R': 0}
            question_ids = [int(q_id_str) for q_id_str in responses.keys()] # Use .keys() to iterate over response dictionary keys and convert to int
            all_questions = Question.objects.in_bulk(question_ids)

            for q_id_str, answer_value in responses.items():
                q_id = int(q_id_str)
                question = all_questions.get(q_id)
                if isinstance(question, Question): # Ensure 'question' is a Question object
                     valid_values = {question.option_a_value, question.option_b_value}
                     if answer_value in valid_values:
                        scores[answer_value] += 1
            # Recalculate final_type based on recalculated scores as well
            final_type_to_save = ""
            final_type_to_save += 'P' if scores.get('P', 0) >= scores.get('I', 0) else 'I'
            final_type_to_save += 'D' if scores.get('D', 0) >= scores.get('N', 0) else 'N'
            final_type_to_save += 'C' if scores.get('C', 0) >= scores.get('H', 0) else 'H'
            final_type_to_save += 'T' if scores.get('T', 0) >= scores.get('R', 0) else 'R'

            # Log the scores dictionary before saving
            print(f"Scores before saving: {scores}")

            # Prepare scores_json for saving: use None if scores dict is empty, otherwise dump to JSON
            scores_json_to_save = json.dumps(scores) if scores else None

            # Find the corresponding Axis object
            axis_object = None # Initialize axis_object to None
            try:
                axis_object = Axis.objects.get(code=final_type_to_save)
            except Axis.DoesNotExist:
                print(f"Warning: Axis with code {final_type_to_save} not found. Proceeding without assigning final_type_axis.")
                # axis_object remains None, which is allowed if the foreign key is nullable

            # Create the Result object and get the created instance
            created_result = Result.objects.create(
                user_email='', # Email is not collected during initial submission
                responses_json=responses, # Store raw responses
                scores_json=scores_json_to_save,
                newsletter_consent=False, # Initial save sets consent to False
                final_type_axis=axis_object, # Assign the found Axis object or None
                # created_at is set automatically
            )
            result_id_to_redirect = str(created_result.id)

        except Exception as db_error:
            print(f"Error saving result to Django DB: {db_error}")
            # If Django DB save failed, return an error response
            return JsonResponse({'status': 'error', 'message': 'Failed to save result to the database.'}, status=500)

        # Redirect to the result page if save was successful
        # Use the UUID of the created Result object for the URL
        result_url = reverse('diagnosis:result', args=[result_id_to_redirect]) # Use namespace
        return JsonResponse({'status': 'success', 'redirect_url': result_url})


    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        print(f"Error in submit_survey: {e}")
        # In production, log the error properly
        return JsonResponse({'status': 'error', 'message': 'An internal server error occurred.'}, status=500)


def contact_view(request):
    """Handles contact form submission and renders the contact page."""
    if request.method == 'POST':
        user_email = request.POST.get('user_email', '')
        inquiry_content = request.POST.get('inquiry_content', '')

        # Basic validation
        if not user_email or not inquiry_content:
            # Render contact page with an error message
            return render(request, 'diagnosis/contact.html', {
                'error_message': '이메일 주소와 문의 내용을 모두 입력해주세요.',
                'user_email': user_email,
                'inquiry_content': inquiry_content
            })

        # Define email parameters (similar to send_inquiry_email)
        subject = '[업무 정체성 진단] 문의 접수'
        message = f'''보낸 사람: {user_email}

                        문의 내용:
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
            return render(request, 'diagnosis/contact.html', {'success_message': '문의 메일이 성공적으로 발송되었습니다.'})

        except Exception as e:
            print(f"Error sending contact email: {e}")
            # Render contact page with an error message
            return render(request, 'diagnosis/contact.html', {
                'error_message': '문의 메일 발송에 실패했습니다.',
                'user_email': user_email, 'inquiry_content': inquiry_content})

    else: # Handle GET requests
        return render(request, 'diagnosis/contact.html')

def result(request, result_id):
    """Fetches result from Django DB and renders the result page."""
    # This view now handles displaying the result and the email input form.
    # Firebase is not used, so only fetch from Django DB.

    try:
        # Ensure result_id is a valid UUID before querying Django DB and fetch the result
        uuid_result_id = uuid.UUID(result_id) # Validate and convert to UUID object
        # Fetch the result object or return 404 if not found
        django_result = get_object_or_404(Result, id=uuid_result_id)

        print(f"Result ID {result_id} found in Django DB.")

        # Populate data from Django DB object
        final_type = django_result.final_type_axis.code if django_result.final_type_axis else "Unknown" # Get code from linked Axis
        scores = json.loads(django_result.scores_json) if django_result.scores_json else {} # Explicitly load JSON and handle potential None
        user_email = django_result.user_email
        
        # Extract the part before '@' from the email, if it exists
        user_id = ""
        if user_email and '@' in user_email:
            user_id = user_email.split('@')[0]
        
        # --- Result type title and description ---
        # Use the linked Axis object to get title and description
        # Access the linked Axis model through the final_type_axis foreign key
        type_title = django_result.final_type_axis.name.split('(')[0] # Use axis name
        type_subtitle = django_result.final_type_axis.name.split('(')[1].split(')')[0] # Use axis code for subtitle
        type_description = django_result.final_type_axis.description.split('한마디로')[0] # Use the description from the Axis model
        type_one_sentence = django_result.final_type_axis.description.split('"')[1].split('"')[0]
        work_style = django_result.final_type_axis.work_style
        work_condition = django_result.final_type_axis.work_condition
        work_develop = django_result.final_type_axis.work_develop
        work_communication = django_result.final_type_axis.work_communication
        # Fetch Axis names and details for chart labels from Django Model

        # Define axis labels for the chart
        axis_labels = {
            'PI': {'left': '적응형', 'right': '계획형'},
            'DN': {'left': '데이터 기반', 'right': '직관 기반'},
            'CH': {'left': '명료화형', 'right': '조화형'},
            'TR': {'left': '성과 중심', 'right': '관계 중심'},
        }
        axis_data = {}

        # Work Process (P vs I)
        p_score = scores.get('P', 0)
        i_score = scores.get('I', 0)
        total_pi = p_score + i_score
        p_percentage = (p_score / total_pi) * 100 if total_pi > 0 else 50
        dominant_pi_type = '계획형' if p_score >= i_score else '적응형'
        dominant_pi_percentage = p_percentage if p_score >= i_score else 100 - p_percentage
        axis_data['PI'] = {'dominant_type': dominant_pi_type, 'percentage': round(dominant_pi_percentage), 'i_percentage': 100-round(p_percentage)}

        # Decision-Making (D vs N)
        d_score = scores.get('D', 0)
        n_score = scores.get('N', 0)
        total_dn = d_score + n_score
        d_percentage = (d_score / total_dn) * 100 if total_dn > 0 else 50
        dominant_dn_type = '데이터 기반' if d_score >= n_score else '직관 기반'
        dominant_dn_percentage = d_percentage if d_score >= n_score else 100 - d_percentage
        axis_data['DN'] = {'dominant_type': dominant_dn_type, 'percentage': round(dominant_dn_percentage), 'n_percentage': 100-round(d_percentage)}

        # Communication Orientation (C vs H)
        c_score = scores.get('C', 0)
        h_score = scores.get('H', 0)
        total_ch = c_score + h_score
        c_percentage = (c_score / total_ch) * 100 if total_ch > 0 else 50
        dominant_ch_type = '명료화형' if c_score >= h_score else '조화형'
        dominant_ch_percentage = c_percentage if c_score >= h_score else 100 - c_percentage
        axis_data['CH'] = {'dominant_type': dominant_ch_type, 'percentage': round(dominant_ch_percentage), 'h_percentage': 100-round(c_percentage)}

        # Work Motivation (T vs R)
        t_score = scores.get('T', 0)
        r_score = scores.get('R', 0)
        total_tr = t_score + r_score
        t_percentage = (t_score / total_tr) * 100 if total_tr > 0 else 50
        dominant_tr_type = '성과 중심' if t_score >= r_score else '관계 중심'
        dominant_tr_percentage = t_percentage if t_score >= r_score else 100 - t_percentage
        axis_data['TR'] = {'dominant_type': dominant_tr_type, 'percentage': round(dominant_tr_percentage), 'r_percentage': 100-round(t_percentage)}

        print(f"Calculated axis data: {axis_data}") # Log the calculated data

        # Prepare the context dictionary to pass data to the template
        # Prepare the context dictionary to pass data to the template
        context = {
            'result_id': result_id,
            'final_type': final_type, # Passed to template
            'type_title': type_title, # Passed to template (from ResultTypeInfo or placeholder)
            'type_subtitle': type_subtitle, # Passed to template
            'type_description': type_description, # Passed to template (from ResultTypeInfo or placeholder)
            'type_one_sentence' : type_one_sentence,
            'scores': scores, # Pass raw scores as JSON string
            'axis_labels': json.dumps(axis_labels), # Pass chart labels as JSON string
            'user_id': user_id, # Pass the extracted user ID
            'work_style': work_style, # Add work_style
            'work_condition': work_condition, # Add work_condition
            'work_develop': work_develop, # Add work_develop
            'work_communication': work_communication, # Add work_communication
            'axis_data':axis_data
        }

        # Render the result template with the context data
        return render(request, 'diagnosis/result.html', context)

    except ValueError:
         # Handle case where the result_id from the URL is not a valid UUID format
         print(f"Invalid UUID format for result_id: {result_id}")
         return render(request, 'diagnosis/404.html', {'message': 'Result not found or invalid format.'}, status=404)

    except Exception as e:
        # Catch any other unexpected errors during the view execution
        print(f"Error in result view for ID {result_id}: {e}")
        # In production, log the error properly
        return render(request, 'diagnosis/error.html', {'message': 'An internal server error occurred while fetching the result.'}, status=500)

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
