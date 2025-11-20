from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages


def home(request):
    return render(request, "home.html")


def ldap_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Введите имя пользователя и пароль.")
            return render(request, "login.html")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(
                request,
                "Вы успешно вошли. Данные синхронизированы с LDAP (заглушка)."
            )
            return redirect("home")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
            return render(request, "login.html")

    return render(request, "login.html")
