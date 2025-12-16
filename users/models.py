from django.db import models
from departments.models import Department

class User(models.Model):
    name = models.TextField(null=True, blank=True)
    displayname = models.TextField(null=True, blank=True)
    role = models.TextField(null=True, blank=True)
    password = models.TextField()

    department = models.ForeignKey(
        Department,
        models.DO_NOTHING,
        db_column="departament_id",  # как в SQL
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "user"
        managed = False
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.displayname or self.name or f"User #{self.pk}"
