def notifications(request):
    if request.user.is_authenticated:
        user_notifications = request.user.notifications \
            .values('text', 'date', 'is_read') \
            .filter(is_read=False) \
            .order_by('-date')
        return {
            'notifications': user_notifications,
            'notifications_count': user_notifications.count()
        }
    else:
        return dict()
