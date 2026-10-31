#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль метакласів для аудиту та логування життєвого циклу об'єктів.
"""

from datetime import datetime
from typing import Dict, Any, List


class LoggingMeta(type):
    """
    Метаклас для автоматичного аудиту класів та їхніх екземплярів.
    - Фіксує час реєстрації класу інтерпретатором.
    - Підраховує кількість створених екземплярів.
    - Додає системні атрибути аудиту до кожного об'єкта.
    """

    # Реєстр створених класів та лічильників
    _instances_registry: Dict[str, int] = {}
    _audit_logs: List[str] = []

    def __new__(mcs, name, bases, namespace):
        # Логуємо конструювання самого класу
        cls = super().__new__(mcs, name, bases, namespace)
        mcs._instances_registry[name] = 0
        log_msg = f"[METACLASS] Зареєстровано клас: '{name}' о {datetime.now().strftime('%H:%M:%S.%f')[:-3]}"
        mcs._audit_logs.append(log_msg)
        return cls

    def __call__(cls, *args, **kwargs):
        # Перехоплюємо інстанціювання (виклик ClassName(...))
        instance = super().__call__(*args, **kwargs)
        cls_name = cls.__name__
        LoggingMeta._instances_registry[cls_name] = LoggingMeta._instances_registry.get(cls_name, 0) + 1
        
        # Додаємо мітку часу створення безпосередньо до об'єкта
        setattr(instance, "_created_at", datetime.now().isoformat())
        setattr(instance, "_instance_id", LoggingMeta._instances_registry[cls_name])
        
        log_msg = f"[METACLASS] Створено екземпляр #{LoggingMeta._instances_registry[cls_name]} класу '{cls_name}'"
        LoggingMeta._audit_logs.append(log_msg)
        return instance

    @classmethod
    def get_audit_summary(mcs) -> Dict[str, Any]:
        """Повертає зведений звіт аудиту метакласу."""
        return {
            "registered_classes": list(mcs._instances_registry.keys()),
            "instance_counts": dict(mcs._instances_registry),
            "logs_count": len(mcs._audit_logs),
            "recent_logs": mcs._audit_logs[-5:]
        }
