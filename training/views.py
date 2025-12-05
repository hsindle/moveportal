# training/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Course, UserAttempt, Question, OnboardingDocument # All required models imported
from accounts.models import CustomUser # Ensure CustomUser is imported
from .forms import OnboardingForm


# --- HELPER: Role Check (assuming this is copied or accessible) ---
def is_manager_or_supervisor(user):
    """Returns True if user is Manager or Supervisor."""
    return user.groups.filter(name__in=["Manager", "Supervisor"]).exists()
# ----------------------------------------------------------------


@login_required
def training_dashboard(request):
    """Staff landing page: shows required courses and completion status."""
    user = request.user
    user_groups = user.groups.all()
    
    # Check Onboarding Status
    onboarding_needed = False
    is_security = user.groups.filter(name='Security').exists()
    
    if not is_security:
        try:
            doc = OnboardingDocument.objects.get(user=user)
            if not doc.is_completed:
                onboarding_needed = True
        except OnboardingDocument.DoesNotExist:
            onboarding_needed = True # Document hasn't even been created yet
    
    # Find courses required for ANY group the user belongs to
    required_courses = Course.objects.filter(required_for_groups__in=user_groups).distinct()
    
    courses_data = []
    now = timezone.now()
    
    for course in required_courses:
        # Get the latest PASSED attempt for expiration checks
        try:
            latest_attempt = UserAttempt.objects.filter(user=user, course=course, is_passed=True).latest('date_completed')
        except UserAttempt.DoesNotExist:
            latest_attempt = None
            
        is_completed = latest_attempt is not None
        
        # Check for expiration and override is_completed status (Renewal Logic)
        if is_completed and course.is_recurring:
            # If renewal date is past current time, the completion is invalid
            if latest_attempt.renewal_due_date and latest_attempt.renewal_due_date < now:
                is_completed = False 
                messages.warning(request, f"Action Required: '{course.title}' expired on {latest_attempt.renewal_due_date.strftime('%B %d, %Y')}.")

        courses_data.append({
            'course': course,
            'is_completed': is_completed,
            'latest_attempt': latest_attempt,
        })
        
    context = {
        'courses_data': courses_data,
        'is_manager': is_manager_or_supervisor(user),
        'onboarding_needed': onboarding_needed, # 🚨 CRITICAL CONTEXT VARIABLE 🚨
    }
    return render(request, 'training/training_dashboard.html', context)


@login_required
def course_detail(request, course_id):
    """Shows video and quiz introduction before starting the module."""
    from .models import Course
    course = get_object_or_404(Course, pk=course_id)
    
    # Check if the user is authorized (safety check)
    if not course.required_for_groups.filter(user=request.user).exists():
        messages.error(request, "This training is not required for your role.")
        return redirect('training:training_dashboard')
        
    context = {
        'course': course
    }
    return render(request, 'training/course_detail.html', context)


@login_required
def course_start(request, course_id):
    """Presents the quiz questions associated with a course."""
    course = get_object_or_404(Course, pk=course_id)
    
    # Check if the user is authorized to take this course (optional, but safe)
    if not course.required_for_groups.filter(user=request.user).exists():
        messages.error(request, "This training is not required for your role.")
        return redirect('training:training_dashboard')
        
    questions = course.questions.all()

    context = {
        'course': course,
        'questions': questions
    }
    return render(request, 'training/quiz_form.html', context)


@login_required
def quiz_submit(request, course_id):
    """Processes quiz answers, calculates score, and saves UserAttempt."""
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    
    if request.method != 'POST':
        return redirect('training:course_detail', course_id=course_id)

    # 1. Score Calculation
    questions = course.questions.all()
    total_questions = questions.count()
    correct_count = 0
    
    for question in list(questions): 
        submitted_answer = request.POST.get(f'q_{question.id}')
        
        if submitted_answer and submitted_answer == question.correct_answer:
            correct_count += 1
            
    # 2. Determine Pass/Fail (80% Pass Threshold)
    PASS_THRESHOLD = 80
    score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    is_passed = score_percentage >= PASS_THRESHOLD

    # 3. Save User Attempt History
    
    # The UserAttempt model's save method calculates the renewal_due_date based on is_passed and is_recurring.
    UserAttempt.objects.create(
        user=user,
        course=course,
        is_passed=is_passed,
        score=correct_count,
        date_completed=timezone.now()
    )

    # 4. Provide Feedback and Redirect
    if is_passed:
        messages.success(request, f"Congratulations! You passed '{course.title}' with a score of {score_percentage:.0f}%.")
    else:
        messages.error(request, f"You failed '{course.title}' with a score of {score_percentage:.0f}%. Please review the materials and try again.")
        
    return redirect('training:training_dashboard')


@login_required
def manager_training_admin(request):
    """Redirects managers to the Django Admin page for Course management."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('training:training_dashboard')
        
    # Redirect to the main Django Admin page for Course management
    return redirect(reverse('admin:training_course_changelist'))


@login_required
def manager_training_list(request):
    """Manager entry point: Lists all courses for editing."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('training:training_dashboard')
    
    courses = Course.objects.all().order_by('title')
    
    context = {
        'courses': courses
    }
    return render(request, 'training/course_admin_list.html', context)


@login_required
def course_admin_edit(request, course_id=None):
    """Handles Course creation and editing, along with inline Question editing."""
    from .forms import CourseForm, QuestionFormSet # Import forms locally
    
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('training:training_dashboard')

    instance = get_object_or_404(Course, pk=course_id) if course_id else None
    
    if request.method == 'POST':
        course_form = CourseForm(request.POST, instance=instance)
        formset = QuestionFormSet(request.POST, instance=instance)
        
        if course_form.is_valid() and formset.is_valid():
            # 1. Save Course
            course = course_form.save()
            
            # 2. Save Questions (Formset)
            formset.instance = course
            formset.save()
            
            messages.success(request, f"Course '{course.title}' and quiz questions saved successfully.")
            return redirect('training:manager_training_list')
    else:
        course_form = CourseForm(instance=instance)
        formset = QuestionFormSet(instance=instance)
        
    context = {
        'course_form': course_form,
        'formset': formset,
        'is_new': instance is None,
        'page_title': "Create New Course" if instance is None else f"Edit Course: {instance.title}",
    }
    return render(request, 'training/course_admin_form.html', context)

@login_required
def user_training_history(request, user_id):
    """
    Displays ALL required training history (completed and incomplete) for a specific user.
    Manager/Supervisor access only.
    """
    # 1. Access Control
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('training:training_dashboard')
        
    target_user = get_object_or_404(CustomUser, pk=user_id)
    user_groups = target_user.groups.all()
    
    # 2. Fetch ALL courses required for ANY of the target user's groups
    required_courses = Course.objects.filter(required_for_groups__in=user_groups).distinct().order_by('title')
    
    history_data = []
    now = timezone.now()
    
    for course in required_courses:
        
        # 3. Fetch the LATEST attempt (passed or failed) for score/date display
        try:
            # We fetch the absolute latest attempt date (passed or failed)
            latest_attempt = UserAttempt.objects.filter(user=target_user, course=course).latest('date_completed')
        except UserAttempt.DoesNotExist:
            latest_attempt = None

        # 4. Determine Compliance Status based on the latest attempt (must be passed and unexpired)
        
        # Did the user ever pass it?
        has_passed = UserAttempt.objects.filter(user=target_user, course=course, is_passed=True).exists()
        
        is_completed = False
        renewal_due_date = None

        if has_passed:
            # Get the latest PASSED attempt for accurate renewal date calculation
            latest_passed_attempt = UserAttempt.objects.filter(user=target_user, course=course, is_passed=True).latest('date_completed')
            
            renewal_due_date = latest_passed_attempt.renewal_due_date
            is_completed = True

            # Check Expiration (only for recurring courses)
            if course.is_recurring and renewal_due_date and renewal_due_date < now:
                is_completed = False # Expired
                messages.warning(request, f"'{course.title}' expired for {target_user.username}.")


        history_data.append({
            'course': course,
            'is_completed': is_completed, # Overall compliance status
            'renewal_due_date': renewal_due_date,
            
            # Data pulled from the LATEST attempt (passed, failed, or just the date)
            'last_completed': latest_attempt.date_completed if latest_attempt else None,
            'score': latest_attempt.score if latest_attempt else None,
        })
        
    context = {
        'target_user': target_user,
        'attempts': history_data, # Pass the aggregated history data
    }
    return render(request, 'training/user_training_history.html', context)

@login_required
def onboarding_start(request):
    """
    Handles the submission of the mandatory staff onboarding document.
    """
    user = request.user
    
    # 1. Check if user is Security (who are exempt)
    if user.groups.filter(name='Security').exists():
        messages.info(request, "Onboarding document is not required for your role.")
        return redirect('training:training_dashboard')
        
    # 2. Check if document is already completed
    try:
        doc = OnboardingDocument.objects.get(user=user)
        if doc.is_completed:
            messages.success(request, "Your onboarding document is already complete.")
            return redirect('training:training_dashboard')
    except OnboardingDocument.DoesNotExist:
        doc = None

    # 3. Initialize Form (Pre-fill name from current user profile)
    initial_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
    }

    if request.method == 'POST':
        form = OnboardingForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            onboarding_doc = form.save(commit=False)
            
            # Update user's official name from the confirmed form data
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            
            # Save Document
            onboarding_doc.user = user
            onboarding_doc.is_completed = True
            onboarding_doc.save()
            
            messages.success(request, "Onboarding Document submitted successfully.")
            return redirect('training:training_dashboard')
    else:
        form = OnboardingForm(instance=doc, initial=initial_data)
        
    return render(request, 'training/onboarding_form.html', {'form': form, 'user': user})
