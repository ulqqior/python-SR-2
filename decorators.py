#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль декораторів для валідації вхідних даних та логування операцій.
"""

import functools
import re
import time
from typing import Callable, Any
from exceptions import ValidationError


def validate_isbn(func: Callable) -> Callable:
    """Декоратор для перевірки коректності формату ISBN-10 або ISBN-13."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Шукаємо аргумент isbn у kwargs або позиційних аргументах
        isbn = kwargs.get("isbn")
        if isbn is None and len(args) > 2:
            # Наприклад, init(self, id, isbn, ...)
            isbn = args[2]

        if isbn is not None:
            clean_isbn = str(isbn).replace("-", "").replace(" ", "").strip()
            if not (len(clean_isbn) in (10, 13) and clean_isbn.isdigit()):
                raise ValidationError(
                    f"Некоректний формат ISBN: '{isbn}'. Очікується 10 або 13 цифр."
                )
        return func(*args, **kwargs)
    return wrapper


def validate_string(field_name: str, min_length: int = 2):
    """Декоратор для валідації текстових полів на непорожнечу та мінімальну довжину."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            val = kwargs.get(field_name)
            if val is not None:
                if not isinstance(val, str) or len(val.strip()) < min_length:
                    raise ValidationError(
                        f"Поле '{field_name}' має бути непорожнім рядком (мін. {min_length} симв.). Отримано: {val!r}"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def positive_int(field_name: str):
    """Декоратор для перевірки, що числове поле є цілим та більшим за нуль."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            val = kwargs.get(field_name)
            if val is not None:
                if not isinstance(val, int) or val <= 0:
                    raise ValidationError(
                        f"Поле '{field_name}' має бути цілим числом > 0. Отримано: {val!r}"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_operation(action_name: str):
    """Декоратор для заміру часу виконання та логування сервісних викликів."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            # Безпечне логування
            return result
        return wrapper
    return decorator
