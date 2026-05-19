import hmac

from django import forms
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import FormView, ListView

from .mixins import StaffSessionRequiredMixin
from .models import Application, CourseCategory
from .services import ApplicationLifecycle
from .staff_credentials import STAFF_PASSWORD, STAFF_USERNAME, staff_password_ok



class StaffLoginForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=64)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.setdefault('class', 'form-control')
        self.fields['password'].widget.attrs.setdefault('class', 'form-control')
        if self.is_bound:
            for fname in self.fields:
                if fname in self.errors:
                    w = self.fields[fname].widget
                    c = w.attrs.get('class', '')
                    w.attrs['class'] = f'{c} is-invalid'.strip()

class StaffLoginView(FormView):
    template_name = 'portal/staff_login.html'
    form_class = StaffLoginForm
    success_url = reverse_lazy('portal:staff_dashboard')

    def form_valid(self, form):
        u = form.cleaned_data['username']
        p = form.cleaned_data['password']
        if hmac.compare_digest(u, STAFF_USERNAME) and staff_password_ok(p):
            self.request.session['staff_authenticated'] = True
            messages.success(self.request, 'Добро пожаловать в панель администратора.')
            return super().form_valid(form)
        messages.error(self.request, 'Неверный логин или пароль администратора.')
        return self.form_invalid(form)


class StaffLogoutView(View):
    def get(self, request, *args, **kwargs):
        request.session.pop('staff_authenticated', None)
        messages.info(request, 'Сессия администратора завершена.')
        return redirect('portal:home')


def _filtered_applications_queryset(request):
    qs = Application.objects.select_related('user', 'course', 'course__category').all()
    status_map = dict(Application.Status.choices)
    st = request.GET.get('status')
    if st in status_map:
        qs = qs.filter(status=st)
    category = request.GET.get('category')
    if category:
        qs = qs.filter(course__category_id=category)
    pay_map = dict(Application.PaymentMethod.choices)
    pay = request.GET.get('payment')
    if pay in pay_map:
        qs = qs.filter(payment_method=pay)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(user__email__icontains=q))
    ordering = request.GET.get('ordering', '-created_at')
    allowed = {
        'created_at',
        '-created_at',
        'status',
        '-status',
        'user__username',
        '-user__username',
        'course__title',
        '-course__title',
    }
    return qs.order_by(ordering if ordering in allowed else '-created_at')


class StaffApplicationListView(StaffSessionRequiredMixin, ListView):
    model = Application
    template_name = 'portal/staff_dashboard.html'
    context_object_name = 'applications'
    paginate_by = 15

    def get_queryset(self):
        return _filtered_applications_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = CourseCategory.objects.all()
        ctx['status_choices'] = Application.Status.choices
        ctx['payment_choices'] = Application.PaymentMethod.choices
        q = self.request.GET.copy()
        q.pop('page', None)
        ctx['filter_query'] = q.urlencode()
        ctx['filters'] = {
            'status': self.request.GET.get('status', ''),
            'category': self.request.GET.get('category', ''),
            'payment': self.request.GET.get('payment', ''),
            'q': self.request.GET.get('q', ''),
            'ordering': self.request.GET.get('ordering', '-created_at'),
        }
        return ctx

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string('portal/staff/_results.html', context, request=request)
            return JsonResponse({'ok': True, 'html': html})
        return super().get(request, *args, **kwargs)


def _status_payload(app: Application) -> dict:
    labels = dict(Application.Status.choices)
    return {
        'ok': True,
        'application_id': app.pk,
        'status': app.status,
        'status_label': labels.get(app.status, app.status),
    }


@require_POST
def staff_advance_application(request, pk):
    if not request.session.get('staff_authenticated'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'Требуется вход в панель.'}, status=403)
        messages.warning(request, 'Войдите в панель администратора.')
        return redirect('portal:staff_login')

    app = get_object_or_404(Application.objects.select_related('user', 'course'), pk=pk)
    new_status = request.POST.get('status', '').strip()
    status_map = dict(Application.Status.choices)

    if new_status not in status_map:
        err = 'Укажите корректный статус.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': err}, status=400)
        messages.error(request, err)
        return redirect('portal:staff_dashboard')

    if not ApplicationLifecycle.set_status(app, new_status):
        err = 'Статус не изменён.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': err}, status=400)
        messages.error(request, err)
        return redirect('portal:staff_dashboard')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(_status_payload(app))

    messages.success(request, f'Заявка #{pk}: статус обновлён.')
    nxt = request.POST.get('next')
    if nxt and nxt.startswith('/') and not nxt.startswith('//'):
        return redirect(nxt)
    return redirect('portal:staff_dashboard')
