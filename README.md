# Foodgram

Фудграм — это сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд. Так же этот список пакупок можно скачать в формате txt.

Сайт доступен по ссылке: **https://hostily4kochergin.ddnsking.com**
Админка
Логин: aa@aa.ru
Пароль: admin

### Установка проекта
<i>Примечание: Все примеры указаны для Linux</i><br>
1. Склонируйте репозиторий на свой компьютер:
    ```
    git clone git@github.com:Ilya1996k/foodgram-project-react.git
    ```
2. Создайте файл `.env` и заполните его своими данными.

3. Пересоберите образ:

    ```
    Запустить из католога infra файл
    docker-compose up --build
    ```

4. Сделайте  миграции:

    ```
    - docker-compose exec backend bash
    - python manage.py makemigrations users
    - python manage.py makemigrations api
    - python manage.py makemigrations recipes
    - python manage.py migrate
    ```

5.  Сделайте миграции  статики
    ```
    docker exec -it foodgram_backend python manage.py loaddata data/dump.json
    ```
### Развертывания проекта на сервере

    ```
    1. Настройте nginx локально и на серврее
    2. Добавьте Secrets* на https://github.com/ в репазитории проекта
    2. Раскомментируйте файл #main.yml 
    3. Выполните команду git add .
    4. git commit -m 'коментарий'
    5. git push 
    ```
### Настройка CI/CD

1. Файл workflow уже написан и находится в директории:

    ```
    foodgram/.github/workflows/main.yml
    ```

2. Для адаптации его к вашему серверу добавьте секреты в GitHub Actions:

    ```
    DOCKER_USERNAME                # имя пользователя в DockerHub
    DOCKER_PASSWORD                # пароль пользователя в DockerHub
    HOST                           # IP-адрес сервера
    USER                           # имя пользователя
    SSH_KEY                        # содержимое приватного SSH-ключа 
    SSH_PASSPHRASE                 # пароль для SSH-ключа

   
    ```