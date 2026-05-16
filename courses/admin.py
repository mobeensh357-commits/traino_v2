from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import Course, Section, Material, Enrollment, WishList
from notifications.models import Notification  # optional – remove if you don't need notifications


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 0
    fields = ('title', 'material_type', 'is_preview', 'is_verified', 'file')
    readonly_fields = ('is_verified',)


class SectionInline(admin.StackedInline):
    model = Section
    extra = 0
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'instructor_name', 'status_badge',
        'category', 'level', 'price', 'total_enrolled', 'created_at'
    )
    list_filter = ('status', 'category', 'level', 'price')
    search_fields = ('title', 'instructor__full_name', 'summary')
    ordering = ('-created_at',)
    actions = ['approve_courses', 'reject_courses']
    inlines = [SectionInline]

    def instructor_name(self, obj):
        return obj.instructor.get_display_name()
    instructor_name.short_description = 'Instructor'
    instructor_name.admin_order_field = 'instructor__full_name'

    def status_badge(self, obj):
        color = {
            'draft': '#9ca3af',
            'pending': '#F5C518',
            'approved': '#16A34A',
            'rejected': '#DC2626',
        }.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8rem;font-weight:600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    @admin.action(description="Approve selected pending courses")
    def approve_courses(self, request, queryset):
        pending = queryset.filter(status='pending')
        count = pending.count()
        for course in pending:
            course.status = 'approved'
            course.save(update_fields=['status'])
            # Notify instructor
            Notification.objects.create(
                recipient=course.instructor.user,
                title='Course Approved',
                message=f'Your course "{course.title}" has been approved and is now live.',
                notif_type='success',
                link=f'/courses/{course.pk}/',
            )
        # Notify admins? (optional)
        self.message_user(request, f'{count} course(s) approved.')

    @admin.action(description="Reject selected pending courses")
    def reject_courses(self, request, queryset):
        pending = queryset.filter(status='pending')
        count = pending.count()
        for course in pending:
            course.status = 'rejected'
            course.save(update_fields=['status'])
            # Notify instructor
            Notification.objects.create(
                recipient=course.instructor.user,
                title='Course Rejected',
                message=f'Your course "{course.title}" has been rejected. Please review and resubmit.',
                notif_type='error',
                link=f'/courses/{course.pk}/manage/',
            )
        self.message_user(request, f'{count} course(s) rejected.')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    inlines = [MaterialInline]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'material_type', 'is_preview', 'is_verified')
    list_filter = ('material_type', 'is_preview', 'is_verified')
    search_fields = ('title', 'section__title', 'section__course__title')
    actions = ['verify_materials']

    @admin.action(description="Verify selected materials")
    def verify_materials(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} material(s) verified.')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'is_completed')
    list_filter = ('is_completed', 'enrolled_at')
    search_fields = ('student__username', 'course__title')


@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'added_at')
    search_fields = ('student__username', 'course__title')