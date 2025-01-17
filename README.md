# Название Проекта: Foodgram

Этот проект позволяет пользователям регистрироваться, делиться рецептами, подписываться друг на друга, добавлять рецепты в избранное или список покупок, а затем скачивать их.
https://richi-host.zapto.org/

## Содержание

- [Описание проекта](#описание-проекта)
- [Инструкция по запуску](#инструкция-по-запуску)
- [Примеры запросов](#примеры-запросов)
- [Использованные технологии](#использованные-технологии)
- [Автор](#автор)

## Описание проекта

Проект Foodgram — это веб-приложение, которое позволяет пользователям управлять рецептами, делиться ими, подписываться на других пользователей и добавлять рецепты в избранное или в список покупок.

## Инструкция по запуску

Для запуска проекта выполните следующие шаги:

1. Перейдите в папку `foodgram`.
2. Запустите контейнеры с помощью команды:

   ```bash
   docker-compose up --build
После выполнения этой команды приложение будет доступно по адресу http://127.0.0.1:8000/ и спецификация API по адресу http://127.0.0.1:8000/api/docs/.

## Примеры запросов

Получить список рецептов
GET /api/recipes/

Создать новый рецепт
POST /api/recipes/
```
Content-Type: application/json
{
  "name": "Нечто съедобное",
  "ingredients": [
    {
      "id": 1,
      "amount": 10
    }
  ],
  "tags": [1, 2],
  "image": "data:image/png;base64,...",
  "text": "Приготовьте как нибудь эти ингредиенты",
  "cooking_time": 5
}
```

Получить информацию о рецепте по ID
GET /api/recipes/{id}/


## Использованные технологии
 - Python
 - Django
 - Django REST Framework
 - Docker
 - PostgreSQL
## Автор
Студент курса Яндекс Практикум: Прыжиков Илья
