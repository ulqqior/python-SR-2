#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль користувацьких виключень для бібліотечної системи.
"""

class LibraryException(Exception):
    """Базове виключення бібліотечної системи."""
    pass


class ValidationError(LibraryException):
    """Помилка валідації вхідних даних."""
    pass


class BookNotFoundError(LibraryException):
    """Книга за вказаним ідентифікатором або назвою не знайдена."""
    pass


class ReaderNotFoundError(LibraryException):
    """Читач з таким ідентифікатором не зареєстрований."""
    pass


class BookAlreadyBorrowedError(LibraryException):
    """Усі примірники зазначеної книги наразі видані читачам."""
    pass


class ReaderLimitExceededError(LibraryException):
    """Перевищено ліміт одночасно позичених книг для читача."""
    pass
