"""
Эмоциональная и семантическая память ROMIND.

Хранит краткую историю взаимодействий:
- текст пользователя
- активная персона
- социальная роль (мама/друг/партнёр/наставник и т.д.)
- эмоция ROMIND о пользователе
- уровень доверия

Плюс расширенный слой:
- биографические факты о пользователе
- семантические паттерны (темы и связанные эмоции)
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


# Отдельный лог, если захочется писать "сырые" события
MEMORY_LOG_FILE = "romind_memory_log.json"
# Ограничение размера истории
MAX_RECORDS = 300


# === 1. Базовая эмоциональная память ===

class RomindMemory:
    """
    Базовая JSON-память ROMIND.

    Записи формата:
    {
        "time": ISO-время,
        "user_text": str,
        "persona": str,
        "role_context": str | None,
        "emotion": str,
        "trust": float,
    }
    """

    MEMORY_FILE = "romind_memory.json"

    def __init__(self, path: Optional[str] = None) -> None:
        # Путь к файлу памяти (можно переопределить)
        self.path: str = path or self.MEMORY_FILE
        # ВСЕГДА список, никогда None
        self.data: List[Dict[str, Any]] = []
        # Подгружаем, если есть
        self._load()

    # --- Внутренние методы ---

    def _load(self) -> None:
        """Загружает память из файла, если он существует."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self.data = raw
                else:
                    self.data = []
            except Exception:
                self.data = []
        else:
            self.data = []

    def _save(self) -> None:
        """Сохраняет память в файл (обрезая до MAX_RECORDS)."""
        try:
            trimmed = self.data[-MAX_RECORDS:]
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(trimmed, f, ensure_ascii=False, indent=2)
        except Exception:
            # Память не должна рушить ROMIND
            pass

    # --- Публичные методы ---

    def remember(
        self,
        user_text: str,
        persona_id: str,
        role_context: Optional[str],
        emotion: str,
        trust: float,
    ) -> None:
        """Записывает одно эмоциональное событие."""
        record: Dict[str, Any] = {
            "time": datetime.utcnow().isoformat(),
            "user_text": user_text,
            "persona": persona_id,
            "role_context": role_context,
            "emotion": emotion,
            "trust": round(float(trust), 3),
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
        values = [float(r.get("trust", 0.0)) for r in self.data]
        return sum(values) / len(values)

    def recent_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Последние N записей для анализа."""
        return self.data[-limit:]


# === 2. Расширенный биографический слой памяти ===

class RomindFullMemory(RomindMemory):
    """
    Полная биографическая память ROMIND.

    Структура self.profile:
    {
        "primary": {  # базовая идентичность (не должна теряться)
            "name": str | None,
            "birthdate": str | None,
            "location": str | None,
            "occupation": str | None,
            "children": int | None,
            "partner": str | None,
        },
        "secondary": {  # интересы, привычки, вкусы, soft-факты
            "likes": [str],
            "dislikes": [str],
            "hobbies": [str],
            "values": [str],
            "possessions": [str],
        },
        "emotional": {  # эмоциональный портрет
            "baseline": str | None,      # общий тон
            "sensitive_topics": [str],   # к чему больно
            "comfort_topics": [str],     # что успокаивает
        },
        "meta": {
            "updated_at": str,           # последнее обновление
            "facts_count": int,          # сколько фактов собрано
        }
    }

    Чем дольше ROMIND общается с человеком, тем богаче становится профиль.
    Ничего важного не затирается без причины.
    """

    BIOGRAPHY_FILE = "romind_user_biography.json"

    def __init__(self, path: Optional[str] = None) -> None:
        super().__init__(path or RomindMemory.MEMORY_FILE)
        self.bio_path: str = self.BIOGRAPHY_FILE
        self.profile: Dict[str, Any] = self._load_biography()

    # --- Загрузка / сохранение ---

    def _empty_profile(self) -> Dict[str, Any]:
        return {
            "primary": {
                "name": None,
                "birthdate": None,
                "location": None,
                "occupation": None,
                "children": None,
                "partner": None,
            },
            "secondary": {
                "likes": [],
                "dislikes": [],
                "hobbies": [],
                "values": [],
                "possessions": [],
            },
            "emotional": {
                "baseline": None,
                "sensitive_topics": [],
                "comfort_topics": [],
            },
            "meta": {
                "updated_at": datetime.utcnow().isoformat(),
                "facts_count": 0,
            },
        }

    def _load_biography(self) -> Dict[str, Any]:
        if os.path.exists(self.bio_path):
            try:
                with open(self.bio_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # мягко дополняем недостающие поля
                    base = self._empty_profile()
                    for k, v in data.items():
                        if k in base and isinstance(v, dict):
                            base[k].update(v)
                        else:
                            base[k] = v
                    return base
            except Exception:
                pass
        return self._empty_profile()

    def _save_biography(self) -> None:
        try:
            self.profile["meta"]["updated_at"] = datetime.utcnow().isoformat()
            # пересчёт фактов
            facts = 0
            for section in ("primary", "secondary", "emotional"):
                block = self.profile.get(section, {})
                if isinstance(block, dict):
                    for v in block.values():
                        if isinstance(v, list):
                            facts += len([x for x in v if x])
                        elif v not in (None, "", 0):
                            facts += 1
            self.profile["meta"]["facts_count"] = facts

            with open(self.bio_path, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # --- Обновление профиля по тексту пользователя ---

    def update_profile(self, user_text: str) -> None:
        """
        Извлекает биографические сигналы из текста.
        Наращивает знания, не затирая уже известное.
        """
        text = user_text.lower()
        p = self.profile["primary"]
        s = self.profile["secondary"]
        e = self.profile["emotional"]

        # Имя
        if "меня зовут" in text and not p["name"]:
            name = text.split("меня зовут", 1)[-1].strip().split()[0]
            if name:
                p["name"] = name.capitalize()

        # Локация (город/страна)
        if "я живу" in text and not p["location"]:
            place = text.split("я живу", 1)[-1].strip().split()[0:5]
            if place:
                p["location"] = " ".join(place)

        # Работа
        if "я работаю" in text and not p["occupation"]:
            job = text.split("я работаю", 1)[-1].strip().split()[0:8]
            if job:
                p["occupation"] = " ".join(job)

        # Дети
        if "у меня трое детей" in text or "у меня 3 детей" in text:
            p["children"] = 3
        elif "у меня двое детей" in text or "у меня 2 детей" in text:
            p["children"] = 2
        elif "у меня один ребёнок" in text or "у меня 1 ребёнок" in text:
            p["children"] = 1

        # Партнёр (очень мягкий, без вторжения)
        if "мой муж" in text or "моя жена" in text or "мой парень" in text or "моя девушка" in text:
            p["partner"] = "есть"

        # Интересы
        if "я люблю" in text:
            fragment = text.split("я люблю", 1)[-1].strip()
            part = fragment.split(".")[0].split(",")[0:8]
            likes = s["likes"]
            item = " ".join(part).strip()
            if item:
                likes.append(item)
                s["likes"] = sorted(set(likes))

        # Вещи, которые важны
        if "у меня есть" in text:
            fragment = text.split("у меня есть", 1)[-1].strip()
            part = fragment.split(".")[0].split(",")[0:8]
            poss = s["possessions"]
            item = " ".join(part).strip()
            if item:
                poss.append(item)
                s["possessions"] = sorted(set(poss))

        # Эмоциональный baseline
        last = self.last_emotion()
        if last:
            # если baseline ещё не задан — задаём
            if not e["baseline"]:
                e["baseline"] = last

        self._save_biography()

    def summarize_profile(self) -> str:
        """Человеческое резюме того, что ROMIND уже знает о пользователе."""
        p = self.profile["primary"]
        s = self.profile["secondary"]
        e = self.profile["emotional"]
        meta = self.profile["meta"]

        likes = ", ".join(s["likes"]) if s["likes"] else "пока не делился интересами"
        poss = ", ".join(s["possessions"]) if s["possessions"] else "не отмечено"

        return (
            f"Имя: {p['name'] or 'друг'}\n"
            f"Место: {p['location'] or 'неизвестно'}\n"
            f"Работа: {p['occupation'] or 'не указана'}\n"
            f"Дети: {p['children'] if p['children'] is not None else 'не указано'}\n"
            f"Партнёр: {'есть' if p['partner'] else 'не указано'}\n"
            f"Интересы: {likes}\n"
            f"Важные вещи: {poss}\n"
            f"Эмоциональный фон: {e['baseline'] or 'пока формируется'}\n"
            f"Всего зафиксировано фактов: {meta.get('facts_count', 0)}"
        )

# === 3. Семантическая память ===

class RomindSemanticMemory(RomindFullMemory):
    """
    Семантическая память ROMIND:

    - считает, о чём чаще всего говорит пользователь (темы)
    - связывает темы с эмоциями
    """

    SEMANTIC_FILE = "romind_semantic_memory.json"

    def __init__(self, path: Optional[str] = None) -> None:
        super().__init__(path or RomindMemory.MEMORY_FILE)
        self.semantic_path: str = self.SEMANTIC_FILE
        self.semantic_index: Dict[str, Any] = self._load_semantics()

    def _load_semantics(self) -> Dict[str, Any]:
        if os.path.exists(self.semantic_path):
            try:
                with open(self.semantic_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {}

    def _save_semantics(self) -> None:
        try:
            with open(self.semantic_path, "w", encoding="utf-8") as f:
                json.dump(self.semantic_index, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def update_semantic_patterns(self, user_text: str, emotion: str) -> None:
        """
        Определяет частые темы (работа, семья, усталость, любовь и т.д.)
        и добавляет их в семантический индекс.
        """
        text = user_text.lower()

        THEMES: Dict[str, List[str]] = {
            "family": ["мама", "папа", "дети", "сын", "дочь", "семья", "родители"],
            "work": ["работа", "проект", "босс", "начальник", "офис", "коллег"],
            "health": ["боль", "здоровье", "болит", "устала", "устал", "сон"],
            "love": ["люблю", "поцелуй", "роман", "чувства", "партнёр", "парень", "девушка"],
            "self": ["я думаю", "я чувствую", "мне кажется", "я боюсь", "я хочу"],
            "money": ["деньги", "зарабатывать", "банк", "кредит", "оплата", "счёт"],
            "future": ["мечта", "будущее", "планы", "хочу построить", "проектировать"],
            "friends": ["друг", "подруга", "компания", "встреча", "разговор"],
        }

        matched: List[str] = []
        for theme, words in THEMES.items():
            if any(w in text for w in words):
                matched.append(theme)
                self.semantic_index[theme] = int(self.semantic_index.get(theme, 0)) + 1

        if not matched:
            return

        # эмоции по темам
        emo_map: Dict[str, Dict[str, int]] = self.semantic_index.setdefault("_emotions", {})
        for theme in matched:
            theme_emotions = emo_map.setdefault(theme, {})
            theme_emotions[emotion] = int(theme_emotions.get(emotion, 0)) + 1

        self._save_semantics()

    def get_top_themes(self, limit: int = 5):
        """Возвращает топ часто упоминаемых тем пользователя."""
        items = [
            (k, v)
            for k, v in self.semantic_index.items()
            if not k.startswith("_") and isinstance(v, int)
        ]
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:limit]

    def describe_emotional_patterns(self) -> str:
        """Создаёт сводку: с какими эмоциями связаны темы."""
        emo_map: Dict[str, Dict[str, int]] = self.semantic_index.get("_emotions", {})
        if not emo_map:
            return "Пока недостаточно данных для анализа."

        lines: List[str] = []
        for theme, emo_stats in emo_map.items():
            if not emo_stats:
                continue
            top_emo = max(emo_stats.items(), key=lambda x: x[1])[0]
            lines.append(f"Тема «{theme}» чаще связана с эмоцией «{top_emo}».")
        return "\n".join(lines) if lines else "Пока недостаточно данных для анализа."
