from rest_framework.routers import DefaultRouter

from . import views

app_name = 'lists_api'

router = DefaultRouter()
router.register('', views.MailingListViewSet, basename='list')

urlpatterns = router.urls
