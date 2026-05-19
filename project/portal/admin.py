from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Application, Course, CourseCategory, CustomUser, Review



@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'full_name', 'email', 'phone', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'full_name', 'email', 'phone')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Профиль', {'fields': ('full_name',)}),
        ('Контакты', {'fields': ('email', 'phone')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'full_name', 'email', 'phone', 'password1', 'password2'),
            },
        ),
    )

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')
    list_filter = ('category',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'status', 'start_date', 'created_at')
    list_filter = ('status', 'payment_method', 'course__category')



@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'application', 'rating', 'created_at')
