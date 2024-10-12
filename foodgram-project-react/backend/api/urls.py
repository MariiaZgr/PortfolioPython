from django.urls import include, path
from rest_framework import routers
from .views import (RecipeViewSet, TagViewSet,
                    IngredientViewSet, CustomUserViewSet)

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename="recipe")
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)

router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
