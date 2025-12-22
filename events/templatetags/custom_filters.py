from django import template

register = template.Library()


@register.filter
def pluralize_ru(number, forms):
    try:
        number = int(number)
    except (ValueError, TypeError):
        return forms.split(',')[2] if ',' in forms else forms

    forms = forms.split(',')

    if len(forms) != 3:
        return forms[0] if forms else ''

    if number % 10 == 1 and number % 100 != 11:
        return forms[0]
    elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
        return forms[1]
    else:
        return forms[2]