# Краткое описание проекта

Серверная часть платформы YaMDb позволяет администраторам сайта загружать новые произведения, назначать для них нужные жанры и категорию. Пользователи сервиса могут оставлять отзывы на произведения, ставить им оценки, а также комментировать отзывы других пользователей.

# Шаблон наполнения env-файла

Создайте файл `/infra_sp2/infra/.env`.

Контент файла может быть следующим: 

```
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД 
```

# Описание команд для запуска приложения в контейнерах

Для запуска проекта, находясь в корневой директории данного проекта, выполните эту команду:

```
docker compose -f ./infra/docker-compose.yaml up -d
```

При первом запуске свежей композиции (контейнеры только создались) --  выполните следующие команды, как только композиция поднимется:
```
docker compose -f ./infra/docker-compose.yaml exec web python manage.py migrate
docker compose -f ./infra/docker-compose.yaml exec web python manage.py createsuperuser
docker compose -f ./infra/docker-compose.yaml exec web python manage.py collectstatic --no-input 
```

# Описание команды для заполнения базы данными.

Для снятия слепка базы данных выполните эту команду:
```
docker compose -f ./infra/docker-compose.yaml exec web python manage.py dumpdata > fixtures.json 
```
Для заполнения базы данных из слепка выполните эту команду:

```
docker compose -f ./infra/docker-compose.yaml exec web python manage.py loaddata fixtures.json
```
