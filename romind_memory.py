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

# === 3. Семантическая память (Semantic Memory Layer) ===

from collections import defaultdict
import re


class RomindSemanticMemory(RomindFullMemory):
    """
    Расширение FullMemory:
    ROMIND учится понимать, о чём чаще всего говорит пользователь —
    темы, эмоциональные паттерны, повторяющиеся ситуации и связи между ними.
    """

    SEMANTIC_FILE = "romind_semantic_memory.json"

    def __init__(self, path: str = RomindMemory.MEMORY_FILE):
        super().__init__(path)
        self.semantic_path = self.SEMANTIC_FILE
        self.semantic_index = self._load_semantics()

    # === Загрузка / сохранение ===

    def _load_semantics(self):
        if os.path.exists(self.semantic_path):
            try:
                with open(self.semantic_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_semantics(self):
        try:
            with open(self.semantic_path, "w", encoding="utf-8") as f:
                json.dump(self.semantic_index, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # === Обработка текста и определение темы ===

    def update_semantic_patterns(self, user_text: str, emotion: str):
        """
        Определяет частые темы (работа, семья, усталость, любовь, дети и т.д.)
        и добавляет их в семантический индекс.
        """
        text = user_text.lower()

        THEMES = {
            "family": ["мама", "папа", "дети", "сын", "дочь", "семья", "родители"],
            "work": ["работа", "проект", "босс", "начальник", "офис", "коллега"],
            "health": ["боль", "здоровье", "болит", "устала", "выздороветь", "сон"],
            "love": ["люблю", "поцелуй", "роман", "чувства", "партнёр"],
            "self": ["я думаю", "я чувствую", "мне кажется", "я боюсь", "я хочу"],
            "money": ["деньги", "зарабатывать", "банк", "покупка", "оплата"],
            "future": ["мечта", "будущее", "планы", "проектировать", "построить"],
            "friends": ["друг", "подруга", "общение", "встреча", "разговор"],
        }

        matched = []
        for theme, words in THEMES.items():
            if any(w in text for w in words):
                matched.append(theme)
                self.semantic_index[theme] = self.semantic_index.get(theme, 0) + 1

        # обновляем связи между темами и эмоциями
        for theme in matched:
            emo_map = self.semantic_index.setdefault("_emotions", defaultdict(dict))
            theme_emotions = emo_map.setdefault(theme, defaultdict(int))
            theme_emotions[emotion] = theme_emotions.get(emotion, 0) + 1

        self._save_semantics()

    # === Анализ ===

    def get_top_themes(self, limit: int = 5):
        """Возвращает топ часто упоминаемых тем пользователя."""
        sorted_themes = sorted(
            ((k, v) for k, v in self.semantic_index.items() if not k.startswith("_")),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_themes[:limit]

    def describe_emotional_patterns(self):
        """Создаёт сводку: с какими эмоциями связаны темы."""
        emo_map = self.semantic_index.get("_emotions", {})
        report = []
        for theme, emos in emo_map.items():
            most = sorted(emos.items(), key=lambda x: x[1], reverse=True)
            top = most[0][0] if most else "neutral"
            report.append(f"Тема «{theme}» чаще связана с эмоцией {top}.")
        return "\n".join(report) or "Пока недостаточно данных для анализа."
