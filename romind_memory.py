# romind_memory.py
# Простая долговременная память ROMIND.
# Хранит то, что Светлана явно просит запомнить, и ключевые внутренние правила.

import json
import os
from datetime import datetime
from typing import List, Dict, Any

MEMORY_FILE = "romind_memory.json"


DEFAULT_MEMORY = {
    "version": 1,
    "last_updated": None,
    "rules": [],      # важные установки вида {"text": "...", "source": "...", "ts": "..."}
    "notes": []       # менее формальные заметки
}


class RomindMemory:
    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # дополняем недостающие поля
                for k, v in DEFAULT_MEMORY.items():
                    data.setdefault(k, v)
                return data
            except Exception:
                # если файл битый — не умираем, начинаем заново
                return DEFAULT_MEMORY.copy()
        return DEFAULT_MEMORY.copy()

    def _save(self):
        self.data["last_updated"] = datetime.utcnow().isoformat()
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            # не ломаем систему, если не можем записать
            pass

    def remember_rule(self, text: str, source: str = "user"):
        """Жёсткая установка: ценность, принцип, правило поведения ROMIND."""
        text = text.strip()
        if not text:
            return
        entry = {
            "text": text,
            "source": source,
            "ts": datetime.utcnow().isoformat()
        }
        self.data.setdefault("rules", []).append(entry)
        # ограничим размер, чтобы файл не разрастался бесконечно
        if len(self.data["rules"]) > 200:
            self.data["rules"] = self.data["rules"][-200:]
        self._save()

    def remember_note(self, text: str, source: str = "user"):
        """Мягкая заметка, не обязательно правило."""
        text = text.strip()
        if not text:
            return
        entry = {
            "text": text,
            "source": source,
            "ts": datetime.utcnow().isoformat()
        }
        self.data.setdefault("notes", []).append(entry)
        if len(self.data["notes"]) > 300:
            self.data["notes"] = self.data["notes"][-300:]
        self._save()

    def get_brief(self, limit: int = 10) -> str:
        """
        Краткое содержимое памяти для системного промпта:
        берём последние важные правила.
        """
        rules = self.data.get("rules", [])[-limit:]
        if not rules:
            return "No explicit long-term rules recorded yet."
        lines = [f"- {r['text']}" for r in rules]
        return "\n".join(lines)
