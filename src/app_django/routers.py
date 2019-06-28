from rest_framework import routers

from red_cards.viewsets import CardViewSet

router = routers.DefaultRouter()
router.register(r'cards', CardViewSet)
