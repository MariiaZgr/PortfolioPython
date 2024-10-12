FROM python:3.7-slim

# Создать директорию вашего приложения.
RUN mkdir /app

# Сделать директорию /app рабочей директорией.
WORKDIR /app

# Скопировать с локального компьютера файл зависимостей
# в директорию /app.
COPY ./backend/requirements.txt /app
COPY ./data/fixtures.json /app

# Выполнить установку зависимостей внутри контейнера.
RUN pip3 install -r /app/requirements.txt --no-cache-dir

# Скопировать содержимое директории /api_yamdb c локального компьютера
# в директорию /app.
COPY ./backend /app

# Выполнить запуск сервера разработки при старте контейнера.
CMD ["gunicorn", "foodgram_api.wsgi:application", "--bind", "0:8000" ]