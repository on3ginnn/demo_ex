"""Публичные страницы и личный кабинет слушателя."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView, TemplateView

from .forms import (
    ApplicationForm,
    CustomUserCreationForm,
    PortalAuthenticationForm,
    ReviewForm,
)
from .models import Application, CourseCategory, CustomUser, Review


class HomeView(TemplateView):
    template_name = 'portal/home.html'


class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'portal/register.html'
    success_url = reverse_lazy('portal:login')

    def form_valid(self, form):
        messages.success(self.request, 'Регистрация успешна. Войдите, используя логин и пароль.')
        return super().form_valid(form)

    def form_invalid(self, form):
        for name in form.errors:
            w = form.fields[name].widget
            css = w.attrs.get('class', 'form-control')
            if 'is-invalid' not in css:
                w.attrs['class'] = f'{css} is-invalid'.strip()
        return super().form_invalid(form)


class PortalLoginView(LoginView):
    template_name = 'portal/login.html'
    authentication_form = PortalAuthenticationForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Не удалось войти. Проверьте логин и пароль.',
        )
        return super().form_invalid(form)


class CabinetView(LoginRequiredMixin, ListView):
    """ЛК: история заявок и возможность оставить отзыв по завершённым без отзыва."""

    model = Application
    template_name = 'portal/cabinet.html'
    context_object_name = 'applications'

    def get_queryset(self):
        return (
            Application.objects.filter(user=self.request.user)
            .select_related('course', 'course__category')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        completed_ids = list(
            Application.objects.filter(
                user=self.request.user,
                status=Application.Status.COMPLETED,
            ).values_list('id', flat=True)
        )
        reviewed_ids = set(
            Review.objects.filter(application_id__in=completed_ids).values_list(
                'application_id', flat=True
            )
        )
        missing = [pk for pk in completed_ids if pk not in reviewed_ids]
        ctx['applications_missing_review'] = list(
            Application.objects.filter(pk__in=missing).select_related('course', 'course__category')
        )
        ctx['reviews'] = (
            Review.objects.filter(user=self.request.user)
            .select_related('application', 'application__course')
            .order_by('-created_at')
        )
        return ctx


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'portal/application_form.html'
    success_url = reverse_lazy('portal:cabinet')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories_qs'] = CourseCategory.objects.prefetch_related('courses').order_by('code')
        return ctx

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = Application.Status.NEW
        messages.success(self.request, 'Заявка отправлена.')
        return super().form_valid(form)


class ReviewCreateView(LoginRequiredMixin, FormView):
    template_name = 'portal/review_form.html'
    form_class = ReviewForm
    success_url = reverse_lazy('portal:cabinet')

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(
            Application.objects.select_related('course', 'course__category'),
            pk=self.kwargs['application_pk'],
            user=request.user,
        )
        if self.application.status != Application.Status.COMPLETED:
            messages.error(request, 'Отзыв можно оставить только для заявки со статусом «Обучение завершено».')
            return redirect('portal:cabinet')
        if Review.objects.filter(application=self.application).exists():
            messages.warning(request, 'Отзыв по этой заявке уже существует.')
            return redirect('portal:cabinet')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['application'] = self.application
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Отзыв сохранён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['application'] = self.application
        return ctx
