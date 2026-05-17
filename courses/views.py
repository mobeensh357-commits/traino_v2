# courses views — to be implemented
"""
Traino v2 — courses/views.py
Course list, detail, create, enroll, manage sections & materials.
"""
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import DatabaseError, transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.utils import timezone
from assessments.models import Assessment, Submission
from feedback.models import Review   # instead of from .models import Review
from .models import Course, Section, Material, Enrollment, WishList, CATEGORY_CHOICES, LEVEL_CHOICES
from instructor.models import InstructorProfile
from notifications.models import Notification
from django.http import JsonResponse
from .models import StudentMaterialProgress, update_course_progress   # already imported
logger = logging.getLogger(__name__)


def course_list(request):
    """
    Public course catalog with search and filters.
    Supports: keyword search, category filter, level filter, price filter.
    """
    query    = request.GET.get('q', '').strip()
    category = request.GET.get('cat', '').strip()
    level    = request.GET.get('level', '').strip()
    price    = request.GET.get('price', '').strip()

    courses = Course.objects.filter(
        status='approved'
    ).select_related('instructor').order_by('-created_at')

    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(description__icontains=query) |
            Q(instructor__full_name__icontains=query)
        )
    if category:
        courses = courses.filter(category=category)
    if level:
        courses = courses.filter(level=level)
    if price == 'free':
        courses = courses.filter(price=0)
    elif price == 'paid':
        courses = courses.filter(price__gt=0)

    paginator = Paginator(courses, 12)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    return render(request, 'courses/list.html', {
        'page_obj':   page_obj,
        'total':      paginator.count,
        'query':      query,
        'category':   category,
        'level':      level,
        'price':      price,
        'categories': CATEGORY_CHOICES,
        'levels':     LEVEL_CHOICES,
    })


def course_detail(request, pk):
    # Get the course (first check existence, later check permissions)
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        raise Http404("Course does not exist")

    # ---- PREVIEW PERMISSION (instructors/admins can see non-approved courses) ----
    if course.status != 'approved':
        # Only allow instructor who owns the course or a staff/admin
        if request.user.is_authenticated:
            is_owner = request.user.is_teacher and course.instructor.user == request.user
            is_admin = request.user.is_staff
            if not (is_owner or is_admin):
                raise Http404("Course not available")
        else:
            raise Http404("Course not available")

    # Assessments for this course
    assessments = Assessment.objects.filter(course=course).order_by('due_date', '-created_at')


    # Which assessments has the current student already submitted?
    submitted_assessments = []
    my_submissions_data   = []  # full submission data for 3-state button logic
    if request.user.is_authenticated and request.user.is_student:
        submitted_assessments = list(Submission.objects.filter(
            assessment__course=course,
            student=request.user
        ).values_list('assessment_id', flat=True))

        # Full submission data for 3-state button logic (grade, remove)
        my_submissions_data = list(Submission.objects.filter(
            assessment__course=course,
            student=request.user
        ).values('id', 'assessment_id', 'is_graded', 'marks', 'feedback'))


    sections = Section.objects.filter(course=course).prefetch_related('materials')
    reviews = course.reviews.filter(is_visible=True).select_related('student')[:10]

    # Default values
    is_enrolled = False
    is_wishlisted = False
    completed_material_ids = []
    progress_percentage = 0

    if request.user.is_authenticated and request.user.is_student:
        # Check enrollment
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        is_wishlisted = WishList.objects.filter(student=request.user, course=course).exists()

        # Debug prints
        logger.debug(f"User: {request.user.username}, is_student: {request.user.is_student}")

        if is_enrolled:
            # Get IDs of materials already completed
            completed_material_ids = StudentMaterialProgress.objects.filter(
                student=request.user,
                material__section__course=course
            ).values_list('material_id', flat=True)
            # Get progress percentage from enrollment
            enrollment = Enrollment.objects.get(student=request.user, course=course)
            progress_percentage = enrollment.progress
            print(f"Progress: {progress_percentage}%, Completed materials: {list(completed_material_ids)}")
        else:
            print("User is not enrolled in this course.")
    else:
        print("User not authenticated or not a student.")

    # Total materials count
    total_materials = Material.objects.filter(section__course=course).count()

    # Filter assessments: students only see published ones
    if request.user.is_authenticated and request.user.is_student:
        assessments = assessments.filter(is_published=True)

    return render(request, 'courses/detail.html', {
        'course':                 course,
        'sections':               sections,
        'reviews':                reviews,
        'is_enrolled':            is_enrolled,
        'is_wishlisted':          is_wishlisted,
        'total_materials':        total_materials,
        'avg_rating':             course.avg_rating,
        'review_count':           reviews.count(),
        'completed_material_ids': completed_material_ids,
        'progress_percentage':    progress_percentage,
        'assessments':            assessments,
        'submitted_assessments':  submitted_assessments,
        'my_submissions_data':    my_submissions_data,
    })

@login_required
def enroll(request, pk):
    """
    Enroll the current student in a course.
    Free courses enroll directly; paid courses go to shop.
    """
    if not request.user.is_student:
        messages.error(request, 'Only students can enroll in courses.')
        return redirect('course_detail', pk=pk)

    course = get_object_or_404(Course, pk=pk, status='approved')

    # Paid course → go to payment
    if course.price > 0:
        if course.price > 0:
            return redirect('shop:checkout', course_id=pk)

    try:
        with transaction.atomic():
            enrollment, created = Enrollment.objects.get_or_create(
                student=request.user, course=course
            )
            if created:
                Course.objects.filter(pk=pk).update(total_enrolled=course.total_enrolled + 1)
                # Update instructor student count
                InstructorProfile.objects.filter(pk=course.instructor.pk).update(
                    total_students=course.instructor.total_students + 1
                )
                Notification.objects.create(
                    recipient=request.user,
                    title=f'Enrolled: {course.title}',
                    message=f'You have successfully enrolled in "{course.title}". Start learning now!',
                    notif_type='success',
                    link=f'/courses/{pk}/',
                )
                # Notify instructor
                Notification.objects.create(
                    recipient=course.instructor.user,
                    title='New Student Enrolled',
                    message=f'{request.user.username} enrolled in your course "{course.title}".',
                    notif_type='info',
                    link='/instructor/dashboard/',
                )
                messages.success(request, f'Successfully enrolled in "{course.title}"!')
            else:
                messages.info(request, 'You are already enrolled in this course.')
    except DatabaseError as e:
        logger.error(f'Enrollment error for course {pk}: {e}')
        messages.error(request, 'Enrollment failed. Please try again.')

    return redirect('course_detail', pk=pk)


@login_required
def course_create(request):
    """
    Instructor creates a new course.
    Course starts as 'draft' — must be submitted for admin approval.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Only instructors can create courses.')
        return redirect('home')

    try:
        profile = InstructorProfile.objects.get(user=request.user)
    except InstructorProfile.DoesNotExist:
        messages.error(request, 'Please complete your instructor profile first.')
        return redirect('instructor_profile_edit')

    if not profile.is_approved:
        messages.warning(
            request,
            'Your profile is pending admin approval. '
            'You can create draft courses but cannot publish until approved.'
        )

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        category    = request.POST.get('category', '').strip()
        level       = request.POST.get('level', '').strip()
        language    = request.POST.get('language', 'English').strip()
        price       = request.POST.get('price', '0').strip()
        summary     = request.POST.get('summary', '').strip()
        description = request.POST.get('description', '').strip()
        requirements = request.POST.get('requirements', '').strip()
        objectives  = request.POST.get('objectives', '').strip()

        if not title:
            messages.error(request, 'Course title is required.')
            return render(request, 'courses/create.html', {
                'categories': CATEGORY_CHOICES, 'levels': LEVEL_CHOICES,
            })

        try:
            # Generate unique slug
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1

            course = Course.objects.create(
                instructor=profile,
                title=title,
                slug=slug,
                category=category,
                level=level,
                language=language,
                price=float(price) if price else 0,
                summary=summary,
                description=description,
                requirements=requirements,
                objectives=objectives,
                status='draft',
            )

            if 'thumbnail' in request.FILES:
                course.thumbnail = request.FILES['thumbnail']
                course.save(update_fields=['thumbnail'])

            messages.success(request, f'Course "{title}" created as draft. Add sections and materials, then submit for approval.')
            return redirect('course_manage', pk=course.pk)

        except (DatabaseError, ValueError) as e:
            logger.error(f'Course create error: {e}')
            messages.error(request, 'Could not create course. Please try again.')

    return render(request, 'courses/create.html', {
        'categories': CATEGORY_CHOICES,
        'levels':     LEVEL_CHOICES,
    })


@login_required
def course_manage(request, pk):
    """
    Instructor management view for their own course.
    Shows sections, materials, and approval status.
    """
    course = get_object_or_404(Course, pk=pk)

    if not request.user.is_teacher or course.instructor.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('home')

    sections = Section.objects.filter(course=course).prefetch_related('materials')
    enrollments = Enrollment.objects.filter(course=course).count()

    return render(request, 'courses/manage.html', {
        'course':      course,
        'sections':    sections,
        'enrollments': enrollments,
    })


@login_required
def submit_for_approval(request, pk):
    """Instructor submits a draft course for admin approval."""
    course = get_object_or_404(Course, pk=pk)

    if not request.user.is_teacher or course.instructor.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('home')

    if course.status != 'draft':
        messages.warning(request, 'Only draft courses can be submitted for approval.')
        return redirect('course_manage', pk=pk)

    course.status = 'pending'
    course.save(update_fields=['status'])

    # Notify all admins
    from accounts.models import User
    for admin_user in User.objects.filter(is_staff=True):
        Notification.objects.create(
            recipient=admin_user,
            title='Course Awaiting Approval',
            message=f'"{course.title}" by {course.instructor.get_display_name()} has been submitted for review.',
            notif_type='info',
            link=f'/admin/courses/course/{course.pk}/change/',
        )

    messages.success(request, 'Course submitted for admin approval. You will be notified when reviewed.')
    return redirect('course_manage', pk=pk)


@login_required
def add_section(request, course_id):
    """Instructor adds a section (chapter) to their course."""
    course = get_object_or_404(Course, pk=course_id)

    if not request.user.is_teacher or course.instructor.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        order = request.POST.get('order', 0)

        if title:
            try:
                Section.objects.create(course=course, title=title, order=int(order))
                messages.success(request, f'Section "{title}" added.')
            except DatabaseError as e:
                logger.error(f'Add section error: {e}')
                messages.error(request, 'Could not add section.')

    return redirect('course_manage', pk=course_id)


@login_required
def add_material(request, section_id):
    """Instructor uploads a material file to a section."""
    section = get_object_or_404(Section, pk=section_id)
    course  = section.course

    if not request.user.is_teacher or course.instructor.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('home')

    if request.method == 'POST':
        title         = request.POST.get('title', '').strip()
        material_type = request.POST.get('material_type', 'pdf')
        description   = request.POST.get('description', '').strip()
        is_preview    = request.POST.get('is_preview') == 'on'
        file          = request.FILES.get('file')

        if not title or not file:
            messages.error(request, 'Title and file are required.')
        else:
            try:
                Material.objects.create(
                    section=section,
                    title=title,
                    material_type=material_type,
                    description=description,
                    is_preview=is_preview,
                    file=file,
                    is_verified=False,
                )
                messages.success(request, f'Material "{title}" uploaded. Admin will verify it shortly.')
            except DatabaseError as e:
                logger.error(f'Add material error: {e}')
                messages.error(request, 'Could not upload material.')

    return redirect('course_manage', pk=course.pk)


@login_required
def download_material(request, pk):
    """
    Enrolled student downloads a verified material file.
    Also works for preview materials (no enrollment needed).
    """
    material = get_object_or_404(Material, pk=pk)

    # Preview materials are accessible without enrollment
    if not material.is_preview:
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_student:
            enrolled = Enrollment.objects.filter(
                student=request.user, course=material.section.course
            ).exists()
            if not enrolled:
                messages.error(request, 'You must be enrolled to download this material.')
                return redirect('course_detail', pk=material.section.course.pk)
        elif request.user.is_teacher and material.section.course.instructor.user != request.user:
            messages.error(request, 'Access denied.')
            return redirect('home')

    if not material.is_verified and not request.user.is_teacher:
        messages.error(request, 'This material is pending admin verification.')
        return redirect('course_detail', pk=material.section.course.pk)

    try:
        return FileResponse(
            material.file.open('rb'),
            as_attachment=True,
            filename=material.file.name.split('/')[-1]
        )
    except FileNotFoundError:
        raise Http404('File not found.')


@login_required
def submit_review(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    # Only enrolled students can review
    if not request.user.is_student:
        messages.error(request, "Only students can leave reviews.")
        return redirect('course_detail', pk=course.pk)

    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    if not is_enrolled:
        messages.error(request, "You must be enrolled in this course to leave a review.")
        return redirect('course_detail', pk=course.pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()

        if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
            messages.error(request, "Please select a valid rating (1–5 stars).")
        else:
            # Create or update the review using the feedback.Review model
            review, created = Review.objects.update_or_create(
                student=request.user,
                course=course,
                defaults={
                    'rating': int(rating),
                    'title': title,
                    'body': body,
                    'is_visible': True,
                }
            )
            messages.success(request, "Your review has been submitted. Thank you!")

    return redirect('course_detail', pk=course.pk)

from django.http import JsonResponse
from .models import StudentMaterialProgress, update_course_progress

@login_required
def toggle_material_completion(request, material_id):
    """Mark/unmark a material as complete for the logged-in student (AJAX)."""
    material = get_object_or_404(Material, pk=material_id)
    course = material.section.course

    # Security: must be enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return JsonResponse({'error': 'Not enrolled'}, status=403)

    # Toggle completion
    progress_obj, created = StudentMaterialProgress.objects.get_or_create(
        student=request.user, material=material
    )
    if not created:
        progress_obj.delete()
        completed = False
    else:
        completed = True

    # Recalculate course progress
    update_course_progress(request.user, course)

    # Get updated progress
    enrollment = Enrollment.objects.get(student=request.user, course=course)
    return JsonResponse({'completed': completed, 'progress': enrollment.progress})