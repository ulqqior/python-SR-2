#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль реалізації патернів проектування:
1. Singleton (Потокобезпечний Одинак для бази даних бібліотеки).
2. Factory Method (Фабрика сутностей для стандартизованого створення).
3. Observer (Спостерігач для нотифікації читачів про надходження книг).
"""

import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from models import Author, Book, Reader


# ==============================================================================
# 1. ПАТЕРН SINGLETON (ПОТОКОБЕЗПЕЧНИЙ МЕТАКЛАС)
# ==============================================================================

class ThreadSafeSingletonMeta(type):
    """
    Метаклас для створення потокобезпечного Singleton (Double-Checked Locking).
    Гарантує існування єдиного екземпляру класу в усьому процесі.
    """
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


# ==============================================================================
# 2. ПАТЕРН FACTORY METHOD
# ==============================================================================

class EntityFactory:
    """
    Фабрика для створення моделей системи з попередньою уніфікацією параметрів.
    """

    _author_id_seq = 0
    _book_id_seq = 0
    _reader_id_seq = 0
    _seq_lock = threading.Lock()

    @classmethod
    def create_author(cls, name: str, country: str = "Україна") -> Author:
        with cls._seq_lock:
            cls._author_id_seq += 1
            author_id = cls._author_id_seq
        return Author(author_id=author_id, name=name, country=country)

    @classmethod
    def create_book(cls, isbn: str, title: str, author: Author,
                    year: int, total_copies: int = 1) -> Book:
        with cls._seq_lock:
            cls._book_id_seq += 1
            book_id = cls._book_id_seq
        return Book(book_id=book_id, isbn=isbn, title=title,
                    author=author, year=year, total_copies=total_copies)

    @classmethod
    def create_reader(cls, name: str, email: str, max_loans: int = 3) -> Reader:
        with cls._seq_lock:
            cls._reader_id_seq += 1
            reader_id = cls._reader_id_seq
        return Reader(reader_id=reader_id, name=name, email=email, max_loans=max_loans)


# ==============================================================================
# 3. ПАТЕРН OBSERVER (СПОСТЕРІГАЧ)
# ==============================================================================

class Observer(ABC):
    """Інтерфейс спостерігача для отримання сповіщень."""

    @abstractmethod
    def update(self, message: str, book: Book):
        pass


class ReaderNotificationObserver(Observer):
    """Конкретний спостерігач — читач, який очікує на повернення потрібної книги."""

    def __init__(self, reader: Reader):
        self.reader = reader
        self.notifications: List[str] = []

    def update(self, message: str, book: Book):
        note = f"[СПОСТЕРІГАЧ -> {self.reader.name}]: {message} (Книга: '{book.title}', доступно: {book.available_copies})"
        self.notifications.append(note)
        print(note)


class BookSubject:
    """Суб'єкт спостереження, що керує підписками читачів на оновлення статусу книг."""

    def __init__(self):
        self._observers: Dict[int, List[Observer]] = {}  # book_id -> список спостерігачів
        self._obs_lock = threading.Lock()

    def subscribe(self, book_id: int, observer: Observer):
        with self._obs_lock:
            if book_id not in self._observers:
                self._observers[book_id] = []
            self._observers[book_id].append(observer)

    def unsubscribe(self, book_id: int, observer: Observer):
        with self._obs_lock:
            if book_id in self._observers and observer in self._observers[book_id]:
                self._observers[book_id].remove(observer)

    def notify_book_available(self, book: Book):
        with self._obs_lock:
            observers = self._observers.get(book.id, [])
            for obs in observers:
                obs.update("Бажана книга знову доступна для видачі!", book)
