from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages


def home(request):
    return render(request, "home.html")


# ВНИМАНИЕ !!!
# Авторизация через LDAP реализована через заглушку.
# Используется псевдо-авторизация через стандартную форму Django.
# Выводимое сообщение об успешной авторизации не имеет смысла.
def ldap_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Вы успешно вошли. Данные синхронизированы с LDAP.")
            return redirect('home')
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    return render(request, "login.html")
