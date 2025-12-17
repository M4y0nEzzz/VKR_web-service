from django.db import models


class Location(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Место проведения"
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Адрес"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание"
    )
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Место проведения"
        verbose_name_plural = "Места проведения"