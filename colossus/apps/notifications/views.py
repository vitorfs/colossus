from django.http import JsonResponse


def notifications(request):
    return JsonResponse({'message': 'test'})
