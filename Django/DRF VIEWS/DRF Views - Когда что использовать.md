# DRF Views — Когда что использовать

---

## Шаг 1 — Выбери класс

```
Тебе нужен endpoint?
│
├── Данные НЕ из Django-модели (расчёты, внешний API, логин и т.д.)
│   └── → APIView  или  @api_view
│
└── Данные из Django-модели
    │
    ├── Логика нестандартная:
    │   разные queryset для list и detail,
    │   сложные условия, несколько моделей в одном view
    │   └── → APIView
    │
    └── Логика стандартная (CRUD)
        │
        ├── Нужны только 1-2 операции
        │   (например, только список и создание)
        │   └── → Generic View  (ListCreateAPIView и т.д.)
        │
        └── Нужен полный или почти полный CRUD
            + возможно кастомные actions (/publish/, /like/)
            └── → ModelViewSet
```

---

## Шаг 2 — Что обязательно определить в классе

### `@api_view`

```python
@api_view(['GET', 'POST'])          # ← обязательно: список методов
def my_view(request):
    if request.method == 'GET':
        ...
        return Response(data)       # ← обязательно: всегда возвращай Response
    if request.method == 'POST':
        ...
        return Response(data, status=201)
```

**Обязательно:** декоратор с методами, `return Response(...)` в каждой ветке.
**Опционально:** `@permission_classes([...])`, `@authentication_classes([...])`.

---

### `APIView`

```python
class MyView(APIView):
    permission_classes = [IsAuthenticated]   # опционально, но почти всегда нужно

    def get(self, request):                  # ← метод = HTTP-метод (в нижнем регистре)
        ...
        return Response(data)               # ← обязательно

    def post(self, request):
        ...
        return Response(data, status=201)
```

**Обязательно:** методы `get` / `post` / `put` / `patch` / `delete` под каждый нужный HTTP-метод, `return Response(...)`.
**Опционально:** `permission_classes`, `authentication_classes`, `throttle_classes`.

❗ В `APIView` нет `queryset` и `serializer_class` — всё делаешь вручную внутри методов.

---

### Generic Views

```python
class ArticleListCreateView(generics.ListCreateAPIView):
    queryset           = Article.objects.all()    # ← обязательно
    serializer_class   = ArticleSerializer        # ← обязательно
    permission_classes = [IsAuthenticated]        # опционально
```

**Обязательно:** `queryset`, `serializer_class`.
**Не нужно:** писать `get()`, `post()` — они уже реализованы внутри.
**Опционально (переопределяй только если нужно изменить поведение):** см. Шаг 3.

---

### ModelViewSet

```python
class ArticleViewSet(ModelViewSet):
    queryset           = Article.objects.all()    # ← обязательно
    serializer_class   = ArticleSerializer        # ← обязательно
    permission_classes = [IsAuthenticated]        # опционально
```

**Обязательно:** `queryset`, `serializer_class`.
**Не нужно:** писать `list()`, `create()`, `retrieve()` и т.д. — всё уже внутри.
**Не нужно:** писать URL — роутер генерирует их сам.
**Опционально (переопределяй только если нужно):** см. Шаг 3.

---

## Шаг 3 — Какие методы переопределять и когда

### Таблица методов Generic Views и ModelViewSet

| Метод | Когда переопределять | Пример |
|---|---|---|
| `get_queryset()` | Нужна фильтрация: по текущему пользователю, по параметрам URL, по правам | `return qs.filter(author=request.user)` |
| `get_serializer_class()` | Разные сериализаторы для чтения и записи, или для разных actions | `if self.action == 'list': return ...` |
| `perform_create(serializer)` | Нужно добавить данные при создании (автор, дата, tenant и т.д.) | `serializer.save(author=request.user)` |
| `perform_update(serializer)` | Нужно добавить данные при обновлении | `serializer.save(updated_by=request.user)` |
| `perform_destroy(instance)` | Нужна логика перед удалением (soft delete, логирование) | `instance.is_deleted = True; instance.save()` |
| `get_object()` | Искать объект не по `pk`, а по другому полю, или добавить проверку прав | `return get_object_or_404(Article, slug=self.kwargs['slug'])` |
| `get_permissions()` | Разные права для разных actions (ViewSet) | `if self.action == 'destroy': return [IsAdminUser()]` |

---

### Подробно — когда и зачем

#### `get_queryset()` — переопределяй если:

```python
# ✅ Нужна фильтрация по текущему пользователю
def get_queryset(self):
    return Article.objects.filter(author=self.request.user)

# ✅ Нужна фильтрация по параметру из URL (?status=published)
def get_queryset(self):
    qs = Article.objects.all()
    status = self.request.query_params.get('status')
    if status:
        qs = qs.filter(status=status)
    return qs

# ✅ Нужен select_related / prefetch_related для оптимизации
def get_queryset(self):
    return Article.objects.select_related('author').prefetch_related('tags')

# ❌ Не нужно если queryset одинаковый для всех — просто пиши атрибут класса
queryset = Article.objects.all()
```

---

#### `get_serializer_class()` — переопределяй если:

```python
# ✅ Разные сериализаторы для чтения и записи
def get_serializer_class(self):
    if self.request.method in ('POST', 'PUT', 'PATCH'):
        return ArticleWriteSerializer
    return ArticleReadSerializer

# ✅ В ViewSet — разный сериализатор для разных actions
def get_serializer_class(self):
    if self.action == 'list':
        return ArticleListSerializer      # короткий (только title, date)
    if self.action == 'retrieve':
        return ArticleDetailSerializer    # полный
    return ArticleWriteSerializer         # для create/update

# ❌ Не нужно если один сериализатор на всё — просто пиши атрибут
serializer_class = ArticleSerializer
```

---

#### `perform_create()` — переопределяй если:

```python
# ✅ Нужно подставить текущего пользователя как автора
def perform_create(self, serializer):
    serializer.save(author=self.request.user)

# ✅ Нужно подставить объект из URL (например, статья для комментария)
def perform_create(self, serializer):
    article = get_object_or_404(Article, pk=self.kwargs['article_pk'])
    serializer.save(article=article, author=self.request.user)

# ✅ Нужно отправить уведомление после создания
def perform_create(self, serializer):
    instance = serializer.save()
    send_notification.delay(instance.pk)   # celery task

# ❌ Не нужно если дополнительных данных нет — DRF сам вызовет serializer.save()
```

---

#### `perform_destroy()` — переопределяй если:

```python
# ✅ Soft delete (не удалять из БД, а помечать флагом)
def perform_destroy(self, instance):
    instance.is_deleted = True
    instance.deleted_at = timezone.now()
    instance.save()

# ✅ Нужно логировать удаление
def perform_destroy(self, instance):
    logger.info(f"Article {instance.pk} deleted by {self.request.user}")
    instance.delete()

# ❌ Не нужно если просто удаляем — DRF сам вызовет instance.delete()
```

---

## Шаг 4 — URL: роутер или вручную?

```
Используешь ViewSet?
│
├── ДА → используй Router, не пиши URL вручную
│   └── router.register('articles', ArticleViewSet, basename='article')
│
└── НЕТ (APIView / Generic View)
    └── пиши URL вручную через path()
        path('articles/',          ArticleListCreateView.as_view()),
        path('articles/<int:pk>/', ArticleDetailView.as_view()),
```

---

## Шаг 5 — Что возвращать

### Всегда возвращай `Response`, никогда `JsonResponse` или `HttpResponse`

```python
from rest_framework.response import Response
from rest_framework import status

# Список объектов
return Response(serializer.data)                          # 200 OK

# Созданный объект
return Response(serializer.data, status=status.HTTP_201_CREATED)

# Успешное действие без данных (удаление)
return Response(status=status.HTTP_204_NO_CONTENT)

# Кастомный ответ (например, @action)
return Response({'status': 'опубликовано', 'likes': 42})

# Ошибка (обычно DRF сам бросает исключения, но если нужно вручную)
return Response({'detail': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
```

### В Generic Views и ViewSet — не возвращай ничего из perform_*

```python
# ✅ Правильно
def perform_create(self, serializer):
    serializer.save(author=self.request.user)   # нет return

# ❌ Неправильно — perform_create не должен ничего возвращать
def perform_create(self, serializer):
    return serializer.save(author=self.request.user)
```

---

## Итоговая шпаргалка одной таблицей

| Ситуация | Класс | Что определить обязательно | Что переопределять при необходимости |
|---|---|---|---|
| Нет модели / нестандартная логика | `APIView` | методы `get/post/put/delete` | — |
| Простой endpoint, 1-2 строки | `@api_view` | список методов в декораторе | — |
| Список + создание | `ListCreateAPIView` | `queryset`, `serializer_class` | `get_queryset`, `perform_create` |
| Деталь + редактирование + удаление | `RetrieveUpdateDestroyAPIView` | `queryset`, `serializer_class` | `get_queryset`, `perform_update`, `perform_destroy` |
| Полный CRUD | `ModelViewSet` | `queryset`, `serializer_class` | `get_queryset`, `get_serializer_class`, `perform_create`, `get_permissions` |
| Только чтение | `ReadOnlyModelViewSet` | `queryset`, `serializer_class` | `get_queryset` |
| Только список | `ListAPIView` | `queryset`, `serializer_class` | `get_queryset` |
| Только создание | `CreateAPIView` | `queryset`, `serializer_class` | `perform_create` |

---

## Частые ошибки

```python
# ❌ Забыл queryset — Generic/ViewSet не знает, что брать из БД
class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleSerializer
    # нет queryset! → AssertionError

# ❌ Написал get() в ModelViewSet — он там не нужен и не работает
class ArticleViewSet(ModelViewSet):
    def get(self, request):    # ← это не работает в ViewSet
        ...
    # Правильно: def list(self, request) или просто не переопределять

# ❌ Вернул Response из perform_create
def perform_create(self, serializer):
    return serializer.save()   # ← return здесь игнорируется, но сбивает с толку

# ❌ Забыл is_valid() при ручной работе с сериализатором
serializer = ArticleSerializer(data=request.data)
serializer.save()              # ← AttributeError: нужен сначала is_valid()
# Правильно:
serializer.is_valid(raise_exception=True)
serializer.save()
```