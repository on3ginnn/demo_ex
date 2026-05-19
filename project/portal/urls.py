from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

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

]
