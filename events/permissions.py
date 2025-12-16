def can_view_event(user, event):
    if user.is_anonymous:
        return False

    if user.is_admin():
        return True

    if user.is_department_head() and event.department_id == user.department_id:
        return True

    return event.created_by_id == user.id


def can_edit_event(user, event):
    return can_view_event(user, event)


def can_delete_event(user, event):
    return can_view_event(user, event)
