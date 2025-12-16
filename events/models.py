from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


User = settings.AUTH_USER_MODEL


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Категория мероприятия"
        verbose_name_plural = "Категории мероприятий"

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Место проведения"
        verbose_name_plural = "Места проведения"

    def __str__(self):
        return self.name


class Event(models.Model):
    STATUS_CHOICES = (
        ("planned", "Запланировано"),
        ("ongoing", "Проводится"),
        ("completed", "Завершено"),
        ("cancelled", "Отменено"),
    )

    title = models.CharField(
        max_length=500,
        verbose_name="Название мероприятия",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name="Категория",
    )

    department = models.ForeignKey(
        "users.Department",
        on_delete=models.PROTECT,
        verbose_name="Подразделение",
    )

    responsibles = models.ManyToManyField(
        User,
        blank=True,
        related_name="events_responsible_many",
        verbose_name="Ответственные",
    )

    locations = models.ManyToManyField(
        Location,
        blank=True,
        related_name="events",
        verbose_name="Места проведения",
    )

    date_start = models.DateTimeField(
        verbose_name="Дата и время начала",
    )

    date_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата и время окончания",
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="planned",
        verbose_name="Статус",
    )

    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликовано на сайте",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events_created",
        verbose_name="Создатель",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено",
    )

    file = models.FileField(
        upload_to="events/",
        null=True,
        blank=True,
        verbose_name="Файл",
    )

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ("-date_start",)

    def clean(self):
        if self.date_end and self.date_end < self.date_start:
            raise ValidationError("Дата окончания не может быть раньше даты начала")

    def __str__(self):
        return self.title
