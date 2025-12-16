from django.db import migrations


def forwards(apps, schema_editor):
    Category = apps.get_model("events", "Category")
    Department = apps.get_model("users", "Department")
    Event = apps.get_model("events", "Event")

    # --- Категории по ТЗ ---
    categories = {
        "Общеуниверситетские мероприятия": None,
        "Внутри института (колледжа)": None,
        "Участие в других мероприятиях": None,
    }

    for name in categories:
        obj, _ = Category.objects.get_or_create(name=name)
        categories[name] = obj

    default_category = categories["Внутри института (колледжа)"]

    # --- Подразделение-заглушка ---
    department, _ = Department.objects.get_or_create(
        name="Не указано"
    )

    # --- Приведение Event ---
    for event in Event.objects.all():
        changed = False

        if event.category_id is None:
            event.category = default_category
            changed = True

        if event.department_id is None:
            event.department = department
            changed = True

        if event.description is None:
            event.description = ""
            changed = True

        if changed:
            event.save(update_fields=["category", "department", "description"])


def backwards(apps, schema_editor):
    # Обратную миграцию не делаем осознанно
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_department_user_phone_alter_user_department"),
        ("events", "0006_category_location_alter_event_options_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
