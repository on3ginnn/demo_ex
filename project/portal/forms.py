import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import PHONE_RE, Application, Course, CustomUser, Review


_USERNAME_RE = re.compile(r'^[a-zA-Z0-9]+$')
_FULL_NAME_RE = re.compile(r'^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\s\-\.]{0,198}$')


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ('full_name', 'username', 'email', 'phone', 'password1', 'password2')
        labels = {
            'full_name': 'ФИО',
            'username': 'Логин',
            'email': 'Email',
            'phone': 'Контактный телефон',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            self.fields[name].widget.attrs.setdefault('class', 'form-control')
        self.fields['username'].help_text = 'От 6 символов, только латиница и цифры.'
        self.fields['username'].widget.attrs['minlength'] = 6
        self.fields['username'].widget.attrs['pattern'] = r'[A-Za-z0-9]*'
        self.fields['username'].widget.attrs['title'] = 'От 6 символов, латиница и цифры'
        self.fields['phone'].help_text = 'Формат: 8(XXX)XXX-XX-XX'
        self.fields['phone'].widget.attrs['placeholder'] = '8(900)123-45-67'
        self.fields['phone'].widget.attrs['pattern'] = r'8\(\d{3}\)\d{3}-\d{2}-\d{2}'
        self.fields['phone'].widget.attrs['title'] = 'Пример: 8(900)123-45-67'
        self.fields['phone'].widget.attrs['maxlength'] = 17
        self.fields['password1'].help_text = 'Минимум 8 символов.'
        self.fields['password1'].widget.attrs['minlength'] = 8
        self.fields['password2'].widget.attrs['minlength'] = 8

    def clean_full_name(self):
        full_name = (self.cleaned_data.get('full_name') or '').strip()
        if not full_name:
            raise forms.ValidationError('Обязательное поле.')
        if len(full_name) < 2:
            raise forms.ValidationError('ФИО должно содержать не менее 2 символов.')
        if not _FULL_NAME_RE.match(full_name):
            raise forms.ValidationError('ФИО может содержать только буквы, пробелы и дефис.')
        return full_name

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            raise forms.ValidationError('Обязательное поле.')
        if not PHONE_RE.match(phone):
            raise forms.ValidationError('Укажите телефон в формате 8(XXX)XXX-XX-XX.')
        return phone

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise forms.ValidationError('Обязательное поле.')
        if not _USERNAME_RE.match(username):
            raise forms.ValidationError('Разрешены только латинские буквы и цифры.')
        if len(username) < 6:
            raise forms.ValidationError('Логин не может быть короче 6 символов.')
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1 and len(password1) < 8:
            raise forms.ValidationError('Пароль должен быть не короче 8 символов.')
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают.')
        if password2 and len(password2) < 8:
            raise forms.ValidationError('Пароль должен быть не короче 8 символов.')
        return password2

class PortalAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'
        for name in self.fields:
            self.fields[name].widget.attrs.setdefault('class', 'form-control')
        self.fields['username'].widget.attrs['minlength'] = 6


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('course', 'start_date', 'payment_method')
        labels = {
            'course': 'Курс',
            'start_date': 'Дата старта',
            'payment_method': 'Способ оплаты',
        }
        widgets = {
            'start_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'},
            ),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].empty_label = 'Выберите способ оплаты'
        self.fields['course'].queryset = Course.objects.select_related('category').order_by(
            'category_id', 'title'
        )
        self.fields['course'].label_from_instance = self._label_course

    @staticmethod
    def _label_course(obj: Course) -> str:
        return f'{obj.category.name}: {obj.title}'



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('text', 'rating')
        labels = {'text': 'Текст отзыва', 'rating': 'Оценка (1–5)'}
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

    def __init__(self, *args, application: Application, user: CustomUser, **kwargs):
        self._application = application
        self._user = user
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.setdefault('class', 'form-control')
        self.fields['rating'].widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned = super().clean()
        if self._application.status != Application.Status.COMPLETED:
            raise forms.ValidationError('Отзыв доступен только после статуса «Обучение завершено».')
        if self._application.user_id != self._user.id:
            raise forms.ValidationError('Нельзя оставить отзыв к чужой заявке.')
        if Review.objects.filter(application=self._application).exists():
            raise forms.ValidationError('Отзыв по этой заявке уже отправлен.')
        return cleaned

    def save(self, commit=True):
        self.instance.application = self._application
        self.instance.user = self._user
        return super().save(commit=commit)
