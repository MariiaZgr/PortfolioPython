import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from reviews.models import Category, Comment, Genre, Review, Title, User

TABLES_NO_FK = {
    User: 'users.csv',
    Category: 'category.csv',
    Genre: 'genre.csv',

}

TABLES_FK = {
    Title: 'titles.csv',
    Review: 'review.csv',
    Comment: 'comments.csv',
}


class Command(BaseCommand):
    help = 'Load csv files to reviews models'

    def handle(self, *args, **kwargs):
        for klass in TABLES_NO_FK.keys():
            klass.objects.all().delete()
        for klass in TABLES_FK.keys():
            klass.objects.all().delete()

        for model, csv_file in TABLES_NO_FK.items():
            with open(
                f"{settings.BASE_DIR}/static/data/{csv_file}",
                'r', encoding='utf-8'
            ) as csv_files:
                reader = csv.DictReader(csv_files)
                model.objects.bulk_create(
                    model(**data) for data in reader)

        with open(
            f"{settings.BASE_DIR}/static/data/titles.csv",
            'r', encoding='utf-8'
        ) as csv_file:
            titles_reader = csv.DictReader(csv_file)
            for title in titles_reader:
                current_category = Category.objects.get(id=title['category'])
                title.pop('category')
                Title.objects.create(**title, category=current_category)

        with open(
            f"{settings.BASE_DIR}/static/data/genre_title.csv",
            'r', encoding='utf-8'
        ) as csv_file:
            genres_titles_reader = csv.DictReader(csv_file)
            for genre_title in genres_titles_reader:
                current_genre = Genre.objects.get(id=genre_title['genre_id'])
                current_title = Title.objects.get(id=genre_title['title_id'])
                current_title.genre.add(current_genre)

        with open(
            f"{settings.BASE_DIR}/static/data/review.csv",
            'r', encoding='utf-8'
        ) as csv_file:
            review_reader = csv.DictReader(csv_file)
            for review in review_reader:

                current_title = Title.objects.get(id=review['title_id'])
                review.pop('title_id')

                current_author = User.objects.get(id=review['author'])
                review.pop('author')

                Review.objects.create(
                    **review,
                    title=current_title,
                    author=current_author)

        with open(
            f"{settings.BASE_DIR}/static/data/comments.csv",
            'r', encoding='utf-8'
        ) as csv_file:
            comment_reader = csv.DictReader(csv_file)
            for comment in comment_reader:
                current_review = Review.objects.get(id=comment['review_id'])
                comment.pop('review_id')

                current_author = User.objects.get(id=comment['author'])
                comment.pop('author')

                Comment.objects.create(
                    **comment,
                    review=current_review,
                    author=current_author)
