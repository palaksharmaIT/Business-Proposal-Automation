# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required


# @login_required(login_url='login')
# def dashboard_home(request):
#     return render(request, 'dashboard/index.html')


# def login_view(request):
#     if request.user.is_authenticated:
#         return redirect('dashboard-home')

#     error = None
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect('dashboard-home')
#         else:
#             error = "Invalid username or password."

#     return render(request, 'dashboard/login.html', {'error': error})


# def logout_view(request):
#     logout(request)
#     return redirect('login')


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings


@login_required(login_url='login')
def dashboard_home(request):
    return render(request, 'dashboard/index.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard-home')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print("=" * 50)
        print("DATABASE:", settings.DATABASES["default"]["NAME"])
        print("USERNAME:", username)
        print("PASSWORD:", password)

        user = authenticate(
            request,
            username=username,
            password=password
        )

        print("AUTHENTICATE RESULT:", user)

        if user is not None:
            print("LOGIN SUCCESS")
            login(request, user)
            return redirect('dashboard-home')
        else:
            print("LOGIN FAILED")
            error = "Invalid username or password."

    return render(request, 'dashboard/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')