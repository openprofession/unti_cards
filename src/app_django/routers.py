from rest_framework import routers

from red_cards.viewsets import CardViewSet, StatusViewSet

router = routers.DefaultRouter()
router.register(r'cards', CardViewSet)
router.register(r'statuses', StatusViewSet)
