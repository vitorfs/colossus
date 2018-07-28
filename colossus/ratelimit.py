from colossus.utils import get_client_ip


def ip_key(group, request):
    return get_client_ip(request)


def admin_rate(group, request):
    if request.user.is_authenticated and request.user.is_staff:
        return None
    return '10/5m'
