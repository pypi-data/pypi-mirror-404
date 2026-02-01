# Veloce API - Python Клиент

[![PyPI version](https://img.shields.io/pypi/v/veloce-api.svg)](https://pypi.org/project/veloce-api/)
[![Python versions](https://img.shields.io/pypi/pyversions/veloce-api.svg)](https://pypi.org/project/veloce-api/)
[![License](https://img.shields.io/pypi/l/veloce-api.svg)](https://pypi.org/project/veloce-api/)

**[English](https://github.com/ASAPok/veloce-api/blob/main/README_EN.md)** | **Русский**

Официальная Python библиотека для работы с API [панели управления Veloce VPN](https://github.com/ASAPok/veloce).

## ✨ Возможности

- 🚀 **Полное покрытие API** - Все эндпоинты панели Veloce
- 🔄 **Async/Await** - Полная асинхронная поддержка
- 🛡️ **Типобезопасность** - Pydantic модели и type hints
- 🔁 **Автоповтор** - Экспоненциальная задержка при ошибках
- 🎯 **Простота** - Интуитивный API
- 📦 **Free & Paid тарифы** - Автоматическое управление
- 🔑 **API ключи** - Безопасная аутентификация
- 📊 **Всё включено** - Пользователи, ноды, система, инбаунды

## 📦 Установка

```bash
pip install veloce-api
```

## 🚀 Быстрый Старт

```python
from veloce import VeloceClient

# Инициализация клиента
client = VeloceClient(
    base_url="https://your-panel.com/api",
    api_key="your_api_key"
)

# Создать бесплатного пользователя
url = await client.users.create_free("username123")
print(f"Ссылка подписки: {url}")

# Продлить подписку
await client.users.extend_subscription("username123", days=30)

# Получить данные пользователя
user = await client.users.get("username123")
print(f"Статус: {user['status']}, Истекает: {user['expire']}")
```

## 📚 API Модули

### Пользователи (`client.users`)
Полное управление пользователями с поддержкой free/paid тарифов:
```python
# Создание пользователей
await client.users.create_free("user123")
await client.users.create_paid("user456", days=30)

# Управление подписками
await client.users.extend_subscription("user123", days=30)
await client.users.get_subscription_url("user123")

# Операции с пользователями
await client.users.list(offset=0, limit=10, status="active")
await client.users.ban("user123")
await client.users.reset_traffic("user123")
```

### Система (`client.system`)
Системная статистика и операции:
```python
# Получить статистику
stats = await client.system.get_stats()
print(f"Всего пользователей: {stats['total_user']}")
print(f"Активных: {stats['users_active']}")

# Управление ядром
await client.system.restart_core()
config = await client.system.get_core_config()
```

### Ноды (`client.nodes`)
Управление нодами:
```python
# Список нод
nodes = await client.nodes.list()

# Операции с нодами
await client.nodes.create(node_data)
await client.nodes.update(node_id, node_data)
await client.nodes.reconnect(node_id)
```

### Админы (`client.admin`)
Операции администратора:
```python
# Аутентификация
token = await client.admin.login("username", "password")

# Управление
await client.admin.create("newadmin", "password", is_sudo=True)  # Требует Sudo
await client.admin.delete("oldadmin")  # Требует Sudo
```

### И Больше!
- **Инбаунды** (`client.inbounds`) - Конфигурация инбаундов
- **Core** (`client.core`) - Статистика и управление ядром
- **API Ключи** (`client.api_keys`) - Управление API ключами

## 🔧 Продвинутое Использование

### Обработка Ошибок
```python
from veloce.exceptions import VeloceNotFoundError, VeloceAuthError

try:
    user = await client.users.get("несуществующий")
except VeloceNotFoundError:
    print("Пользователь не найден")
except VeloceAuthError:
    print("Неверный API ключ")
```

### Типобезопасность с Pydantic
```python
from veloce.models import UserResponse

user = await client.users.get("user123")
# user типизирован как Dict, или используй Pydantic модель:
user_model = UserResponse(**user)
print(user_model.username)
```

### Настройка Повторов
```python
from veloce.retry import retry_on_error

@retry_on_error(max_retries=5, base_delay=2.0)
async def надежная_операция():
    return await client.users.get("user123")
```

## 📖 Документация

- [История изменений](CHANGELOG.md)

## 💻 Разработка

```bash
# Клонировать репозиторий
git clone https://github.com/ASAPok/veloce-api.git
cd veloce-api

# Установить в режиме разработки
pip install -e ".[dev]"

# Запустить тесты
pytest

# Проверка типов
mypy veloce

# Форматирование кода
black veloce
```

## 🤝 Участие в Разработке

Мы приветствуем вклад в проект! Пожалуйста, не стесняйтесь отправлять Pull Request.

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Добавить amazing-feature'`)
4. Запушьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Проект распространяется под лицензией MIT - см. файл [LICENSE](LICENSE).

## 🔗 Ссылки

- **PyPI**: https://pypi.org/project/veloce-api/
- **Исходный код**: https://github.com/ASAPok/veloce-api
- **Баг-трекер**: https://github.com/ASAPok/veloce-api/issues
- **Veloce Panel**: https://github.com/ASAPok/veloce

## 🌟 Поддержка

Если проект вам полезен, поставьте ⭐️!

По вопросам и поддержке, пожалуйста, [создайте issue](https://github.com/ASAPok/veloce-api/issues).
