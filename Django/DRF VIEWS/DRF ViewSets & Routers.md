# DRF ViewSets & Routers — Шпаргалка

---

## Что такое ViewSet и зачем он нужен?

В предыдущей шпаргалке для полного CRUD нужно было два класса и два URL:

```python
# Два класса...
class ArticleListCreateView(generics.ListCreateAPIView): ...
class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView): ...

# Два URL...
path('articles/',          ArticleListCreateView.as_view()),
path('articles/<int:pk>/', ArticleDetailView.as_view()),
```

ViewSet позволяет свернуть это в один класс, а Router — автоматически
генерирует URL. Писать `path()` вручную почти не нужно.

```python
# Один класс...
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

# Один роутер вместо ручных URL
router.register('articles', ArticleViewSet)
```

---

## Основные типы ViewSet

### 1. `ViewSet` — базовый, полностью ручной

Никакой логики по умолчанию. Только группировка методов под одним классом.

```python
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

class ArticleViewSet(ViewSet):

    def list(self, request):
        # GET /articles/
        qs = Article.objects.all()
        return Response(ArticleSerializer(qs, many=True).data)

    def create(self, request):
        # POST /articles/
        serializer = ArticleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    def retrieve(self, request, pk=None):
        # GET /articles/<pk>/
        article = get_object_or_404(Article, pk=pk)
        return Response(ArticleSerializer(article).data)

    def update(self, request, pk=None):
        # PUT /articles/<pk>/
        ...

    def destroy(self, request, pk=None):
        # DELETE /articles/<pk>/
        ...
```

**Когда использовать:** логика сильно отличается от стандартной,
нет модели Django, нужен полный контроль.

---

### 2. `GenericViewSet` — ViewSet + Generic-возможности

Добавляет `get_queryset()`, `get_serializer_class()`, `get_object()` и т.д.
Сам по себе не делает ничего — нужно добавить Mixins.

```python
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

class ArticleViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    # Нет update и destroy — намеренно!
```

**Когда использовать:** нужен не полный CRUD — например, только чтение + создание.

---

### 3. `ModelViewSet` — полный CRUD из коробки

Содержит все 5 Mixins внутри. Самый популярный вариант.

```python
from rest_framework.viewsets import ModelViewSet

class ArticleViewSet(ModelViewSet):
    queryset           = Article.objects.select_related('author').all()
    serializer_class   = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

Автоматически предоставляет:

| Метод ViewSet | HTTP           | URL                  |
|---------------|----------------|----------------------|
| `list`        | GET            | `/articles/`         |
| `create`      | POST           | `/articles/`         |
| `retrieve`    | GET            | `/articles/<pk>/`    |
| `update`      | PUT            | `/articles/<pk>/`    |
| `partial_update` | PATCH       | `/articles/<pk>/`    |
| `destroy`     | DELETE         | `/articles/<pk>/`    |

---

### 4. `ReadOnlyModelViewSet` — только чтение

Только `list` и `retrieve`. Полезен для публичных справочников.

```python
from rest_framework.viewsets import ReadOnlyModelViewSet

class CategoryViewSet(ReadOnlyModelViewSet):
    queryset         = Category.objects.all()
    serializer_class = CategorySerializer
```

---

## Routers — автоматическая генерация URL

### SimpleRouter vs DefaultRouter

| Возможность                     | `SimpleRouter` | `DefaultRouter`  |
|---------------------------------|:--------------:|:----------------:|
| Стандартные CRUD URL            | ✅             | ✅               |
| Корневой endpoint (`/api/`)     | ❌             | ✅               |
| Trailing slash по умолчанию     | ✅             | ✅               |
| Формат-суффиксы (`.json`)       | ❌             | ✅               |

```python
# urls.py
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, CategoryViewSet

router = DefaultRouter()
router.register('articles',   ArticleViewSet,  basename='article')
router.register('categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

`DefaultRouter` создаёт корневой endpoint `GET /api/` со списком всех маршрутов —
удобно при разработке.

### Что генерирует роутер

После `router.register('articles', ArticleViewSet)`:

```
GET    /api/articles/          → list
POST   /api/articles/          → create
GET    /api/articles/{pk}/     → retrieve
PUT    /api/articles/{pk}/     → update
PATCH  /api/articles/{pk}/     → partial_update
DELETE /api/articles/{pk}/     → destroy
```

### basename — зачем нужен

`basename` используется для именования URL (`article-list`, `article-detail`).
Если queryset задан явно — DRF может вывести basename сам.
Если `get_queryset()` переопределён — basename обязателен.

```python
router.register('articles', ArticleViewSet, basename='article')

# Генерирует имена:
# article-list   → /api/articles/
# article-detail → /api/articles/<pk>/
```

---

## @action — кастомные endpoints

Иногда нужны нестандартные действия, которые не вписываются в CRUD.
Декоратор `@action` добавляет произвольный endpoint к ViewSet.

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class ArticleViewSet(ModelViewSet):
    queryset         = Article.objects.all()
    serializer_class = ArticleSerializer

    # GET /api/articles/published/
    @action(detail=False, methods=['get'])
    def published(self, request):
        qs = self.get_queryset().filter(status='published')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # POST /api/articles/<pk>/publish/
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.status = 'published'
        article.save()
        return Response({'status': 'опубликовано'})

    # GET /api/articles/<pk>/comments/
    # POST /api/articles/<pk>/comments/
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        article = self.get_object()
        if request.method == 'GET':
            comments = article.comments.all()
            return Response(CommentSerializer(comments, many=True).data)
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(article=article, author=request.user)
        return Response(serializer.data, status=201)
```

### Параметры @action

| Параметр           | Описание                                                                |
|--------------------|-------------------------------------------------------------------------|
| `detail`           | `True` → endpoint для одного объекта (`/<pk>/action/`), `False` → для коллекции (`/action/`) |
| `methods`          | Список HTTP-методов: `['get']`, `['post', 'put']`                      |
| `url_path`         | Имя сегмента URL (по умолчанию — имя метода)                            |
| `url_name`         | Имя для `reverse()` (по умолчанию — имя метода с `_` → `-`)            |
| `permission_classes` | Переопределить права только для этого action                          |
| `serializer_class` | Использовать другой сериализатор для этого action                      |

```python
# Переопределить URL и права на конкретный action
@action(
    detail=True,
    methods=['post'],
    url_path='set-password',       # → /api/users/<pk>/set-password/
    url_name='set-password',       # → reverse('user-set-password', args=[pk])
    permission_classes=[IsAdminUser],
)
def set_password(self, request, pk=None):
    ...
```

---

## Кастомизация ViewSet

### Разные сериализаторы для разных действий

```python
class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer      # короткий — только title, date
        if self.action in ('create', 'update', 'partial_update'):
            return ArticleWriteSerializer     # для записи
        return ArticleDetailSerializer        # полный — для retrieve

    # self.action принимает значения:
    # 'list', 'create', 'retrieve', 'update', 'partial_update', 'destroy'
    # + имена кастомных @action методов
```

---

### Разные права для разных действий

```python
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [IsAuthenticated()]
```

---

### Динамический queryset

```python
class ArticleViewSet(ModelViewSet):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        qs = Article.objects.select_related('author').all()

        # Фильтр по параметру URL: /api/articles/?author=5
        author_id = self.request.query_params.get('author')
        if author_id:
            qs = qs.filter(author_id=author_id)

        # Для detail-actions — возвращаем полный queryset
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

---

## Смешивание роутера с ручными URL

Роутер и обычные `path()` можно комбинировать.

```python
# urls.py
router = DefaultRouter()
router.register('articles', ArticleViewSet, basename='article')
router.register('users',    UserViewSet,    basename='user')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/me/',    CurrentUserView.as_view()),   # обычный APIView
    path('api/stats/', StatsView.as_view()),
]
```

---

## Сравнение: Generic Views vs ViewSet

| Критерий                        | Generic Views                    | ViewSet + Router               |
|---------------------------------|----------------------------------|--------------------------------|
| URL                             | Пишешь вручную                   | Генерируются автоматически     |
| Кол-во классов на ресурс        | 2 (list/detail)                  | 1                              |
| Нестандартные endpoints         | Отдельный класс                  | `@action` внутри ViewSet       |
| Разные сериализаторы            | `get_serializer_class()`         | `get_serializer_class()` + `self.action` |
| Гибкость                        | Высокая                          | Высокая                        |
| Читаемость при сложной логике   | Лучше                            | Хуже (всё в одном классе)      |
| Когда выбирать                  | Нестандартная логика, разные права на list и detail | Стандартный CRUD, много ресурсов |

---

## Полный пример — production-ready ViewSet

```python
# views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter

class ArticleViewSet(ModelViewSet):
    """
    Полный CRUD для статей.
    GET    /api/articles/             — список
    POST   /api/articles/             — создать
    GET    /api/articles/<pk>/        — деталь
    PUT    /api/articles/<pk>/        — заменить
    PATCH  /api/articles/<pk>/        — обновить частично
    DELETE /api/articles/<pk>/        — удалить
    GET    /api/articles/my/          — мои статьи
    POST   /api/articles/<pk>/like/   — поставить лайк
    """
    queryset           = Article.objects.select_related('author').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends    = [SearchFilter, OrderingFilter]
    search_fields      = ['title', 'body']
    ordering_fields    = ['created_at', 'title']
    ordering           = ['-created_at']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ArticleWriteSerializer
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleDetailSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # GET /api/articles/my/
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my(self, request):
        qs = self.get_queryset().filter(author=request.user)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # POST /api/articles/<pk>/like/
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        article = self.get_object()
        article.likes.add(request.user)
        return Response({'likes': article.likes.count()})


# urls.py
router = DefaultRouter()
router.register('articles', ArticleViewSet, basename='article')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

---

## Шпаргалка: self.action в ViewSet

```python
self.action == 'list'            # GET /articles/
self.action == 'create'          # POST /articles/
self.action == 'retrieve'        # GET /articles/<pk>/
self.action == 'update'          # PUT /articles/<pk>/
self.action == 'partial_update'  # PATCH /articles/<pk>/
self.action == 'destroy'         # DELETE /articles/<pk>/
self.action == 'my'              # GET /articles/my/  (кастомный @action)
self.action == 'like'            # POST /articles/<pk>/like/
```
