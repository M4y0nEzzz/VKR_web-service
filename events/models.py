from datetime import datetime
import json
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

    def get_formatted_dates(self):
        """Возвращает список всех отформатированных дат из EventDate"""
        dates = []
        for ed in self.event_dates.all().order_by('start'):
            if ed.end:
                dates.append(f"{ed.start.strftime('%d.%m.%Y %H:%M')} — {ed.end.strftime('%d.%m.%Y %H:%M')}")
            else:
                dates.append(ed.start.strftime('%d.%m.%Y %H:%M'))

        # Если нет дат в EventDate, пробуем из полей date/end_date
        if not dates and self.date:
            if self.end_date:
                dates.append(f"{self.date.strftime('%d.%m.%Y %H:%M')} — {self.end_date.strftime('%d.%m.%Y %H:%M')}")
            else:
                dates.append(self.date.strftime('%d.%m.%Y %H:%M'))
        return dates

    def get_first_formatted_date(self):
        """Возвращает первую отформатированную дату"""
        first = self.event_dates.order_by('start').first()
        if first:
            if first.end:
                return f"{first.start.strftime('%d.%m.%Y %H:%M')} — {first.end.strftime('%d.%m.%Y %H:%M')}"
            return first.start.strftime('%d.%m.%Y %H:%M')

        # fallback на старые поля date/end_date
        if self.date:
            if self.end_date:
                return f"{self.date.strftime('%d.%m.%Y %H:%M')} — {self.end_date.strftime('%d.%m.%Y %H:%M')}"
            return self.date.strftime('%d.%m.%Y %H:%M')
        return ""

    @property
    def dates_count(self):
        """Возвращает количество дат"""
        count = self.event_dates.count()
        if count == 0 and self.date:
            return 1
        return count


class EventDate(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_dates')
    start = models.DateTimeField(verbose_name='Дата и время начала')
    end = models.DateTimeField(verbose_name='Дата и время окончания', null=True, blank=True)

    class Meta:
        db_table = 'event_date'
        ordering = ['start']
        verbose_name = 'Дата мероприятия'
        verbose_name_plural = 'Даты мероприятий'

    def __str__(self):
        return f"{self.start} - {self.end}" if self.end else str(self.start)