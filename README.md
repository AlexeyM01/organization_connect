# Organization connect

## Назначение проекта

Этот проект представляет собой API для управления организациями и связанными с ними активностями в базе данных. Он позволяет пользователям выполнять такие действия, как поиск организаций по адресу здания, имени активности, создание новых организаций и зданий, а также добавление активностей.

## Системные требования

- **Язык программирования**: Python 3.9 или выше
- **База данных**: PostgreSQL 13 или выше
- **Docker**: версия 20.10.0 или выше (для контейнеризации приложения)
- **Docker Compose**: версия 1.27.0 или выше

### Системные зависимости

- **Python библиотеки**:
  - fastapi
  - uvicorn
  - sqlalchemy
  - asyncpg
  - pydantic
  - python-dotenv
  - alembic

## Шаги по установке, сборке и запуску

### 1. Клонирование репозитория

Клонируйте репозиторий на свою локальную машину:

```bash
git clone https://github.com/AlexeyM01/organization_connect
cd organization_connect
```

### 2. Установка Docker и Docker Compose
Убедитесь, что Docker и Docker Compose установлены на вашем компьютере. Инструкции по установке [Docker](https://docs.docker.com/get-started/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/).
Убедитесь, что Docker и Docker Compose установлены на вашем компьютере. Инструкции по установке [Docker](https://docs.docker.com/get-started/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/).

### 3. Настройка переменных окружения
Создайте файл .env в корневой директории проекта и добавьте необходимые переменные окружения:

```text
DB_HOST=db
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASS=your_password

```

### 4. Сборка и запуск контейнеров
Запустите следующую команду для сборки и запуска контейнеров:

```bash
docker-compose up --build
```

### 5. Заполните базу данных
Можете взять прилагаемые данные в виде запроса в файле query.txt, скопировать их в СУБД и наполнить таблицы.

### 6. Проверка работы приложения
После успешного запуска контейнеров, перейдите по адресу ```http://localhost:8000``` в вашем веб-браузере

##Примеры использования
###Пример GET запроса, чтобы получить организации по адресу здания:

```http
GET /organizations/by_building_address/?address=123%20Main%20St
```

##Пример POST запроса, чтобы создать новую организацию:

```http
POST /create_organization/
Content-Type: application/json

{
  "name": "Авто запчасти",
  "address": "Улица Глухарёва, 4",
  "phone_numbers": ["+79123456789"],
  "activities": ["Автомобили", "Запчасти"]
}
```

