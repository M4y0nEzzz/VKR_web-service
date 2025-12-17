from django.db import models

class Department(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название подразделения'
    )
    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'departament'