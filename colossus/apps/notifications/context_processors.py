def notifications(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_seen=False).count()
        return {
            'notifications_count': count
        }
    else:
        return dict()
