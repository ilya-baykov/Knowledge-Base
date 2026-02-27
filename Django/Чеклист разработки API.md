# DRF — Чеклист разработки API

---

## Уровень 1 — Проект (делается один раз)

### 1. Установка

```bash
pip install djangorestframework
pip install djangorestframework-simplejwt   # если нужен JWT
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    'rest_framework',
]
```

---

### 2. Базовые настройки DRF в settings.py

```python
REST_FRAMEWORK = {

    # Кто может обращаться к API по умолчанию
    # Варианты: AllowAny / IsAuthenticated / IsAuthenticatedOrReadOnly
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],

    # Как подтверждается личность пользователя
    # JWT — самый распространённый для современных API
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # для browsable API
    ],

    # Пагинация (если нужна — лучше включить сразу)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Формат ответов по умолчанию
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # убрать в продакшне
    ],
}
```

> 💡 Настройки в `REST_FRAMEWORK` — это глобальные defaults.
> В каждом view их можно переопределить через атрибуты класса.

---

### 3. Подключение URL для аутентификации (если JWT)

```python
# urls.py (корневой)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('api/token/',         TokenObtainPairView.as_view()),   # логин → access + refresh
    path('api/token/refresh/', TokenRefreshView.as_view()),      # обновить access по refresh
    path('api/', include('myapp.urls')),
]
```

---

### 4. Структура файлов приложения

```
myapp/
├── models.py
├── serializers.py      ← создай если нет
├── views.py
├── urls.py             ← создай если нет
├── permissions.py      ← создай если нужны кастомные права
└── filters.py          ← создай если нужна фильтрация
```

---

---

## Уровень 2 — Ресурс (повторяется для каждой сущности)

Допустим, добавляем ресурс `Article`. Идём строго по порядку.

---

### Шаг 1 — Модель (`models.py`)

Ты уже умеешь — это обычный Django.
Убедись что модель есть и миграции применены.

```python
class Article(models.Model):
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
```

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Шаг 2 — Сериализатор (`serializers.py`)

**Вопросы которые нужно решить:**

- Какие поля отдавать клиенту?
- Какие поля принимать от клиента?
- Нужны ли разные сериализаторы для чтения и записи?
- Есть ли вложенные объекты (FK, M2M)?
- Нужна ли кастомная валидация?

```python
from rest_framework import serializers
from .models import Article

# Минимальный вариант — один сериализатор на всё
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Article
        fields = ['id', 'title', 'body', 'author', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']
```

```python
# Продвинутый вариант — разные для чтения и записи
class ArticleReadSerializer(serializers.ModelSerializer):
    author = UserShortSerializer(read_only=True)   # вложенный объект

    class Meta:
        model  = Article
        fields = ['id', 'title', 'body', 'author', 'created_at']


class ArticleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Article
        fields = ['title', 'body']   # author подставим в perform_create
```

**Чеклист сериализатора:**
- [ ] `fields` содержит только нужные поля (не `__all__` в продакшне)
- [ ] Поля только для чтения указаны в `read_only_fields`
- [ ] Поля с паролями / токенами помечены `write_only=True`
- [ ] Если есть FK — решено, как он отображается (ID / вложенный объект / строка)
- [ ] Если нужна валидация — написаны `validate_<field>` или `validate`

---

### Шаг 3 — View (`views.py`)

**Сначала ответь на вопросы:**

```
Нужен ли полный CRUD?
├── ДА → ModelViewSet
└── НЕТ → Generic View нужных операций

Нужна ли фильтрация по текущему пользователю?
└── ДА → переопредели get_queryset()

Нужно ли подставлять данные при создании (автор, tenant)?
└── ДА → переопредели perform_create()

Разные сериализаторы для чтения и записи?
└── ДА → переопредели get_serializer_class()

Разные права для разных действий?
└── ДА → переопредели get_permissions() (только в ViewSet)
```

```python
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Article
from .serializers import ArticleReadSerializer, ArticleWriteSerializer

class ArticleViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Article.objects.select_related('author').filter(is_published=True)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ArticleWriteSerializer
        return ArticleReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

**Чеклист view:**
- [ ] Указан `queryset` или переопределён `get_queryset()`
- [ ] Указан `serializer_class` или переопределён `get_serializer_class()`
- [ ] Указан `permission_classes`
- [ ] Если автор/владелец — переопределён `perform_create()`
- [ ] Если нужна фильтрация — добавлен `filter_backends` и поля

---

### Шаг 4 — URL (`urls.py` приложения)

```python
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register('articles', views.ArticleViewSet, basename='article')

urlpatterns = [
    path('', include(router.urls)),
]
```

Если используешь Generic Views (не ViewSet):

```python
urlpatterns = [
    path('articles/',          views.ArticleListCreateView.as_view(),  name='article-list'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(),      name='article-detail'),
]
```

Подключи в корневом `urls.py`:

```python
# project/urls.py
urlpatterns = [
    path('api/', include('myapp.urls')),
]
```

**Чеклист URL:**
- [ ] ViewSet зарегистрирован через router
- [ ] `basename` указан (обязательно если `get_queryset` переопределён)
- [ ] Роутер подключён в корневой `urls.py`

---

### Шаг 5 — Проверка

Минимальная ручная проверка через browsable API или curl:

```bash
# Получить список
curl http://localhost:8000/api/articles/

# Получить токен
curl -X POST http://localhost:8000/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin"}'

# Создать объект с токеном
curl -X POST http://localhost:8000/api/articles/ \
     -H "Authorization: Bearer <твой_токен>" \
     -H "Content-Type: application/json" \
     -d '{"title": "Тест", "body": "Содержание"}'

# Обновить частично
curl -X PATCH http://localhost:8000/api/articles/1/ \
     -H "Authorization: Bearer <твой_токен>" \
     -H "Content-Type: application/json" \
     -d '{"title": "Новый заголовок"}'

# Удалить
curl -X DELETE http://localhost:8000/api/articles/1/ \
     -H "Authorization: Bearer <твой_токен>"
```

**Чеклист проверки:**
- [ ] `GET /api/articles/` возвращает список (200)
- [ ] `POST /api/articles/` без токена возвращает 401/403
- [ ] `POST /api/articles/` с токеном создаёт объект (201)
- [ ] `PATCH /api/articles/<pk>/` обновляет частично (200)
- [ ] `DELETE /api/articles/<pk>/` удаляет (204)
- [ ] Чужой объект нельзя редактировать (403) — если это нужно по логике

---

---

## Итоговый чеклист одной страницей

### Один раз на проект
- [ ] `rest_framework` добавлен в `INSTALLED_APPS`
- [ ] `REST_FRAMEWORK` настроен в `settings.py` (права, аутентификация, пагинация)
- [ ] URL для токенов подключены
- [ ] Созданы файлы `serializers.py`, `urls.py` в приложении

### На каждый новый ресурс
- [ ] **Модель** — создана, миграции применены
- [ ] **Сериализатор** — поля определены, `read_only` / `write_only` расставлены
- [ ] **View** — выбран класс, `queryset` и `serializer_class` заданы, `perform_create` при необходимости
- [ ] **URL** — ресурс зарегистрирован в роутере или прописан вручную
- [ ] **Проверка** — все 5 HTTP-методов отработали как ожидается

### Перед выпуском в продакшн
- [ ] `BrowsableAPIRenderer` убран из `DEFAULT_RENDERER_CLASSES`
- [ ] `DEBUG = False` и `SECRET_KEY` не в коде
- [ ] Права настроены максимально жёстко (не `AllowAny` там где это не нужно)
- [ ] Пагинация включена (без неё эндпоинт со списком вернёт все записи сразу)

---

## Порядок файлов при разработке — шпаргалка

```
models.py        ← 1. сначала структура данных
    ↓
serializers.py   ← 2. что отдаём / принимаем наружу
    ↓
views.py         ← 3. логика обработки запроса
    ↓
urls.py          ← 4. куда подключить
    ↓
проверка         ← 5. curl / browsable API / тесты
```

Этот порядок важен: каждый следующий файл зависит от предыдущего.
Не пытайся писать view раньше чем готов сериализатор — будет сложнее думать.
```
