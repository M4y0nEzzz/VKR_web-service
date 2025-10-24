from django.contrib.auth.models import AbstractUser
from django.db import models
from departments.models import Department
from django.contrib.auth.models import Group

class User(AbstractUser):

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Подразделение'
    )

    @property
    def is_admin(self):
        return self.groups.filter(name='admin').exists()

    def __str__(self):
        return f"{self.username} ({self.department})" if self.department else self.username

    # Назначение группы безопасности
    def save(self, *args, **kwargs):
        if not self.pk:
            group, created = Group.objects.get_or_create(name='user')
            self.groups.add(group)
        super().save(*args, **kwargs)
