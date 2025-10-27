# Pandemic

Веб-версия настольной игры «Пандемия».

Это Flask-приложение для сетевой версии настольной игры «Пандемия». Проект предоставляет REST- и WebSocket-интерфейсы для создания комнат, подключения игроков и обмена игровыми действиями в режиме реального времени.

## Технологии
- Python 3.11+
- Flask + Flask-SocketIO для HTTP- и WebSocket-слоя
- Flask-SQLAlchemy и SQLite (по умолчанию) для хранения сессий и игроков
- Vue 3 и Socket.IO client на фронтенде

## Подготовка окружения
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install flask flask-socketio flask-sqlalchemy eventlet
```

Настройки берутся из `config.Config` и могут переопределяться переменными окружения:
- `SECRET_KEY` — ключ приложения Flask
- `DATABASE_URL` — строка подключения SQLAlchemy

## Запуск разработки
```bash
python app.py
```
Приложение стартует на `http://localhost:5000` и автоматически поднимает Socket.IO-сервер.

## REST API
- `POST /api/host/create` — создает игровую комнату и возвращает код подключения.
- `GET /api/health` — проверка доступности сервера.

## События Socket.IO
- `host_join` — ведущий присоединяется к комнате; сервер отвечает `host_ready`.
- `player_join` — игрок присоединяется, сервер уведомляет комнату событием `player_joined` и фиксирует игрока в БД.
- `start_game` — переводит комнату в активное состояние и рассылает `game_started`.
- `player_action` — отправка произвольного действия с ретрансляцией `action_broadcast` всем участникам.

## Модели данных
- `GameSession`: код комнаты и статус (waiting/active/finished).
- `Player`: имя игрока и код комнаты.
- `MoveLog`: задел под журнал действий (payload — текстовое поле).

## Авторы
- [Денис Свиридов](https://github.com/MrFireDeN)
- [Илья Подмосковнов](https://github.com/rokosvlg)
- [Петр Березовский](https://github.com/8RODOGAST8)
