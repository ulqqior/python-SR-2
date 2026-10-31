#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль потокобезпечної бази даних бібліотеки з реалізацією бізнес-логіки.
"""

import threading
from typing import Dict, List, Optional, Any
from patterns import ThreadSafeSingletonMeta, BookSubject
from models import Book, Author, Reader, Loan
from exceptions import (
    BookNotFoundError, ReaderNotFoundError,
    BookAlreadyBorrowedError, ReaderLimitExceededError, ValidationError
)


class LibraryDatabase(metaclass=ThreadSafeSingletonMeta):
    """
    Потокобезпечне сховище та менеджер операцій бібліотеки.
    Використовує SingletonMeta та блокування RLock для захисту від стану гонитви (race conditions).
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.books: Dict[int, Book] = {}
        self.authors: Dict[int, Author] = {}
        self.readers: Dict[int, Reader] = {}
        self.loans: Dict[int, Loan] = {}
        self.notification_service = BookSubject()
        self._loan_seq = 0

    def clear(self):
        """Очищення бази для повторного запуску тестів."""
        with self._lock:
            self.books.clear()
            self.authors.clear()
            self.readers.clear()
            self.loans.clear()
            self._loan_seq = 0

    def add_author(self, author: Author):
        with self._lock:
            self.authors[author.id] = author

    def add_book(self, book: Book):
        with self._lock:
            self.books[book.id] = book

    def register_reader(self, reader: Reader):
        with self._lock:
            self.readers[reader.id] = reader

    def get_book(self, book_id: int) -> Book:
        with self._lock:
            if book_id not in self.books:
                raise BookNotFoundError(f"Книгу з ID={book_id} не знайдено.")
            return self.books[book_id]

    def get_reader(self, reader_id: int) -> Reader:
        with self._lock:
            if reader_id not in self.readers:
                raise ReaderNotFoundError(f"Читача з ID={reader_id} не знайдено.")
            return self.readers[reader_id]

    def borrow_book(self, reader_id: int, book_id: int) -> Loan:
        """
        Атомарна операція видачі книги читачеві.
        Захищена RLock для запобігання надлишкової видачі в умовах багатопоточності.
        """
        with self._lock:
            reader = self.get_reader(reader_id)
            book = self.get_book(book_id)

            if not reader.can_borrow():
                raise ReaderLimitExceededError(
                    f"Читач '{reader.name}' досяг ліміту позичок ({reader.max_loans})."
                )

            if not book.is_available():
                raise BookAlreadyBorrowedError(
                    f"Усі примірники книги '{book.title}' наразі видані."
                )

            # Видаємо книгу
            book.borrow_copy()
            reader.borrowed_books.append(book.id)

            self._loan_seq += 1
            loan = Loan(loan_id=self._loan_seq, reader=reader, book=book)
            self.loans[loan.id] = loan
            return loan

    def return_book(self, reader_id: int, book_id: int) -> bool:
        """
        Атомарна операція повернення книги.
        Оновлює лічильник, закриває абонемент та сповіщає чергу спостерігачів.
        """
        with self._lock:
            reader = self.get_reader(reader_id)
            book = self.get_book(book_id)

            if book.id not in reader.borrowed_books:
                raise ValidationError(
                    f"Читач '{reader.name}' не має зареєстрованої позички на '{book.title}'."
                )

            # Знаходимо активний абонемент
            for loan in self.loans.values():
                if loan.reader.id == reader_id and loan.book.id == book_id and loan.is_active:
                    loan.close_loan()
                    break

            reader.borrowed_books.remove(book.id)
            book.return_copy()

            # Сповіщення через патерн Observer
            self.notification_service.notify_book_available(book)
            return True

    def search_books(self, query: str) -> List[Book]:
        """Пошук книг за назвою або автором."""
        with self._lock:
            q = query.lower().strip()
            return [
                b for b in self.books.values()
                if q in b.title.lower() or q in b.author.name.lower() or q in b.isbn
            ]

    def get_statistics(self) -> Dict[str, Any]:
        """Отримання агрегованої статистики."""
        with self._lock:
            total_books_fund = sum(b.total_copies for b in self.books.values())
            available_fund = sum(b.available_copies for b in self.books.values())
            active_loans = sum(1 for l in self.loans.values() if l.is_active)
            return {
                "total_unique_titles": len(self.books),
                "total_fund_copies": total_books_fund,
                "available_copies": available_fund,
                "borrowed_copies": total_books_fund - available_fund,
                "registered_readers": len(self.readers),
                "active_loans": active_loans
            }
