from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"

    def __str__(self):
        return self.name


class User(AbstractUser):
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Подразделение",
    )

    phone = models.CharField(
        max_length=32,
        blank=True,
        verbose_name="Телефон",
    )

    # ---- РОЛИ ----
    def is_user(self):
        return self.groups.filter(name="user").exists()

    def is_department_head(self):
        return self.groups.filter(name="department_head").exists()

    def is_admin(self):
        return self.groups.filter(name="admin").exists()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            from django.contrib.auth.models import Group

            group, _ = Group.objects.get_or_create(name="user")
            self.groups.add(group)
