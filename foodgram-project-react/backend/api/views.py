from rest_framework import filters, status, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)

from django.db.models import Sum
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend

from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django.http import HttpResponse
from .filters import RecipeFilter

from recipes.models import (Recipe, Tag, Ingredient, ShoppingCart,
                            Favorite, IngredientInRecipe)
from users.models import Subscription
from .serializers_recipes import (RecipesViewSerializer,
                                  RecipesModifySerializer,
                                  IngredientViewSerializer, TagSerializer)

from .serializers_users import (SubscriptionListSerializer,
                                UserSerializer, SetPasswordSerializer,
                                UserListSerializer,
                                UserRecipesShortViewSerializer,
                                SubscriptionModifySerializer)

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    """Вьюсет для операций с рецептом."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    search_fields = ('name',)
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if self.action in ('list', 'retrieve'):
            return Recipe.objects.prefetch_related(
                'tags', 'author').all()
        return Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipesViewSerializer
        return RecipesModifySerializer

    @action(detail=True, methods=('post', 'delete'))
    def favorite(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        fav_record = Favorite.objects.filter(
            user=user,
            recipe=recipe
        )

        if self.request.method == 'POST':
            if fav_record.exists():
                raise exceptions.ValidationError('Рецепт уже в избранном.')

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = UserRecipesShortViewSerializer(
                recipe,
                context={'request': request}
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            if not fav_record.exists():
                raise exceptions.ValidationError(
                    'Рецепта нет в избранном, либо он уже удален.'
                )

            fav_record.first().delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=('post', 'delete'))
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        cart_item = ShoppingCart.objects.filter(
            user=user,
            recipe=recipe
        )
        if self.request.method == 'POST':
            if cart_item.exists():
                raise exceptions.ValidationError(
                    'Рецепт уже в списке покупок.'
                )

            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = UserRecipesShortViewSerializer(
                recipe,
                context={'request': request}
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            if not cart_item.exists():
                raise exceptions.ValidationError(
                    'Рецепта нет в списке покупок, либо он уже удален.'
                )
            cart_item.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        buy_list = IngredientInRecipe.objects.filter(
            recipe__shopping_card_recipes__user=request.user
        ).values(
            'ingredient'
        ).annotate(
            amount=Sum('amount')
        )

        buy_list_text = 'Список покупок с сайта Foodgram:\n\n'
        for item in buy_list:
            ingredient = Ingredient.objects.get(pk=item['ingredient'])
            amount = item['amount']
            buy_list_text += (
                f'{ingredient.name}, {amount} '
                f'{ingredient.measurement_unit}\n'
            )

        response = HttpResponse(buy_list_text, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=shopping-list.txt'
        )
        return response


class TagViewSet(ModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all().order_by('id')
    filter_backends = (DjangoFilterBackend,)
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientViewSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None
    permission_classes = (IsAuthenticatedOrReadOnly,)


class CustomUserViewSet(UserViewSet):
    """Кастомный вьюсет для пользователей на основе djoser-вьюсета."""

    queryset = User.objects.all()
    lookup_field = 'id'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = UserListSerializer

    @action(
        methods=['get', ],
        detail=False,
        url_path='me', url_name='me',
        permission_classes=(IsAuthenticated,),
        serializer_class=UserSerializer
    )
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(
            request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if request.user.role != 'user':
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post', ],
        permission_classes=(IsAuthenticated,),
        serializer_class=UserSerializer
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        serializer_class=SubscriptionListSerializer,
        permission_classes=(IsAuthenticated, ),
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            author__in=self.request.user.subscriber.all())
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(paginated_queryset, many=True)

        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete',),
        serializer_class=SubscriptionListSerializer
    )
    def subscribe(self, request, id=None):
        user = self.request.user
        author = get_object_or_404(User, pk=id)
        if self.request.method == 'POST':
            validation_serializer = SubscriptionModifySerializer(
                data={'author': author.id, 'user': user.id}
            )
            if validation_serializer.is_valid():
                Subscription.objects.create(user=user, author=author)
                display_serializer = self.get_serializer(author)
                return Response(display_serializer.data,
                                status=status.HTTP_201_CREATED)
            else:
                return Response(
                    validation_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                    )
        if self.request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user,
                author=author
            )
            if subscription.exists():
                subscription.first().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
