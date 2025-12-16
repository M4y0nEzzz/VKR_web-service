from django.db import models
from departments.models import Department
from categories.models import Category
from locations.models import Location
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class Event(models.Model):

    STATUS_CHOICES = [
        ("planned", "Запланировано"),
        ("ongoing", "В процессе"),
        ("completed", "Завершено"),
        ("cancelled", "Отменено"),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name='Название мероприятия'
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )

    date_start = models.DateTimeField(
        verbose_name="Дата начала"
    )
    date_end = models.DateTimeField(
        verbose_name="Дата окончания",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planned",
        verbose_name="Статус"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Подразделение'
    )

    responsibles = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="events_responsible_many",
        blank=True,
        verbose_name="Ответственные"
    )

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='events_participants',
        blank=True,
        verbose_name='Участники'
    )

    related_event = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Связанное мероприятие"
    )

    file = models.FileField(
        upload_to="event_files/",
        blank=True,
        null=True,
        verbose_name="Документ/файл"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )

    locations = models.ManyToManyField(
        Location,
        blank=True,
        verbose_name="Места проведения"
    )

    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликовано на сайте"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events_created",
        verbose_name="Создатель записи"
    )

    # Валидация
    def clean(self):
        super().clean()
        if self.date_end and self.date_end < self.date_start:
            raise ValidationError({"date_end": "Дата окончания не может быть раньше даты начала."})

    # Авто-статус
    def _auto_status(self):
        if self.status == "cancelled":
            return "cancelled"
        now = timezone.now()
        if self.date_end and self.date_end < now:
            return "completed"
        if self.date_start <= now <= (self.date_end or now):
            return "ongoing"
        return "planned"

    def save(self, *args, **kwargs):
        new_status = self._auto_status()
        if self.status != "cancelled" and self.status != new_status:
            self.status = new_status
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.date_start})"

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(date_end__gte=models.F("date_start")),
                name="event_end_after_start",
            )
        ]