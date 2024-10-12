from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from recipes.models import Recipe
from users.models import Subscription
from djoser.serializers import UserCreateSerializer
from django.core import exceptions
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

User = get_user_model()


class UserRecipesShortViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserListSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        return (
            current_user.is_authenticated
            and current_user.subscriber.filter(author=obj).exists()
        )


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'password')


class CustomUserCreateSerializer(UserCreateSerializer):
    def validate(self, obj):
        username_validator = UnicodeUsernameValidator()
        try:
            validate_email(obj['email'])
            username_validator(obj['username'])
        except ValidationError as e:
            raise serializers.ValidationError(
                {'bad email': list(e.messages)}
            )
        return super().validate(obj)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'password')


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150, allow_blank=False)
    confirmation_code = serializers.CharField(allow_blank=False)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class SetPasswordSerializer(serializers.Serializer):

    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неправильный пароль.'}
            )
        if (validated_data['current_password']
           == validated_data['new_password']):
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль должен отличаться от текущего.'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data


class SubscriptionListSerializer(UserListSerializer):

    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count'
    )

    def get_recipes(self, obj):
        author_recipes = Recipe.objects.filter(author=obj)

        if 'recipes_limit' in self.context.get('request').GET:
            recipes_limit = self.context.get('request').GET['recipes_limit']
            author_recipes = author_recipes[:int(recipes_limit)]

        if author_recipes:
            serializer = UserRecipesShortViewSerializer(
                author_recipes,
                context={'request': self.context.get('request')},
                many=True
            )
            return serializer.data

        return []

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'recipes', 'recipes_count')


class SubscriptionModifySerializer(serializers.Serializer):

    author = serializers.IntegerField()
    user = serializers.IntegerField()

    def validate(self, data):
        if data['author'] == data['user']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        sub = Subscription.objects.filter(
            user=data['user'],
            author=data['author']
        )
        if sub.exists():
            raise serializers.ValidationError(
                'Вы уже подписаны.'
            )
        return data
