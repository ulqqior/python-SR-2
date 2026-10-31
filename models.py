#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль сутностей предметної області бібліотеки.
Усі класи використовують метаклас LoggingMeta для аудиту.
"""

from typing import List, Optional
from datetime import datetime
from metaclasses import LoggingMeta
from decorators import validate_isbn, validate_string, positive_int
from exceptions import ValidationError


class Author(metaclass=LoggingMeta):
    """Модель автора книги."""

    def __init__(self, author_id: int, name: str, country: str = "Україна"):
        if not name or not isinstance(name, str):
            raise ValidationError("Ім'я автора не може бути порожнім.")
        self.id = author_id
        self.name = name.strip()
        self.country = country.strip()

    def __repr__(self):
        return f"<Author id={self.id} name='{self.name}' ({self.country})>"


class Book(metaclass=LoggingMeta):
    """Модель книги бібліотечного фонду."""

    @validate_isbn
    def __init__(self, book_id: int, isbn: str, title: str, author: Author,
                 year: int, total_copies: int = 1):
        if not title or len(title.strip()) < 1:
            raise ValidationError("Назва книги не може бути порожньою.")
        if year < 1400 or year > datetime.now().year + 1:
            raise ValidationError(f"Некоректний рік видання: {year}.")
        if total_copies < 1:
            raise ValidationError("Кількість примірників книги має бути не менше 1.")

        self.id = book_id
        self.isbn = isbn
        self.title = title.strip()
        self.author = author
        self.year = year
        self.total_copies = total_copies
        self.available_copies = total_copies

    def is_available(self) -> bool:
        """Перевіряє, чи є вільні примірники книги."""
        return self.available_copies > 0

    def borrow_copy(self):
        """Зменшує кількість доступних примірників."""
        if self.available_copies <= 0:
            raise ValidationError(f"Немає вільних примірників книги '{self.title}'.")
        self.available_copies -= 1

    def return_copy(self):
        """Збільшує кількість доступних примірників."""
        if self.available_copies >= self.total_copies:
            raise ValidationError(f"Кількість вільних примірників перевищує загальний фонд книги '{self.title}'.")
        self.available_copies += 1

    def to_dict(self):
        return {
            "id": self.id,
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author.name,
            "year": self.year,
            "available_copies": self.available_copies,
            "total_copies": self.total_copies
        }

    def __repr__(self):
        return f"<Book id={self.id} '{self.title}' (Доступно: {self.available_copies}/{self.total_copies})>"


class Reader(metaclass=LoggingMeta):
    """Модель читача бібліотеки."""

    def __init__(self, reader_id: int, name: str, email: str, max_loans: int = 3):
        if not name or len(name.strip()) < 2:
            raise ValidationError("Ім'я читача має містити щонайменше 2 символи.")
        if "@" not in email or "." not in email:
            raise ValidationError(f"Некоректний формат email: '{email}'.")
        if max_loans < 1:
            raise ValidationError("Максимальний ліміт книг має бути не менше 1.")

        self.id = reader_id
        self.name = name.strip()
        self.email = email.strip()
        self.max_loans = max_loans
        self.borrowed_books: List[int] = []  # Список ID позичених книг

    def can_borrow(self) -> bool:
        return len(self.borrowed_books) < self.max_loans

    def __repr__(self):
        return f"<Reader id={self.id} name='{self.name}' (Позичено: {len(self.borrowed_books)}/{self.max_loans})>"


class Loan:
    """Запис про факт видачі книги читачеві."""

    def __init__(self, loan_id: int, reader: Reader, book: Book):
        self.id = loan_id
        self.reader = reader
        self.book = book
        self.borrowed_at = datetime.now()
        self.returned_at: Optional[datetime] = None

    def close_loan(self):
        self.returned_at = datetime.now()

    @property
    def is_active(self) -> bool:
        return self.returned_at is None
