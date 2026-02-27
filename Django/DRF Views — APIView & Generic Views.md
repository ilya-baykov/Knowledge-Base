# DRF Views — APIView & Generic Views

---

## Лестница абстракций DRF

```
@api_view          — функция + декоратор (минимум кода, минимум возможностей)
    ↓
APIView            — класс, полный контроль, всё вручную
    ↓
GenericAPIView     — APIView + queryset + serializer + pagination из коробки
    ↓
Mixins             — готовые list / create / retrieve / update / destroy
    ↓
Generic Views      — GenericAPIView + нужные Mixins уже смешаны
    ↓
ViewSet            — следующая шпаргалка
```

Чем выше — тем больше контроля, но больше кода.
Чем ниже — тем меньше кода, но меньше гибкости.

---

## @api_view — функциональный подход

Самый простой способ написать endpoint. Декоратор оборачивает обычную функцию,
добавляя DRF-функциональность: парсинг, рендеринг, authentication, permissions.

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def articles(request):
    if request.method == 'GET':
        qs = Article.objects.all()
        serializer = ArticleSerializer(qs, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = ArticleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if request.method == 'GET':
        return Response(ArticleSerializer(article).data)

    if request.method == 'PUT':
        serializer = ArticleSerializer(article, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    if request.method == 'DELETE':
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

**Когда использовать:** простые или нестандартные endpoints, утилитарные маршруты
(`/api/ping/`, `/api/me/`, `/api/stats/`), когда класс избыточен.

---

## APIView — классовый подход

Базовый класс. Каждый HTTP-метод — отдельный метод класса.
Полный контроль, никакой магии.

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

class ArticleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        articles = Article.objects.all()
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ArticleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ArticleDetailView(APIView):

    def get_object(self, pk):
        return get_object_or_404(Article, pk=pk)

    def get(self, request, pk):
        article = self.get_object(pk)
        return Response(ArticleSerializer(article).data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ArticleSerializer(article, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        article = self.get_object(pk)
        serializer = ArticleSerializer(article, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

```python
# urls.py
urlpatterns = [
    path('articles/',     ArticleListView.as_view()),
    path('articles/<int:pk>/', ArticleDetailView.as_view()),
]
```

**Когда использовать:** нестандартная логика, несколько сериализаторов в одном view,
сложные условия, когда Generic не справляются.

---

## Атрибуты и методы APIView

### Атрибуты класса

```python
class MyView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]
    throttle_classes       = [UserRateThrottle]
    parser_classes         = [JSONParser, MultiPartParser]
    renderer_classes       = [JSONRenderer, BrowsableAPIRenderer]
    content_negotiation_class = DefaultContentNegotiation
```

### Полезные атрибуты request

```python
request.data          # тело запроса (POST / PUT / PATCH), любой content-type
request.query_params  # GET-параметры (аналог request.GET)
request.user          # аутентифицированный пользователь
request.auth          # токен / credentials
request.method        # 'GET', 'POST' и т.д.
request.content_type  # content-type входящего запроса
```

### Response

```python
from rest_framework.response import Response
from rest_framework import status

Response(data)                                  # 200 OK
Response(data, status=status.HTTP_201_CREATED)  # 201 Created
Response(status=status.HTTP_204_NO_CONTENT)     # 204 No Content
Response({'detail': 'Not found.'}, status=404)  # 404
```

### Часто используемые статусы

```python
status.HTTP_200_OK
status.HTTP_201_CREATED
status.HTTP_204_NO_CONTENT
status.HTTP_400_BAD_REQUEST
status.HTTP_401_UNAUTHORIZED
status.HTTP_403_FORBIDDEN
status.HTTP_404_NOT_FOUND
status.HTTP_405_METHOD_NOT_ALLOWED
```

---

## Mixins — строительные блоки

Живут в `rest_framework.mixins`. Добавляют готовые методы для стандартных действий.
Сами по себе не работают — используются вместе с `GenericAPIView`.

| Mixin                 | Метод           | HTTP     | Описание                  |
|-----------------------|-----------------|----------|---------------------------|
| `ListModelMixin`      | `list()`        | GET      | Список объектов            |
| `CreateModelMixin`    | `create()`      | POST     | Создание объекта           |
| `RetrieveModelMixin`  | `retrieve()`    | GET      | Один объект по pk          |
| `UpdateModelMixin`    | `update()`      | PUT/PATCH| Обновление объекта         |
| `DestroyModelMixin`   | `destroy()`     | DELETE   | Удаление объекта           |

```python
# Собрать view вручную из GenericAPIView + нужных Mixins
from rest_framework import mixins, generics

class ArticleListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
```

На практике Mixins напрямую используют редко —
вместо них берут готовые Generic Views (они уже содержат нужные Mixins внутри).

---

## Generic Views — готовые комбинации

Всё в `rest_framework.generics`. Минимум кода для стандартного CRUD.

### Обзорная таблица

| Класс                           | Методы       | HTTP             | Типичный URL              |
|---------------------------------|--------------|------------------|---------------------------|
| `ListAPIView`                   | `get`        | GET              | `/articles/`              |
| `CreateAPIView`                 | `post`       | POST             | `/articles/`              |
| `RetrieveAPIView`               | `get`        | GET              | `/articles/<pk>/`         |
| `UpdateAPIView`                 | `put, patch` | PUT, PATCH       | `/articles/<pk>/`         |
| `DestroyAPIView`                | `delete`     | DELETE           | `/articles/<pk>/`         |
| `ListCreateAPIView`             | `get, post`  | GET, POST        | `/articles/`              |
| `RetrieveUpdateAPIView`         | `get, put, patch` | GET, PUT, PATCH | `/articles/<pk>/`    |
| `RetrieveDestroyAPIView`        | `get, delete`| GET, DELETE      | `/articles/<pk>/`         |
| `RetrieveUpdateDestroyAPIView`  | все          | GET, PUT, PATCH, DELETE | `/articles/<pk>/`  |

---

### Базовые примеры

```python
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser

# Список + создание
class ArticleListCreateView(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]


# Детальная страница + редактирование + удаление
class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
```

```python
# urls.py
urlpatterns = [
    path('articles/',          ArticleListCreateView.as_view()),
    path('articles/<int:pk>/', ArticleDetailView.as_view()),
]
```

Этих двух классов достаточно для полного CRUD.

---

### Кастомизация Generic Views

#### Разные сериализаторы для чтения и записи

```python
class ArticleListCreateView(generics.ListCreateAPIView):
    queryset = Article.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ArticleWriteSerializer
        return ArticleReadSerializer
```

#### Динамический queryset (фильтрация по текущему пользователю)

```python
class MyArticlesView(generics.ListAPIView):
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user)
```

#### Передача данных в serializer.save()

```python
class ArticleListCreateView(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def perform_create(self, serializer):
        # Автоматически подставляем автора при создании
        serializer.save(author=self.request.user)
```

#### perform_update / perform_destroy

```python
class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        # Можно добавить логику перед удалением
        instance.delete()
```

---

### Ключевые методы GenericAPIView для переопределения

| Метод                       | Зачем переопределять                                        |
|-----------------------------|-------------------------------------------------------------|
| `get_queryset()`            | Динамическая фильтрация, доступ к `request`                 |
| `get_serializer_class()`    | Разные сериализаторы для разных методов                     |
| `get_serializer()`          | Передать дополнительный контекст в сериализатор             |
| `get_object()`              | Кастомная логика получения объекта (не только по pk)        |
| `perform_create(serializer)`| Хук перед сохранением нового объекта                        |
| `perform_update(serializer)`| Хук перед обновлением                                       |
| `perform_destroy(instance)` | Хук перед удалением                                         |

```python
# get_object — например, искать по slug вместо pk
class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = 'slug'    # ← вот так просто, без переопределения get_object

# urls.py
path('articles/<slug:slug>/', ArticleDetailView.as_view())
```

---

### Атрибуты GenericAPIView

```python
class MyView(generics.ListCreateAPIView):
    queryset              = Article.objects.select_related('author').all()
    serializer_class      = ArticleSerializer
    permission_classes    = [IsAuthenticated]
    pagination_class      = PageNumberPagination
    filter_backends       = [SearchFilter, OrderingFilter]
    search_fields         = ['title', 'body']
    ordering_fields       = ['created_at', 'title']
    ordering              = ['-created_at']    # сортировка по умолчанию
    lookup_field          = 'pk'               # поле для get_object (по умолчанию 'pk')
    lookup_url_kwarg      = 'pk'               # имя kwarg в URL
```

---

## Сравнение подходов

| Критерий                    | `@api_view`     | `APIView`       | Generic Views           |
|-----------------------------|-----------------|-----------------|-------------------------|
| Количество кода             | Минимум         | Среднее         | Минимум                 |
| Гибкость                    | Высокая         | Максимальная    | Средняя                 |
| Стандартный CRUD            | Много повторений| Много повторений| Из коробки              |
| Несколько сериализаторов    | Легко           | Легко           | Через `get_serializer_class` |
| Нестандартная логика        | Легко           | Легко           | Хуки или переопределение|
| Читаемость                  | Средняя         | Высокая         | Высокая                 |
| Когда выбирать              | Утилитарные endpoints | Сложная логика | Стандартный CRUD  |

---

## Типичная структура проекта

```python
# views.py
from rest_framework import generics, permissions

class ArticleListCreateView(generics.ListCreateAPIView):
    """GET  /api/articles/       — список статей
       POST /api/articles/       — создать статью"""
    queryset           = Article.objects.select_related('author').all()
    serializer_class   = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/articles/<pk>/ — прочитать
       PUT    /api/articles/<pk>/ — заменить
       PATCH  /api/articles/<pk>/ — обновить частично
       DELETE /api/articles/<pk>/ — удалить"""
    queryset           = Article.objects.all()
    serializer_class   = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
```

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('articles/',          views.ArticleListCreateView.as_view(), name='article-list'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(),     name='article-detail'),
]
```