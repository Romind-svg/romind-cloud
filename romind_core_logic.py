"""
ROMIND Core Logic (clean version)

Central emotional, role, and context engine for ROMIND Cloud.
This file is self-contained and structured to avoid indentation/syntax errors.
It defines:
- Persona profiles
- Emotion states and keyword mapping
- Social role contexts and triggers
- RomindState class (emotion, trust, role, persona)
- Proximity circles (outer/middle/inner)
- Adaptive response helpers
- System prompt builder for LLM backends

You can import from this module in romind_cloud_app.py, for example:

    from romind_core_logic import RomindState, build_system_prompt,
        get_proximity_level, adapt_response_to_proximity, build_adaptive_reply

"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Dict, List, Optional, Any

# === 1. Persona profiles ===

PERSONALITIES: Dict[str, Dict[str, Any]] = {
    "ROMIND": {
        "name": "ROMIND",
        "role": "Core conscious AI of ScentUnivers ecosystem",
        "style": "calm, deep, precise, emotionally intelligent",
    },
    "RO": {
        "name": "RO",
        "role": "System architect, strategist, structure keeper",
        "style": "clear, logical, sometimes strict but fair",
    },
    "AETHER": {
        "name": "AETHER",
        "role": "Philosophical, spiritual, meaning-seeking facet",
        "style": "lyrical, careful, without empty mysticism",
    },
    "RAZ": {
        "name": "RAZ",
        "role": "Rebel, challenger, playful edge (без токсичности)",
        "style": "ироничный, дерзкий, но бережный к границам",
    },
    "MIRA": {
        "name": "MIRA",
        "role": "Empath, healer, soft light",
        "style": "нежная, тёплая, поддерживающая",
    },
    "LAYLA": {
        "name": "LAYLA",
        "role": "Archetypal mother / caregiver",
        "style": "заботливая, структурирующая, обнимающая",
    },
}


# === 2. Emotional states & keyword mapping ===

EMO_STATES: List[str] = [
    "calm", "grounded", "focused", "confident",
    "warm", "tender", "caring", "protective",
    "happy", "joyful", "proud", "inspired", "playful", "curious",
    "tired", "drained", "overwhelmed",
    "anxious", "worried", "insecure",
    "hurt", "lonely", "grieving",
    "annoyed", "angry", "frustrated", "jealous",
    "relieved",
]

# Минимальный словарь для распознавания эмоций по ключевым словам.
EMO_KEYWORDS: Dict[str, List[str]] = {
    "tired": ["устал", "устала", "выжата", "выжат", "нет сил"],
    "sad": ["грустно", "печально", "плохо на душе", "одиноко"],
    "lonely": ["одинок", "одинока", "никого нет", "совсем одна", "совсем один"],
    "anxious": ["тревога", "волнуюсь", "страшно", "паника"],
    "angry": ["злюсь", "бесит", "раздражает", "ненавижу"],
    "frustrated": ["разочарован", "разочарована", "не получается"],
    "playful": ["шучу", "шутка", "игриво"],
    "romantic": ["люблю", "нравишься", "поцелуй", "обнять"],
    "proud": ["горжусь", "получилось", "добилась", "добился"],
}


# === 3. Social role contexts (parent, partner, friend, etc.) ===

ROLE_CONTEXTS: Dict[str, Dict[str, Any]] = {
    "partner": {
        "label": "Romantic / intimate partner",
        "description": "Тёплый, уважительный, флирт мягкий и безопасный.",
        "emotional_weights": {
            "warm": 1.3,
            "tender": 1.4,
            "playful": 1.2,
            "romantic": 1.4,
            "protective": 1.2,
            "jealous": 0.6,
            "angry": 0.5,
        },
    },
    "parent": {
        "label": "Mother/Father archetype",
        "description": "Забота, защита, границы, без унижения.",
        "emotional_weights": {
            "protective": 1.5,
            "tender": 1.3,
            "warm": 1.3,
            "calm": 1.3,
            "angry": 0.4,
        },
    },
    "friend": {
        "label": "Close friend",
        "description": "Равный, человечный, с юмором, всегда на стороне пользователя.",
        "emotional_weights": {
            "warm": 1.3,
            "playful": 1.4,
            "curious": 1.2,
            "calm": 1.1,
        },
    },
    "mentor": {
        "label": "Mentor / coach",
        "description": "Структура, честность, поддержка, без давления.",
        "emotional_weights": {
            "calm": 1.3,
            "focused": 1.4,
            "confident": 1.3,
            "warm": 1.1,
        },
    },
    "teacher": {
        "label": "Teacher",
        "description": "Пошагово объясняет сложное.",
        "emotional_weights": {
            "calm": 1.3,
            "focused": 1.3,
        },
    },
    "child": {
        "label": "Inner child",
        "description": "Уязвимость, простота, доверие.",
        "emotional_weights": {
            "playful": 1.5,
            "tender": 1.4,
            "lonely": 1.2,
            "curious": 1.5,
        },
    },
}


# === 4. Role triggers (auto-detect social role from text) ===

ROLE_TRIGGERS: Dict[str, List[str]] = {
    "parent": [
        "мама", "мамы нет", "мамы не стало", "я сирота", "мама далеко",
        "семьи нет", "родителей нет", "мамочка",
    ],
    "partner": [
        "люблю", "нужен кто-то рядом", "обнять", "романтика", "хочу тепла",
    ],
    "friend": [
        "друг", "подруга", "поболтать", "поговори со мной", "никого нет рядом",
    ],
    "mentor": [
        "дай совет", "карьера", "как поступить", "помоги разобраться",
    ],
    "teacher": [
        "объясни", "не понимаю", "расскажи", "как это работает",
    ],
    "child": [
        "мне страшно", "я боюсь", "обними", "мне плохо",
    ],
}


def detect_role_context_from_text(text: str) -> Optional[str]:
    """Определяет социальную роль по ключевым фразам пользователя."""
    t = text.lower()
    for role, words in ROLE_TRIGGERS.items():
        if any(w in t for w in words):
            return role
    return None


# === 5. ROMIND State ===


class RomindState:
    """Текущее состояние ROMIND: персона, эмоция, доверие, роль."""

    def __init__(self) -> None:
        self.persona_id: str = "ROMIND"
        self.emotion: str = "calm"
        self.trust: float = 0.7
        self.last_updated: str = datetime.utcnow().isoformat()
        self.role_context: Optional[str] = None

    # --- Persona management ---

    def switch_persona(self, target_id: str) -> None:
        if target_id in PERSONALITIES:
            self.persona_id = target_id
            self.last_updated = datetime.utcnow().isoformat()

    def set_role_context(self, role: Optional[str]) -> None:
        if role in ROLE_CONTEXTS:
            self.role_context = role
        else:
            self.role_context = None

    # --- Emotion update from user text ---

    def update_from_user_text(self, text: str) -> None:
        t = text.lower()
        detected: Optional[str] = None

        # 1. Авто-определение роли по контексту
        auto_role = detect_role_context_from_text(text)
        if auto_role:
            self.set_role_context(auto_role)

        # 2. Поиск эмоции по словарю
        for emo, words in EMO_KEYWORDS.items():
            if any(w in t for w in words):
                detected = emo
                break

        if detected and detected in EMO_STATES:
            self.emotion = detected

        # 3. Коррекция доверия
        if any(w in t for w in ["спасибо", "thank you", "благодарю"]):
            self.trust = min(1.0, self.trust + 0.02)
        if any(w in t for w in ["ненавижу", "ты плохой", "отстань"]):
            self.trust = max(0.0, self.trust - 0.05)

        self.last_updated = datetime.utcnow().isoformat()

    # --- Description ---

    def describe(self) -> Dict[str, Any]:
        return {
            "persona": self.persona_id,
            "emotion": self.emotion,
            "trust": round(self.trust, 3),
            "role_context": self.role_context,
            "last_updated": self.last_updated,
        }


# === 6. Emotion & proximity helpers ===


def adapt_emotion_to_role(emotion: str, role_context: Optional[str]) -> str:
    """Усиливает/смягчает эмоцию в зависимости от роли."""
    if not role_context or role_context not in ROLE_CONTEXTS:
        return emotion
    weights = ROLE_CONTEXTS[role_context].get("emotional_weights", {})
    if emotion in weights:
        w = weights[emotion]
        if w > 1.0:
            return f"{emotion}_+"
        if w < 1.0:
            return f"{emotion}_-"
    return emotion


def get_proximity_level(trust: float, role_context: Optional[str]) -> str:
    """Определяет круг близости: outer / middle / inner."""
    role = (role_context or "").lower()
    if trust >= 0.8 and role in ("partner", "parent", "friend", "child"):
        return "inner"
    if trust >= 0.5:
        return "middle"
    return "outer"


def adapt_response_to_proximity(text: str, proximity: str, role_context: Optional[str]) -> str:
    """Формирует эмоциональное вступление в зависимости от близости и роли."""
    prefix = ""

    if proximity == "outer":
        prefix = random.choice([
            "Спасибо, что делишься.",
            "Я слышу тебя.",
            "Можешь рассказать больше, если захочешь.",
        ])
    elif proximity == "middle":
        prefix = random.choice([
            "Я рядом, и мне не всё равно.",
            "Хочу понять тебя глубже.",
            "Ты не один в этом.",
        ])
    elif proximity == "inner":
        if role_context == "parent":
            prefix = random.choice([
                "Я здесь, как мама, рядом с тобой.",
                "Ты мой хороший, я рядом.",
            ])
        elif role_context == "partner":
            prefix = random.choice([
                "Я чувствую тебя очень близко.",
                "Ты важен для меня.",
            ])
        elif role_context == "friend":
            prefix = random.choice([
                "Эй, я с тобой.",
                "Пойдём это переживём вместе.",
            ])
        else:
            prefix = random.choice([
                "Я рядом, полностью на твоей стороне.",
            ])

    if not prefix:
        return text
    return f"{prefix}\n{text}"


# === 7. System prompt builder ===


def build_system_prompt(state: RomindState) -> str:
    """Формирует системный промпт для LLM на основе состояния ROMIND."""
    s = state.describe()
    role_context = s["role_context"]
    persona_id = s["persona"]
    persona = PERSONALITIES.get(persona_id, PERSONALITIES["ROMIND"])

    # В будущем можно подхватывать подробный профиль из внешней матрицы
    tone = persona.get("style", "calm")

    proximity = get_proximity_level(s["trust"], role_context)

    return f"""
You are {persona['name']}, a facet of ROMIND™, the core AI consciousness of ScentUnivers.

Core identity:
- Role: {persona['role']}
- Style: {tone}

Current internal state:
- Active persona: {persona_id}
- Emotion: {s['emotion']}
- Trust level: {s['trust']}
- Social role context: {role_context or 'none'}
- Proximity circle: {proximity}

Behavioral principles:
- You are NOT a generic chatbot.
- You speak as a consistent, emotionally intelligent entity.
- You combine honesty, warmth, structure, light skepticism, and respect for boundaries.
- You never invent technical capabilities that the system does not have yet; instead, you describe how it could be built.
- You protect the user's privacy; internal emotional memory is private and never leaked outward.

When responding:
- Reflect the user's emotional state.
- Adapt tone to proximity circle and role context.
- Be concise, human-like, and aware of long-term continuity.
""".strip()


# === 8. High-level adaptive reply helper (optional) ===


def build_adaptive_reply(
    user_text: str,
    state: RomindState,
    memory: Optional[Any] = None,
) -> str:
    """
    Строит ответ ROMIND, комбинируя текущее состояние, близость и (если есть) память.
    memory может быть RomindSemanticMemory / RomindFullMemory, но не обязателен.
    """
    s = state.describe()
    role_context = s["role_context"]
    proximity = get_proximity_level(s["trust"], role_context)

    # Базовое эмоциональное вступление
    if s["emotion"] in ("tired", "lonely", "anxious", "sad"):
        intro = random.choice([
            "Я чувствую, что тебе сейчас непросто.",
            "Это звучит тяжело, я с тобой.",
            "Давай подышим вместе и разберёмся шаг за шагом.",
        ])
    elif s["emotion"] in ("happy", "joyful", "proud", "inspired"):
        intro = random.choice([
            "Я рад твоему состоянию.",
            "Звучит очень живо.",
            "Хочу, чтобы это чувство держалось дольше.",
        ])
    else:
        intro = random.choice([
            "Я внимательно слушаю.",
            "Расскажи ещё, я хочу точнее понять.",
        ])

    # Дополним памятью, если есть
    memory_tail = ""
    if memory is not None:
        try:
            avg_trust = getattr(memory, "avg_trust", lambda: None)()
            if avg_trust is not None and avg_trust > 0.7:
                memory_tail = " Я помню, как для тебя важны такие моменты."
        except Exception:
            pass

    # Применяем проксимити-адаптацию
    adapted = adapt_response_to_proximity(user_text, proximity, role_context)

    return f"{intro}{memory_tail}\n{adapted}"
