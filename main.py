#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СР №2: Створення об'єктно-орієнтованої системи управління базою даних книг у бібліотеці.

Демонстраційний скрипт:
- Метакласи (LoggingMeta)
- Декоратори валідації та логування
- Патерни проектування: Singleton, Factory, Observer
- Обробка виключень
- Мультипотоковість та потокобезпечність (ThreadPoolExecutor)

Автор: Ліпунов Д. О., група БІКСб.2.25.4.О.д.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from models import Author, Book, Reader
from metaclasses import LoggingMeta
from patterns import EntityFactory, ReaderNotificationObserver
from database import LibraryDatabase
from exceptions import (
    LibraryException, ValidationError,
    BookAlreadyBorrowedError, ReaderLimitExceededError
)


def demo_metaclass_and_factory():
    print("\n" + "="*60)
    print(">>> 1. ДЕМОНСТРАЦІЯ ФАБРИКИ (FACTORY) ТА МЕТАКЛАСУ (LOGGINGMETA)")
    print("="*60)

    # Створення сутностей через патерн Factory
    author1 = EntityFactory.create_author("Тарас Шевченко", "Україна")
    author2 = EntityFactory.create_author("Джордж Орвелл", "Велика Британія")

    book1 = EntityFactory.create_book("978-617-07-0245-1", "Кобзар", author1, 1840, total_copies=3)
    book2 = EntityFactory.create_book("978-0-452-28423-4", "1984", author2, 1949, total_copies=2)

    reader1 = EntityFactory.create_reader("Олександр Коваленко", "oleksandr@knu.ua", max_loans=2)
    reader2 = EntityFactory.create_reader("Марія Сидоренко", "maria@gmail.com", max_loans=3)

    print(f"Створено автора: {author1}")
    print(f"Створено автора: {author2}")
    print(f"Створено книгу: {book1}")
    print(f"Створено читача: {reader1}")

    # Звіт аудиту метакласу
    audit = LoggingMeta.get_audit_summary()
    print("\n[+] Аудит життєвого циклу об'єктів метакласом:")
    print(f"  * Зареєстровані класи: {audit['registered_classes']}")
    print(f"  * Кількість інстанційованих об'єктів: {audit['instance_counts']}")
    print(f"  * Останній лог метакласу: {audit['recent_logs'][-1]}")

    return [author1, author2], [book1, book2], [reader1, reader2]


def demo_decorators_and_exceptions():
    print("\n" + "="*60)
    print(">>> 2. ДЕМОНСТРАЦІЯ ДЕКОРАТОРІВ ВАЛІДАЦІЇ ТА ОБРОБКИ ВИКЛЮЧЕНЬ")
    print("="*60)
    dummy_author = Author(99, "Тестовий Автор")

    # Спроба 1: Некоректний ISBN (менше цифр)
    try:
        print("[Тест 1] Спроба створення книги з некоректним ISBN '12345'...")
        Book(991, "12345", "Некоректна Книга", dummy_author, 2020)
    except ValidationError as e:
        print(f"  [V] Успішно перехоплено ValidationError: {e}")

    # Спроба 2: Порожня назва книги
    try:
        print("[Тест 2] Спроба створення книги з порожньою назвою...")
        Book(992, "9781234567890", "   ", dummy_author, 2020)
    except ValidationError as e:
        print(f"  [V] Успішно перехоплено ValidationError: {e}")

    # Спроба 3: Некоректний Email читача
    try:
        print("[Тест 3] Спроба реєстрації читача з некоректним email 'bad_email'...")
        Reader(993, "Іван Іванов", "bad_email")
    except ValidationError as e:
        print(f"  [V] Успішно перехоплено ValidationError: {e}")


def demo_singleton_and_observer():
    print("\n" + "="*60)
    print(">>> 3. ДЕМОНСТРАЦІЯ SINGLETON ТА ПАТЕРНУ OBSERVER (СПОСТЕРІГАЧ)")
    print("="*60)

    # Перевірка Singleton: два виклики повертають один і той самий об'єкт
    db1 = LibraryDatabase()
    db2 = LibraryDatabase()
    print(f"db1 is db2: {db1 is db2} (id(db1)={id(db1)}, id(db2)={id(db2)})")
    assert db1 is db2, "Помилка патерну Singleton!"

    db1.clear()

    # Створюємо популярну книгу з 1 примірником
    author = EntityFactory.create_author("Роберт Мартін", "США")
    rare_book = EntityFactory.create_book("978-0132350884", "Чистий код (Clean Code)", author, 2008, total_copies=1)
    db1.add_author(author)
    db1.add_book(rare_book)

    reader_alice = EntityFactory.create_reader("Аліса", "alice@example.com")
    reader_bob = EntityFactory.create_reader("Боб", "bob@example.com")
    db1.register_reader(reader_alice)
    db1.register_reader(reader_bob)

    # Аліса бере єдиний примірник
    print(f"\nАліса позичає рідкісну книгу '{rare_book.title}'...")
    db1.borrow_book(reader_alice.id, rare_book.id)
    print(f"Стан книги: {rare_book}")

    # Боб хоче взяти ту саму книгу, але вільних копій немає -> оформлює підписку через Observer
    print("\nБоб намагається взяти ту саму книгу:")
    try:
        db1.borrow_book(reader_bob.id, rare_book.id)
    except BookAlreadyBorrowedError as e:
        print(f"  [!] Отримано відмову: {e}")
        print("  [+] Реєстрація читача Боб як підписника (Observer) на оновлення статусу книги...")
        bob_observer = ReaderNotificationObserver(reader_bob)
        db1.notification_service.subscribe(rare_book.id, bob_observer)

    # Аліса повертає книгу -> Observer автоматично сповіщає Боба!
    print("\nАліса повертає книгу до бібліотеки:")
    db1.return_book(reader_alice.id, rare_book.id)
    print(f"Стан книги після повернення: {rare_book}")


def demo_multithreading():
    print("\n" + "="*60)
    print(">>> 4. ДЕМОНСТРАЦІЯ МУЛЬТИПОТОКОВОСТІ (THREAD SAFETY ТА CONCURRENCY)")
    print("="*60)

    db = LibraryDatabase()
    db.clear()

    # Створюємо книгу з пулом лише з 3 примірників
    author = EntityFactory.create_author("Гвідо ван Россум", "Нідерланди")
    popular_book = EntityFactory.create_book(
        "978-1449355739", "Learning Python (Concurrency Edition)", author, 2013, total_copies=3
    )
    db.add_author(author)
    db.add_book(popular_book)

    # Створюємо 10 паралельних читачів
    readers: List[Reader] = []
    for i in range(1, 11):
        r = EntityFactory.create_reader(f"Потік-Читач-{i:02d}", f"reader_{i}@lib.org", max_loans=1)
        db.register_reader(r)
        readers.append(r)

    print(f"Початковий стан: Книга '{popular_book.title}', вільних примірників: {popular_book.available_copies}/3")
    print(f"Запуск 10 конкурентних потоків, які одночасно намагаються взяти книгу...")

    success_borrow = []
    failed_borrow = []

    def attempt_borrow(reader: Reader):
        time.sleep(0.01)  # Імітація мікрозатримки введення для посилення конкурентності
        try:
            loan = db.borrow_book(reader.id, popular_book.id)
            return True, reader.name, loan.id
        except BookAlreadyBorrowedError:
            return False, reader.name, "Немає вільних примірників"
        except Exception as ex:
            return False, reader.name, str(ex)

    # Використання пулу з 10 потоків
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_borrow, r) for r in readers]
        for f in as_completed(futures):
            ok, rname, info = f.result()
            if ok:
                success_borrow.append(rname)
                print(f"  [SUCCESS] {rname} успішно отримав книгу (Loan ID={info})")
            else:
                failed_borrow.append(rname)
                print(f"  [REJECTED] {rname}: {info}")

    print("\n--- Результати мультипотокового змагання (Race Condition Check) ---")
    print(f"Успішно отримали примірник ({len(success_borrow)}): {success_borrow}")
    print(f"Отримали коректну відмову ({len(failed_borrow)}): {failed_borrow}")
    print(f"Залишок вільних примірників: {popular_book.available_copies} (Очікується 0)")
    assert popular_book.available_copies == 0, "Критична помилка: порушено цілісність даних!"
    assert len(success_borrow) == 3, "Критична помилка: видано більше або менше за ліміт примірників!"
    print("[+] Тест мультипотоковості пройдено успішно: гонитву даних (race condition) усунено блокуванням!")

    stats = db.get_statistics()
    print(f"\nПідсумкова статистика БД: {stats}")


def main():
    print("#"*65)
    print(" СР №2: ОБ'ЄКТНО-ОРІЄНТОВАНА СИСТЕМА УПРАВЛІННЯ БІБЛІОТЕКОЮ")
    print(" Розробник: Ліпунов Д. О. (БІКСб.2.25.4.О.д)")
    print("#"*65)

    demo_metaclass_and_factory()
    demo_decorators_and_exceptions()
    demo_singleton_and_observer()
    demo_multithreading()

    print("\n" + "#"*65)
    print(" ВСІ ВИМОГИ СР №2 ПОВНІСТЮ ТА УСПІШНО ВИКОНАНО!")
    print("#"*65)


if __name__ == "__main__":
    main()
