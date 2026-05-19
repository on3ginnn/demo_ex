import re
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinLengthValidator
from django.db import models

_login_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9]+$',
    message='Разрешены только латинские буквы и цифры.',
)
PHONE_PATTERN = r'^8\(\d{3}\)\d{3}-\d{2}-\d{2}$'
PHONE_RE = re.compile(PHONE_PATTERN)
_phone_validator = RegexValidator(
    regex=PHONE_PATTERN,
    message='Телефон в формате 8(XXX)XXX-XX-XX, например 8(900)123-45-67',
)


class CustomUser(AbstractUser):
    username = models.CharField(
        'Логин',
        unique=True,
        validators=[MinLengthValidator(6), _login_validator],
        help_text='Не менее 6 символов, только латиница и цифры.',
        error_messages={'unique': 'Пользователь с таким логином уже существует.'},
    )
    full_name = models.CharField('ФИО', max_length=100)
    email = models.EmailField('Email', unique=True)
    phone = models.CharField(
        'Телефон',
        max_length=15,
        validators=[_phone_validator],
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class CourseCategory(models.Model):
    code = models.CharField('Код', max_length=32, primary_key=True)
    name = models.CharField('Название', max_length=128)

    class Meta:
        verbose_name = 'Категория курсов'
        verbose_name_plural = 'Категории курсов'
        ordering = ['code']

    def __str__(self) -> str:
        return self.name


class Course(models.Model):
    title = models.CharField('Название курса', max_length=255)
    category = models.ForeignKey(
        CourseCategory,
        verbose_name='Категория',
        on_delete=models.PROTECT,
        related_name='courses',
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['category_id', 'title']

    def __str__(self) -> str:
        return f'{self.title} ({self.category.name})'


class Application(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'Идет обучение'
        COMPLETED = 'completed', 'Обучение завершено'

    class PaymentMethod(models.TextChoices):
        CARD = 'card', 'Оплата картой МИР'
        INVOICE = 'invoice', 'Постоплата в офисе организации'
        SBP = 'sbp', 'Предоплата по QR-коду'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Слушатель',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    course = models.ForeignKey(
        Course,
        verbose_name='Курс',
        on_delete=models.PROTECT,
        related_name='applications',
    )
    start_date = models.DateField('Дата старта')
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=32,
        choices=PaymentMethod.choices,
    )
    status = models.CharField(
        'Статус',
        max_length=32,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Заявка #{self.pk} — {self.user.username}'

    @property
    def next_status_code(self) -> str | None:
        """Следующий статус по цепочке или None, если заявка уже завершена."""
        from .services import ApplicationLifecycle

        return ApplicationLifecycle.next_status(self.status)

    @property
    def next_status_label(self) -> str | None:
        code = self.next_status_code
        if not code:
            return None
        return str(dict(self.Status.choices).get(code, code))


class Review(models.Model):
    application = models.OneToOneField(
        Application,
        verbose_name='Заявка',
        on_delete=models.CASCADE,
        related_name='review',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    text = models.TextField('Текст отзыва')
    rating = models.PositiveSmallIntegerField('Оценка', default=5)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Отзыв к заявке #{self.application_id}'
