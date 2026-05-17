"""
Traino v2 — assessments/views.py
Handles: student submission, instructor grading,
         assessment creation, MCQ quiz.
"""
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Assessment, Submission, Question, Option, MCQAnswer
from courses.models import Course, Enrollment
from instructor.models import InstructorProfile
from notifications.models import Notification

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
#  STUDENT: Submit Assessment
# ─────────────────────────────────────────────────────────
@login_required
def submit_assessment(request, pk):
    """
    Student submits a file-upload or MCQ assessment.
    Checks: enrollment, is_published, deadline, duplicate graded submission.
    """
    assessment = get_object_or_404(Assessment, pk=pk)

    if not request.user.is_student:
        messages.error(request, 'Only students can submit assessments.')
        return redirect('course_detail', pk=assessment.course.pk)

    # Must be published by admin
    if not assessment.is_published:
        messages.error(request, 'This assessment is not yet available.')
        return redirect('course_detail', pk=assessment.course.pk)

    # Must be enrolled
    if not Enrollment.objects.filter(
        student=request.user, course=assessment.course
    ).exists():
        messages.error(request, 'You must be enrolled in this course to submit.')
        return redirect('course_detail', pk=assessment.course.pk)

    # Check deadline
    if assessment.due_date:
        due = assessment.due_date
        if timezone.is_naive(due):
            due = timezone.make_aware(due)
        if timezone.now() > due:
            messages.error(request, 'The submission deadline has passed.')
            return redirect('course_detail', pk=assessment.course.pk)

    # Existing submission check
    existing = Submission.objects.filter(
        assessment=assessment, student=request.user
    ).first()

    if existing and existing.is_graded:
        messages.warning(
            request,
            'Your submission has already been graded and cannot be replaced.'
        )
        return redirect('course_detail', pk=assessment.course.pk)

    if request.method == 'POST':
        file = request.FILES.get('file')

        if assessment.mode == 'file':
            if not file:
                messages.error(request, 'Please upload your answer file.')
                return render(request, 'assessments/submit.html', {
                    'assessment': assessment,
                    'existing': existing,
                    'questions': None,
                })

            try:
                if existing:
                    existing.file = file
                    existing.is_graded = False
                    existing.marks     = None
                    existing.feedback  = ''
                    existing.save()
                else:
                    Submission.objects.create(
                        assessment=assessment,
                        student=request.user,
                        file=file
                    )

                # Notify instructor
                Notification.objects.create(
                    recipient=assessment.course.instructor.user,
                    title='New Assessment Submission',
                    message=(
                        f'{request.user.username} submitted '
                        f'"{assessment.title}" in {assessment.course.title}.'
                    ),
                    notif_type='info',
                    link='/assessments/submissions/',
                )
                messages.success(request, 'Assessment submitted successfully!')

            except DatabaseError as e:
                logger.error(f'Submission save error: {e}')
                messages.error(request, 'Submission failed. Please try again.')

        elif assessment.mode == 'mcq':
            questions = assessment.questions.prefetch_related('options').all()
            total_marks = 0
            obtained    = 0

            try:
                with transaction.atomic():
                    sub = existing or Submission.objects.create(
                        assessment=assessment,
                        student=request.user
                    )
                    MCQAnswer.objects.filter(submission=sub).delete()

                    for q in questions:
                        selected_id = request.POST.get(f'question_{q.pk}')
                        if selected_id:
                            try:
                                option = Option.objects.get(pk=selected_id, question=q)
                                MCQAnswer.objects.create(
                                    submission=sub,
                                    question=q,
                                    selected=option
                                )
                                total_marks += q.marks
                                if option.is_correct:
                                    obtained += q.marks
                            except Option.DoesNotExist:
                                pass

                    percentage = round((obtained / total_marks * 100), 1) if total_marks else 0
                    sub.marks     = obtained
                    sub.is_graded = True
                    sub.feedback  = f'You scored {obtained}/{total_marks} ({percentage}%)'
                    sub.save()

                    Notification.objects.create(
                        recipient=request.user,
                        title='Quiz Graded Automatically',
                        message=(
                            f'Your quiz "{assessment.title}" was auto-graded: '
                            f'{obtained}/{total_marks} ({percentage}%)'
                        ),
                        notif_type='success',
                        link=f'/courses/{assessment.course.pk}/',
                    )
                    messages.success(
                        request,
                        f'Quiz submitted! You scored {obtained}/{total_marks} ({percentage}%)'
                    )

            except DatabaseError as e:
                logger.error(f'MCQ submission error: {e}')
                messages.error(request, 'Submission failed. Please try again.')

        return redirect('course_detail', pk=assessment.course.pk)

    # GET — show submission form
    questions = assessment.questions.prefetch_related('options').all() \
        if assessment.mode == 'mcq' else None

    return render(request, 'assessments/submit.html', {
        'assessment': assessment,
        'existing':   existing,
        'questions':  questions,
    })


# ─────────────────────────────────────────────────────────
#  STUDENT: Remove Submission (ungraded only)
# ─────────────────────────────────────────────────────────
@login_required
def remove_submission(request, pk):
    """
    Student removes their own ungraded submission so they can resubmit.
    Only allowed if submission is not yet graded.
    POST required for safety.
    """
    submission = get_object_or_404(Submission, pk=pk, student=request.user)

    if submission.is_graded:
        messages.error(request, 'Graded submissions cannot be removed.')
        return redirect('course_detail', pk=submission.assessment.course.pk)

    if request.method == 'POST':
        course_pk = submission.assessment.course.pk
        submission.delete()
        messages.success(request, 'Submission removed. You may resubmit now.')
        return redirect('course_detail', pk=course_pk)

    # GET — redirect back (POST is required)
    return redirect('course_detail', pk=submission.assessment.course.pk)


# ─────────────────────────────────────────────────────────
#  STUDENT: My Submissions
# ─────────────────────────────────────────────────────────
@login_required
def my_submissions(request):
    """
    Student views all their submissions across all courses,
    with marks, feedback and grading status.
    """
    if not request.user.is_student:
        messages.error(request, 'Access denied.')
        return redirect('home')

    submissions = Submission.objects.filter(
        student=request.user
    ).select_related(
        'assessment', 'assessment__course', 'assessment__course__instructor'
    ).order_by('-submitted_at')

    total   = submissions.count()
    graded  = submissions.filter(is_graded=True).count()
    pending = submissions.filter(is_graded=False).count()

    return render(request, 'assessments/my_submissions.html', {
        'submissions': submissions,
        'total':       total,
        'graded':      graded,
        'pending':     pending,
    })


# ─────────────────────────────────────────────────────────
#  INSTRUCTOR: View All Submissions
# ─────────────────────────────────────────────────────────
@login_required
def instructor_submissions(request):
    """
    Shows all student submissions for courses owned by
    the logged-in instructor. Filterable by status.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Access denied.')
        return redirect('home')

    profile = get_object_or_404(InstructorProfile, user=request.user)

    submissions = Submission.objects.filter(
        assessment__course__instructor=profile
    ).select_related(
        'student', 'assessment', 'assessment__course'
    ).order_by('-submitted_at')

    status = request.GET.get('status', 'all')
    if status == 'pending':
        submissions = submissions.filter(is_graded=False)
    elif status == 'graded':
        submissions = submissions.filter(is_graded=True)

    # Count stats always from full queryset (not filtered)
    all_subs = Submission.objects.filter(assessment__course__instructor=profile)
    total   = all_subs.count()
    pending = all_subs.filter(is_graded=False).count()
    graded  = all_subs.filter(is_graded=True).count()

    return render(request, 'assessments/submissions.html', {
        'submissions': submissions,
        'status':      status,
        'total':       total,
        'pending':     pending,
        'graded':      graded,
    })


# ─────────────────────────────────────────────────────────
#  INSTRUCTOR: Grade a Submission
# ─────────────────────────────────────────────────────────
@login_required
def grade_submission(request, pk):
    """
    Instructor reviews a student's file submission and
    assigns marks + written feedback.
    """
    submission = get_object_or_404(Submission, pk=pk)
    profile    = get_object_or_404(InstructorProfile, user=request.user)

    if submission.assessment.course.instructor != profile:
        messages.error(request, 'You are not authorised to grade this submission.')
        return redirect('instructor_submissions')

    if request.method == 'POST':
        marks_str = request.POST.get('marks', '').strip()
        feedback  = request.POST.get('feedback', '').strip()

        if not marks_str:
            messages.error(request, 'Please enter marks before saving.')
            return render(request, 'assessments/grade.html', {'submission': submission})

        try:
            marks = float(marks_str)
            if marks < 0:
                raise ValueError('Marks cannot be negative.')
            if marks > submission.assessment.total_marks:
                raise ValueError(
                    f'Marks cannot exceed {submission.assessment.total_marks}.'
                )

            submission.marks     = marks
            submission.feedback  = feedback
            submission.is_graded = True
            submission.save(update_fields=['marks', 'feedback', 'is_graded'])

            # Notify student
            percentage = round((marks / submission.assessment.total_marks * 100), 1)
            Notification.objects.create(
                recipient=submission.student,
                title='Assessment Graded',
                message=(
                    f'Your submission for "{submission.assessment.title}" '
                    f'has been graded: {marks}/{submission.assessment.total_marks} '
                    f'({percentage}%)'
                ),
                notif_type='success',
                link=f'/courses/{submission.assessment.course.pk}/',
            )

            messages.success(request, 'Submission graded and student notified.')
            return redirect('instructor_submissions')

        except ValueError as e:
            messages.error(request, str(e))
        except DatabaseError as e:
            logger.error(f'Grade submission DB error: {e}')
            messages.error(request, 'Could not save grade. Please try again.')

    return render(request, 'assessments/grade.html', {'submission': submission})


# ─────────────────────────────────────────────────────────
#  INSTRUCTOR: Create Assessment
# ─────────────────────────────────────────────────────────
@login_required
def create_assessment(request, course_id):
    """
    Instructor adds an assignment or quiz to their course.
    Validates ownership, due date, and required fields.
    Assessment starts as unpublished — admin must publish it.
    """
    course  = get_object_or_404(Course, pk=course_id)
    profile = get_object_or_404(InstructorProfile, user=request.user)

    if course.instructor != profile:
        messages.error(request, 'You do not own this course.')
        return redirect('instructor_dashboard')

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        assess_type = request.POST.get('assess_type', 'assignment')
        mode        = request.POST.get('mode', 'file')
        total_marks = request.POST.get('total_marks', '100').strip()
        due_date    = request.POST.get('due_date', '').strip()
        description = request.POST.get('description', '').strip()
        file        = request.FILES.get('file')

        if not title:
            messages.error(request, 'Assessment title is required.')
            return render(request, 'assessments/create.html', {'course': course})

        try:
            total_marks = int(total_marks)
        except ValueError:
            total_marks = 100

        # Parse due_date
        parsed_due = None
        if due_date:
            try:
                from django.utils.dateparse import parse_datetime
                naive = parse_datetime(due_date)
                if naive:
                    parsed_due = timezone.make_aware(naive)
            except Exception:
                pass

        try:
            assessment = Assessment.objects.create(
                course       = course,
                instructor   = profile,
                title        = title,
                assess_type  = assess_type,
                mode         = mode,
                total_marks  = total_marks,
                description  = description,
                due_date     = parsed_due,
                file         = file,
                is_published = False,  # admin publishes after review
            )
            messages.success(
                request,
                f'Assessment "{title}" created. '
                f'{"Add MCQ questions below." if mode == "mcq" else ""} '
                f'An admin must publish it before students can see it.'
            )
            if mode == 'mcq':
                return redirect('add_questions', assessment_id=assessment.pk)
            return redirect('course_manage', pk=course.pk)

        except DatabaseError as e:
            logger.error(f'Create assessment error: {e}')
            messages.error(request, 'Could not create assessment. Please try again.')

    return render(request, 'assessments/create.html', {'course': course})


# ─────────────────────────────────────────────────────────
#  INSTRUCTOR: Add MCQ Questions
# ─────────────────────────────────────────────────────────
@login_required
def add_questions(request, assessment_id):
    """
    Instructor adds multiple-choice questions to an MCQ assessment.
    Each question has 4 options with one marked correct.
    """
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    profile    = get_object_or_404(InstructorProfile, user=request.user)

    if assessment.course.instructor != profile:
        messages.error(request, 'Access denied.')
        return redirect('instructor_dashboard')

    if request.method == 'POST':
        q_text  = request.POST.get('question_text', '').strip()
        marks   = request.POST.get('marks', '1').strip()
        correct = request.POST.get('correct_option', '').strip()
        opts    = [
            request.POST.get('option_1', '').strip(),
            request.POST.get('option_2', '').strip(),
            request.POST.get('option_3', '').strip(),
            request.POST.get('option_4', '').strip(),
        ]

        if not q_text or not any(opts):
            messages.error(request, 'Question text and at least one option are required.')
        else:
            try:
                q = Question.objects.create(
                    assessment    = assessment,
                    question_text = q_text,
                    marks         = int(marks) if marks.isdigit() else 1,
                    order         = assessment.questions.count() + 1,
                )
                for i, opt_text in enumerate(opts, start=1):
                    if opt_text:
                        Option.objects.create(
                            question    = q,
                            option_text = opt_text,
                            is_correct  = (str(i) == correct),
                        )
                messages.success(request, f'Question {assessment.questions.count()} added.')
            except DatabaseError as e:
                logger.error(f'Add question error: {e}')
                messages.error(request, 'Could not save question.')

    questions = assessment.questions.prefetch_related('options').all()
    return render(request, 'assessments/add_questions.html', {
        'assessment': assessment,
        'questions':  questions,
    })