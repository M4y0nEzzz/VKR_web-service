from django.db import models

class Category(models.Model):

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название категории'
    )

    color = models.CharField(
        max_length=7,
        default='#000000',
        verbose_name='Цвет метки (HEX)'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
