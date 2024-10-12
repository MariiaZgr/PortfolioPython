import datetime

from django.core.exceptions import ValidationError
from rest_framework import serializers
from reviews.models import Category, Comment, Genre, Review, Title, User


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Genre


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Category


class TitleSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(queryset=Genre.objects.all(),
                                         slug_field='slug', many=True)
    category = serializers.SlugRelatedField(queryset=Category.objects.all(),
                                            slug_field='slug')
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = ('id', 'name', 'year', 'rating',
                  'description', 'genre', 'category')
        model = Title

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['genre'] = GenreSerializer(instance.genre, many=True).data
        response['category'] = CategorySerializer(instance.category).data

        return response

    def validate_year(self, value):
        year = datetime.datetime.now().year
        if value > year:
            raise serializers.ValidationError("Некорректный год произведения")
        return value


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150, allow_blank=False)
    confirmation_code = serializers.CharField(allow_blank=False)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254, allow_blank=False)
    username = serializers.CharField(max_length=150, allow_blank=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Этот email уже занят")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists() or value == 'me':
            raise serializers.ValidationError(
                "Это имя уже занято либо недопустимо.")
        return value

    class Meta:
        model = User
        fields = ('email', 'username')


class ReviewSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context.get('view').kwargs.get('title_id')

        if (
            request.method == 'POST'
            and Review.objects.filter(title=title_id, author=author).exists()
        ):
            raise ValidationError('Вы можете оставить только один отзыв!')

        return data

    class Meta:
        model = Review
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    review = serializers.SlugRelatedField(
        slug_field='text',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254, allow_blank=False)
    username = serializers.CharField(max_length=150, allow_blank=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).count() > 0:
            raise serializers.ValidationError("Этот email уже занят")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).count() > 0 or value == 'me':
            raise serializers.ValidationError(
                "Это имя уже занято либо недопустимо.")
        return value

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'username',
            'bio',
            'role'
        )
