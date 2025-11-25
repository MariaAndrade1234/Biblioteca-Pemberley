from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from django.urls import path
from rest_framework_simplejwt.views import (
	TokenObtainPairView,
	TokenRefreshView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = router.urls + [
	path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
	path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]