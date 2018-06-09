from django.shortcuts import render


def dashboard(request):
    return render(request, 'core/dashboard.html', {'menu': 'dashboard'})
