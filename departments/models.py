from django.db import models

class Department(models.Model):

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название подразделения'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
