# MASTER-NOSIROV

Адаптивный интернет-магазин ноутбуков на русском языке. В проекте есть каталог с поиском, фильтрами и сортировкой, карточки товаров, корзина, оформление заказа, REST API на Flask и база MySQL. Сервер сам берёт цены из каталога и рассчитывает итог заказа — присланная браузером цена не используется.

## Запуск на Ubuntu через Docker

Понадобятся Ubuntu 22.04/24.04, Docker Engine и плагин Docker Compose v2. Проверить установку:

```bash
docker --version
docker compose version
```

Если Docker ещё не установлен, в Ubuntu можно установить пакеты из её репозитория:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
```

Если команда `docker` требует прав администратора, добавьте пользователя в группу Docker и войдите в систему заново (либо временно добавляйте `sudo` перед командами Docker):

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

Склонируйте репозиторий и создайте локальный файл настроек:

```bash
git clone https://github.com/menglibaevakram00-bit/online-store.git
cd online-store
cp .env.example .env
```

Откройте `.env` и задайте **два разных длинных случайных пароля** для `MYSQL_PASSWORD` и `MYSQL_ROOT_PASSWORD`. Не публикуйте `.env` и не отправляйте его в Git. Например, можно сгенерировать значения командой:

```bash
openssl rand -hex 24
```

Вставьте первое значение в `MYSQL_PASSWORD`, второе — в `MYSQL_ROOT_PASSWORD`. Затем соберите и запустите все сервисы:

```bash
docker compose up --build -d
docker compose ps
```

При первом запуске MySQL может инициализироваться около минуты. Каталог станет доступен по адресу **http://localhost:8080**. Если порт 8080 уже занят, измените `FRONTEND_PORT` в `.env`, например на `8081`, и откройте `http://localhost:8081`.

## Проверка

Проверить состояние контейнеров и готовность API:

```bash
docker compose ps
curl -fsS http://localhost:8080/api/health
curl -fsS http://localhost:8080/api/products
```

В норме первая команда `curl` вернёт `{"status":"ok"}`; в ответе каталога будут модели и цены. Проверить создание заказа можно так:

```bash
curl -i -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"customer":{"name":"Анна","phone":"+998 90 123 45 67"},"items":[{"product_id":1,"quantity":1}]}'
```

API вернёт созданный заказ и рассчитанную сервером итоговую сумму. В интерфейсе также можно проверить поиск, фильтры, сортировку, добавление/удаление товаров, изменение количества и сообщение об успешном оформлении.

## Локальные тесты API без Docker и MySQL

Тесты используют временную SQLite-базу и не требуют подключения к MySQL. Python 3.10 или новее:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## API

Все маршруты доступны через `/api`:

| Метод и адрес | Назначение |
|---|---|
| `GET /api/health` | Проверка API и соединения с базой |
| `GET /api/categories` | Список категорий каталога |
| `GET /api/products` | Каталог; параметры: `search`, `category`, `min_price`, `max_price`, `sort` |
| `POST /api/orders` | Проверка данных покупателя, серверный расчёт и сохранение заказа |

Допустимая сортировка: `featured`, `price_asc`, `price_desc`, `name_asc`. Заказ принимает JSON с `customer` (`name`, `phone`, необязательный `email`) и массивом `items` (`product_id`, `quantity`). Некорректные данные получают понятный ответ с кодом 400; неизвестный товар — 404.

## Структура проекта

```text
frontend/       Статический интерфейс, корзина, стили и Nginx
backend/app/    Flask API, модели SQLAlchemy и начальные товары
backend/tests/  API-тесты на SQLite
compose.yaml    Nginx + Flask/Gunicorn + MySQL
.env.example   Образец локальных настроек без реальных секретов
```

Корзина хранится в `localStorage` браузера. MySQL сохраняет каталог и заказы в именованном Docker volume `mysql_data`. MySQL доступен только внутри Docker-сети и не публикует порт на компьютер. Для остановки сервисов выполните `docker compose down`; данные при этом сохраняются. Чтобы удалить контейнеры **и все сохранённые данные магазина**, используйте `docker compose down -v`.

## Быстрый локальный запуск без Docker

Для просмотра на компьютере без Docker можно запустить приложение на SQLite. Установите Python и зависимости API:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export DATABASE_URL=sqlite:///local-preview.db
flask --app app init-db
flask --app app run --host 0.0.0.0 --port 8080
```

Откройте **http://localhost:8080**. При первом запуске база и демонстрационный каталог создаются командой `init-db`. Файл SQLite остаётся в `backend/instance/`; этот режим предназначен для локального просмотра, а Docker-развёртывание использует MySQL.

## Изображения

Карточки используют изображения Unsplash по URL. Если такое изображение не загрузится или браузер будет без доступа к сети, интерфейс подставит локальную иллюстрацию `frontend/images/laptop-fallback.svg`.
