from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title, User

from .filters import TitleFilter
from .mixins import CreateListDestroyViewSet
from .permissions import IsAdmin, IsAdminOrReadOnly, IsModerAdminOrReadOnly
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer, SignupSerializer,
                          TitleSerializer, TokenSerializer, UserSerializer)


class GenreViewSet(CreateListDestroyViewSet):
    queryset = Genre.objects.all().order_by('id')
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly,)


class CategoryViewSet(CreateListDestroyViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly,)


class TitleViewSet(ModelViewSet):
    queryset = (Title.objects.
                select_related('category').
                prefetch_related('genre').
                annotate(rating=Avg('reviews__score')).
                order_by("id")
                )
    serializer_class = TitleSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    permission_classes = (IsAdminOrReadOnly,)


class ReviewViewSet(ModelViewSet):
    """
    Обрабатывает запросы к рейтингам.
    """
    serializer_class = ReviewSerializer
    permission_classes = (IsModerAdminOrReadOnly,)

    def get_queryset(self):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id')
        )
        return title.reviews.select_related('title').all().order_by('id')

    def perform_create(self, serializer):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(ModelViewSet):
    """
    Обрабатывает запросы к комментариям.
    """
    serializer_class = CommentSerializer
    permission_classes = (IsModerAdminOrReadOnly,)

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id')
        )
        return review.comments.select_related('review').all().order_by('id')

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id')
        )
        serializer.save(author=self.request.user, review=review)


class UserViewSet(ModelViewSet):
    """
    Создает пользователя.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me', url_name='me',
        permission_classes=(IsAuthenticated,),
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


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)

    # Провести валидацию полей
    serializer_is_valid = serializer.is_valid()
    validateddata = serializer.validated_data
    email = validateddata.get("email")
    username = validateddata.get("username")

    found_user = None
    # Создать юзера, если валидация прошла успешно
    if serializer_is_valid:
        found_user = User.objects.create(email=email, username=username)
    # Иначе найти юзера по емейл
    elif User.objects.filter(email=email).exists():
        found_user = User.objects.filter(email=email).first()

    # Если юзер найден или создан, то отослать код
    if found_user is not None:
        confirmation_code = default_token_generator.make_token(found_user)
        if not confirmation_code:
            return Response(
                serializer.errors,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        send_mail(
            'Тема письма',
            f'Confirmation code: {confirmation_code}',
            settings.EMAIL_DO_NOT_REPLY,
            [found_user.email],
        )

    # Отослать ответ по результатам валидации,
    # независимо от того, был ли сгенерирован код
    if serializer_is_valid:
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = get_object_or_404(User, username=request.data['username'])
    confirmation_code = request.data['confirmation_code']
    if default_token_generator.check_token(user, confirmation_code):
        token = str(AccessToken.for_user(user))
        response = {'token': token}
        return Response(response, status=status.HTTP_200_OK)
    return Response(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)
