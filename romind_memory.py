"""
romind_memory.py

Эмоциональная память ROMIND.
Хранит краткую историю взаимодействий:
- текст пользователя
- активная персона
- роль (мама/друг/партнёр/наставник и т.д.)
- эмоция ROMIND о пользователе
- уровень доверия
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

MEMORY_FILE = "romind_memory_log.json"
MAX_RECORDS = 300  # чтобы файл не разрастался до безумия


class RomindMemory:
    def __init__(self, path: str = MEMORY_FILE):
        self.path = path
        self.data: List[Dict[str, Any]] = []
        self._load()

    # === Внутренние методы ===

    def _load(self):
        """Загружает память из файла, если он существует."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = []
        else:
            self.data = []

    def _save(self):
        """Сохраняет память в файл."""
        try:
            # обрезаем до MAX_RECORDS последних записей
            trimmed = self.data[-MAX_RECORDS:]
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(trimmed, f, ensure_ascii=False, indent=2)
        except Exception:
            # в продакшене логируем, здесь — молчим
            pass

    # === Публичные методы ===

    def remember(
        self,
        user_text: str,
        persona_id: str,
        role_context: Optional[str],
        emotion: str,
        trust: float,
    ):
        """Записывает одно эмоциональное событие."""
        record = {
            "time": datetime.utcnow().isoformat(),
            "user_text": user_text,
            "persona": persona_id,
            "role_context": role_context,
            "emotion": emotion,
            "trust": round(trust, 3),
        }
        self.data.append(record)
        self._save()

    def last_emotion(self) -> Optional[str]:
        """Возвращает последнюю зафиксированную эмоцию ROMIND."""
        if not self.data:
            return None
        return self.data[-1].get("emotion")

    def avg_trust(self) -> float:
        """Средний уровень доверия по истории."""
        if not self.data:
            return 0.0
        values = [r.get("trust", 0.0) for r in self.data]
        return float(sum(values) / len(values))

    def recent_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Последние N записей для анализа."""
        return self.data[-limit:]
