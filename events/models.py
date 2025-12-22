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
        """
        Возвращает список отформатированных дат из комментария.
        Формат: ['22.12.2032 19:32 — 22.12.2032 21:32', ...]
        """
        if not self.comment or "ДАТЫ:" not in self.comment:
            return []

        formatted_dates = []
        lines = self.comment.split('\n')
        in_dates_section = False

        for line in lines:
            line = line.strip()
            if line == "ДАТЫ:":
                in_dates_section = True
                continue

            if in_dates_section and line and ("-" in line and "T" in line):
                # Парсим строку вида "2032-12-22T19:32 - 2032-12-22T21:32"
                parts = line.split(' - ')
                if len(parts) == 2:
                    start_str, end_str = parts

                    try:
                        # Преобразуем в читаемый формат
                        start_dt = datetime.strptime(start_str.strip(), '%Y-%m-%dT%H:%M')
                        end_dt = datetime.strptime(end_str.strip(), '%Y-%m-%dT%H:%M')

                        formatted_start = start_dt.strftime('%d.%m.%Y %H:%M')
                        formatted_end = end_dt.strftime('%d.%m.%Y %H:%M')

                        formatted_dates.append(f"{formatted_start} — {formatted_end}")
                    except ValueError:
                        continue

        return formatted_dates

    def get_first_formatted_date(self):
        """
        Возвращает первую отформатированную дату для отображения в списке.
        """
        dates = self.get_formatted_dates()
        if dates:
            return dates[0]

        # Если нет дат в комментарии, используем основные поля
        if self.date and self.end_date:
            return f"{self.date.strftime('%d.%m.%Y %H:%M')} — {self.end_date.strftime('%d.%m.%Y %H:%M')}"

        return ""

    @property
    def dates_count(self):
        """
        Возвращает количество дат в комментарии.
        """
        if not self.comment or "ДАТЫ:" not in self.comment:
            return 1  # Основная дата

        count = 0
        lines = self.comment.split('\n')
        in_dates_section = False

        for line in lines:
            line = line.strip()
            if line == "ДАТЫ:":
                in_dates_section = True
                continue

            if in_dates_section and line and ("-" in line and "T" in line):
                count += 1

        return max(count, 1)  # Минимум 1 дата