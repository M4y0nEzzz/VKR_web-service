
from django.db import models
from categories.models import Category
from departments.models import Department
from users.models import User

class Event(models.Model):
    name = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    place = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, models.DO_NOTHING, db_column='user_id', null=True, blank=True)
    category = models.ForeignKey(Category, models.DO_NOTHING, db_column='category_id', null=True, blank=True)
    department = models.ForeignKey(Department, models.DO_NOTHING, db_column='departament_id', null=True, blank=True)
    responsible = models.CharField(max_length=255, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'event'
        managed = False
