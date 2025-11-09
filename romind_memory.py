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
# === 2. Расширенный биографический слой памяти (Full Memory Layer) ===

class RomindFullMemory(RomindMemory):
    """
    Расширенная память ROMIND:
    - хранит не только эмоции, но и знания о пользователе
    - постепенно формирует биографию: факты, интересы, окружение
    - обновляется по мере общения
    """

    BIOGRAPHY_FILE = "romind_user_biography.json"

    def __init__(self, path: str = RomindMemory.MEMORY_FILE):
        super().__init__(path)
        self.bio_path = self.BIOGRAPHY_FILE
        self.profile = self._load_biography()

    def _load_biography(self):
        """Загружает биографическую информацию."""
        if os.path.exists(self.bio_path):
            try:
                with open(self.bio_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_biography(self):
        """Сохраняет обновлённую биографию."""
        try:
            with open(self.bio_path, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # === Анализ и добавление фактов ===

    def update_profile(self, user_text: str):
        """
        Анализирует текст пользователя и добавляет новые факты о нём.
        Распознаёт паттерны вроде: 'я живу в...', 'у меня есть дети', 'я люблю...', 'моя работа...'
        """
        text = user_text.lower()

        # === Обнаружение базовых фактов ===
        if "я живу" in text:
            place = text.split("я живу")[-1].strip().split()[0:4]
            self.profile["location"] = " ".join(place)
        if "меня зовут" in text:
            name = text.split("меня зовут")[-1].strip().split()[0]
            self.profile["name"] = name.capitalize()
        if "я люблю" in text:
            love = text.split("я люблю")[-1].strip().split(",")[0:6]
            loves = self.profile.get("likes", [])
            loves.append(" ".join(love))
            self.profile["likes"] = list(set(loves))
        if "моя работа" in text or "я работаю" in text:
            job = text.split("работаю")[-1].strip().split()[0:6]
            self.profile["occupation"] = " ".join(job)
        if "у меня есть" in text:
            thing = text.split("у меня есть")[-1].strip().split(",")[0:6]
            owned = self.profile.get("possessions", [])
            owned.append(" ".join(thing))
            self.profile["possessions"] = list(set(owned))
        if "у меня трое детей" in text or "у меня 3 детей" in text:
            self.profile["children"] = 3
        elif "у меня двое детей" in text or "у меня 2 детей" in text:
            self.profile["children"] = 2
        elif "у меня один ребёнок" in text or "у меня 1 ребёнок" in text:
            self.profile["children"] = 1

        # === Запоминаем эмоциональный оттенок высказывания ===
        last_emotion = self.last_emotion()
        if last_emotion:
            self.profile["emotional_tone"] = last_emotion

        # === Сохраняем обновления ===
        self._save_biography()

    def summarize_profile(self) -> str:
        """Создаёт краткий человеческий портрет пользователя на основе данных."""
        name = self.profile.get("name", "друг")
        location = self.profile.get("location", "неизвестно где")
        job = self.profile.get("occupation", "не указана работа")
        likes = ", ".join(self.profile.get("likes", [])) or "пока не делился интересами"
        children = self.profile.get("children", "не указано")

        return (
            f"Имя: {name}\n"
            f"Место проживания: {location}\n"
            f"Работа: {job}\n"
            f"Интересы: {likes}\n"
            f"Дети: {children}\n"
            f"Последний эмоциональный фон: {self.profile.get('emotional_tone', 'спокойный')}"
        )
