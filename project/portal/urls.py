from django.contrib.auth import views as auth_views
from django.urls import path

from . import views, views_staff

app_name = 'portal'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.PortalLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cabinet/', views.CabinetView.as_view(), name='cabinet'),
    path('cabinet/application/new/', views.ApplicationCreateView.as_view(), name='application_new'),
    path(
        'cabinet/review/<int:application_pk>/',
        views.ReviewCreateView.as_view(),
        name='review_create',
    ),
    path('staff/login/', views_staff.StaffLoginView.as_view(), name='staff_login'),
    path('staff/logout/', views_staff.StaffLogoutView.as_view(), name='staff_logout'),
    path('staff/applications/', views_staff.StaffApplicationListView.as_view(), name='staff_dashboard'),
    path(
        'staff/applications/<int:pk>/advance/',
        views_staff.staff_advance_application,
        name='staff_advance',
    ),
]
