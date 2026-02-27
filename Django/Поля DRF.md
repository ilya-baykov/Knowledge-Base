# DRF Fields — Шпаргалка

---

## Универсальные параметры (работают на любом поле)

| Параметр        | Тип       | По умолчанию | Что делает                                                    |
|-----------------|-----------|--------------|---------------------------------------------------------------|
| `required`      | `bool`    | `True`       | Поле обязательно при записи                                   |
| `read_only`     | `bool`    | `False`      | Только в ответе, игнорируется при записи                      |
| `write_only`    | `bool`    | `False`      | Только при записи, не попадает в ответ (пароли, токены)       |
| `default`       | any       | —            | Значение если поле не передано (снимает `required`)           |
| `allow_null`    | `bool`    | `False`      | Разрешает `null` / `None`                                     |
| `allow_blank`   | `bool`    | `False`      | Разрешает пустую строку `""` (только текстовые поля)          |
| `source`        | `str`     | имя поля     | Откуда брать значение: атрибут, путь `author.email`, `*`      |
| `label`         | `str`     | —            | Человекочитаемое имя (для документации / browsable API)       |
| `help_text`     | `str`     | —            | Описание поля (для документации)                              |
| `validators`    | `list`    | `[]`         | Список дополнительных функций-валидаторов                     |
| `error_messages`| `dict`    | —            | Переопределение текстов ошибок: `{'required': 'Обязательно'}` |
| `style`         | `dict`    | —            | Подсказки для browsable API: `{'input_type': 'password'}`     |

---

## Поля — от популярных к редким

---

### 🔤 Текстовые

#### `CharField`
Самое частое поле. Строка произвольной длины.

```python
title = serializers.CharField(
    max_length=200,
    min_length=3,
    trim_whitespace=True,   # обрезает пробелы по краям (по умолчанию True)
    allow_blank=False,
)
```

| Параметр          | Описание                              |
|-------------------|---------------------------------------|
| `max_length`      | Максимальная длина строки             |
| `min_length`      | Минимальная длина строки              |
| `trim_whitespace` | Обрезать пробелы (по умолч. `True`)   |
| `allow_blank`     | Разрешить пустую строку               |

---

#### `EmailField`
`CharField` с валидацией формата email.

```python
email = serializers.EmailField(max_length=254)
```

---

#### `URLField`
`CharField` с валидацией формата URL.

```python
website = serializers.URLField()
```

---

#### `SlugField`
Только символы `[a-zA-Z0-9_-]`.

```python
slug = serializers.SlugField(max_length=50)
```

---

#### `UUIDField`
UUID в любом формате, приводится к стандартному.

```python
uid = serializers.UUIDField(format='hex_verbose')  # 'hex_verbose' | 'hex' | 'int' | 'urn'
```

---

#### `RegexField`
Строка, совпадающая с регулярным выражением.

```python
phone = serializers.RegexField(r'^\+?1?\d{9,15}$')
```

---

#### `IPAddressField`
Валидация IPv4 или IPv6.

```python
ip = serializers.IPAddressField(protocol='both')  # 'IPv4' | 'IPv6' | 'both'
```

---

### 🔢 Числовые

#### `IntegerField`

```python
age = serializers.IntegerField(min_value=0, max_value=150)
```

| Параметр    | Описание              |
|-------------|-----------------------|
| `max_value` | Максимальное значение |
| `min_value` | Минимальное значение  |

---

#### `FloatField`
Число с плавающей точкой. Те же параметры `min_value` / `max_value`.

```python
rating = serializers.FloatField(min_value=0.0, max_value=5.0)
```

---

#### `DecimalField`
Для денег и точных вычислений. Не страдает от погрешностей float.

```python
price = serializers.DecimalField(
    max_digits=10,       # всего цифр
    decimal_places=2,    # цифр после запятой
    coerce_to_string=False,  # True → вернёт строку "9.99" вместо Decimal
    rounding=None,       # ROUND_UP, ROUND_DOWN и т.д. из модуля decimal
)
```

| Параметр          | Описание                                     |
|-------------------|----------------------------------------------|
| `max_digits`      | Обязательный. Максимум цифр всего            |
| `decimal_places`  | Обязательный. Цифр после запятой             |
| `coerce_to_string`| Вернуть строку вместо `Decimal`              |
| `rounding`        | Режим округления                             |

---

### ✅ Булевы

#### `BooleanField`

```python
is_active = serializers.BooleanField(default=True)
```

Принимает: `true`, `false`, `1`, `0`, `"yes"`, `"no"`, `"True"`, `"False"` и т.д.

---

#### `NullBooleanField`
То же самое, но допускает `null`. Аналог `BooleanField(allow_null=True)`.

```python
agreed = serializers.NullBooleanField()
```

---

### 📅 Дата и время

#### `DateTimeField`

```python
created_at = serializers.DateTimeField(
    format='%Y-%m-%d %H:%M:%S',   # None → объект datetime, 'iso-8601' → ISO строка
    input_formats=['%Y-%m-%dT%H:%M:%S', 'iso-8601'],
    default_timezone=None,
)
```

| Параметр         | Описание                                         |
|------------------|--------------------------------------------------|
| `format`         | Формат вывода (строка или `None` для объекта)    |
| `input_formats`  | Список принимаемых форматов ввода                |

---

#### `DateField`
Только дата, без времени.

```python
birthday = serializers.DateField(format='%d.%m.%Y')
```

---

#### `TimeField`
Только время.

```python
start_time = serializers.TimeField()
```

---

#### `DurationField`
Временной интервал (Python `timedelta`).

```python
duration = serializers.DurationField()
# принимает: "1 day, 0:00:00" или ISO 8601 "P1DT0H0M0S"
```

---

### 🔗 Связи (Relations)

Используются в `ModelSerializer` автоматически для FK / M2M.
Можно переопределять вручную.

#### `PrimaryKeyRelatedField`
Самый частый. Работает с ID.

```python
# Чтение и запись через ID
author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

# Только чтение (в ответе просто ID)
author = serializers.PrimaryKeyRelatedField(read_only=True)

# M2M — список ID
tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
```

---

#### `StringRelatedField`
Только чтение. Вызывает `__str__()` на объекте.

```python
author = serializers.StringRelatedField()
# → "Ivan Ivanov" (что бы ни возвращал __str__)
```

---

#### `SlugRelatedField`
Связь через произвольное поле модели (не ID).

```python
# Запись через username, не через id
author = serializers.SlugRelatedField(
    slug_field='username',
    queryset=User.objects.all()
)
```

---

#### `HyperlinkedRelatedField`
Связь через URL.

```python
author = serializers.HyperlinkedRelatedField(
    view_name='user-detail',
    read_only=True
)
```

---

### 📁 Файлы

#### `FileField`
Загрузка файла. Данные идут через `multipart/form-data`.

```python
document = serializers.FileField(
    max_length=None,
    allow_empty_file=False,
    use_url=True,    # True → в ответе URL, False → путь к файлу
)
```

---

#### `ImageField`
`FileField` с дополнительной проверкой, что файл является изображением.
Требует установленного `Pillow`.

```python
avatar = serializers.ImageField()
```

---

### 📦 Составные / специальные

#### `ListField`
Список однотипных значений.

```python
tags = serializers.ListField(
    child=serializers.CharField(max_length=50),
    min_length=0,
    max_length=20,
    allow_empty=True,
)
```

---

#### `DictField`
Словарь с произвольными ключами.

```python
metadata = serializers.DictField(
    child=serializers.CharField()
)
# принимает: {"color": "red", "size": "XL"}
```

---

#### `JSONField`
Произвольный JSON — объект, массив, число, строка.

```python
settings = serializers.JSONField(binary=False)
# binary=True → хранит как bytes, а не как строку
```

---

#### `SerializerMethodField`
Вычисляемое поле только для чтения.
Метод называется `get_<имя_поля>`.

```python
full_name    = serializers.SerializerMethodField()
is_following = serializers.SerializerMethodField()

def get_full_name(self, obj):
    return f"{obj.first_name} {obj.last_name}"

def get_is_following(self, obj):
    request = self.context.get('request')
    if request and request.user.is_authenticated:
        return obj.followers.filter(pk=request.user.pk).exists()
    return False
```

> 💡 Доступ к `request` и другим данным — через `self.context`.
> View передаёт контекст автоматически; при ручном создании сериализатора — передавай сам:
> ```python
> serializer = ArticleSerializer(article, context={'request': request})
> ```

---

#### `HiddenField`
Поле не принимается от клиента и не отдаётся в ответе.
Используется для автоматической подстановки значений.

```python
from rest_framework.fields import CurrentUserDefault

# Автоматически подставить текущего пользователя
owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

# Автоматически подставить текущее время
created_at = serializers.HiddenField(default=serializers.CreateOnlyDefault(timezone.now))
```

---

#### `ReadOnlyField`
Просто читает атрибут объекта как есть, без приведения типов.
Удобен для вычисляемых `@property` на модели.

```python
# На модели есть @property full_name
full_name = serializers.ReadOnlyField()

# Эквивалентно:
full_name = serializers.CharField(read_only=True)
```

---

## Быстрая шпаргалка — какое поле выбрать

| Задача                                     | Поле                                      |
|--------------------------------------------|-------------------------------------------|
| Строка, текст                              | `CharField`                               |
| Email                                      | `EmailField`                              |
| URL                                        | `URLField`                                |
| Slug                                       | `SlugField`                               |
| Целое число                                | `IntegerField`                            |
| Деньги, точные числа                       | `DecimalField`                            |
| Дата + время                               | `DateTimeField`                           |
| Только дата                                | `DateField`                               |
| Флаг да/нет                                | `BooleanField`                            |
| FK → по ID                                 | `PrimaryKeyRelatedField`                  |
| FK → по `__str__`                          | `StringRelatedField`                      |
| FK → по произвольному полю                 | `SlugRelatedField`                        |
| Вложенный объект                           | Вложенный сериализатор                    |
| Вычисляемое поле                           | `SerializerMethodField`                   |
| `@property` на модели                      | `ReadOnlyField`                           |
| Список строк / чисел                       | `ListField(child=...)`                    |
| Произвольный JSON                          | `JSONField`                               |
| Загрузка файла                             | `FileField`                               |
| Загрузка картинки                          | `ImageField`                              |
| Автоподстановка (текущий юзер и т.п.)      | `HiddenField`                             |
| UUID                                       | `UUIDField`                               |
| Телефон / паттерн                          | `RegexField`                              |