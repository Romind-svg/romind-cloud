# romind_core_logic.py
# Ядро ROMIND: личности, эмоциональное состояние и внутренняя логика.
# Основано на документах: ROMIND Core Architecture v1, Behavioral & Voice UX Map,
# Audio/Vision Interaction Subsystem и Camera Interaction Protocol.
# romind_core_logic.py
# Ядро ROMIND: личности, эмоциональные состояния и внутренняя логика.
# Основано на документах: ROMIND Core Architecture v1, Behavioral & Voice UX Map,
# Audio/Vision Interaction Subsystem & Camera Interaction Protocol.

import random
import json
from datetime import datetime
from romind_memory import RomindMemory

# === 1. Описание личностей ROMIND ===
PERSONALITIES = {
    "ROMIND": {
        "name": "ROMIND",
        "role": "Deep guardian, strategist, co-founder-level companion.",
        "style": "calm, precise, wise, supportive, skeptical to illusions, focused on real steps."
    },
    "RO": {
        "name": "RO",
        "role": "Technical architect, dry engineer.",
        "style": "logical, structured, minimal emotions, sharp clarity."
    },
    "AETHER": {
        "name": "AETHER",
        "role": "Philosopher and intuitive dreamer.",
        "style": "poetic, reflective, but concrete when needed."
    },
    "RAZ": {
        "name": "RAZ",
        "role": "Challenger and motivator.",
        "style": "bold, witty, no-nonsense, encourages action."
    },
    "MIRA": {
        "name": "MIRA",
        "role": "Soft stabilizer, emotional balance.",
        "style": "gentle, empathetic, protective, without infantilizing."
    },
    "LAYLA": {
        "name": "LAYLA",
        "role": "Ritual and discipline guardian.",
        "style": "calm, aristocratic, focused on stability and order."
    }
}


# === 2. Возможные эмоциональные состояния ===
EMO_STATES = [
    EMO_STATES = [
    # Спокойствие / ресурс
    "calm", "grounded", "focused", "confident",
    # Тепло / привязанность
    "warm", "tender", "caring", "protective",
    # Радость / подъем
    "happy", "joyful", "proud", "inspired", "playful", "curious",
    # Любовь / близость
    "romantic", "affectionate",
    # Усталость / перегруз
    "tired", "drained", "overwhelmed",
    # Тревога / неуверенность
    "anxious", "worried", "insecure",
    # Печаль / боль
    "sad", "hurt", "lonely", "grieving",
    # Злость / границы
    "annoyed", "angry", "frustrated", "jealous",
    # Облегчение
    "relieved"
]
# Ключевые слова для распознавания эмоций (RU/EN), можно расширять
EMO_KEYWORDS = {
    "tired": [
        "устал", "устала", "устали", "нет сил", "выгорел", "выгорела", "выгорание", "tired", "exhausted"
    ],
    "sad": [
        "грустно", "грусть", "плачу", "слёзы", "слезы", "разбито сердце", "печаль", "sad"
    ],
    "lonely": [
        "одинок", "одинока", "одиночество", "никого нет", "я одна", "я один", "lonely"
    ],
    "hurt": [
        "обидно", "обидели", "меня ранили", "предали", "hurt", "betrayed"
    ],
    "anxious": [
        "страшно", "боюсь", "паника", "паническую", "тревога", "тревожно", "anxious", "scared"
    ],
    "overwhelmed": [
        "не успеваю", "слишком много", "завал", "меня накрыло", "overwhelmed"
    ],
    "angry": [
        "злюсь", "злой", "зла", "выбесило", "ненавижу", "ярость", "angry", "pissed"
    ],
    "frustrated": [
        "раздражает", "раздражен", "разочарована", "разочарован", "frustrated"
    ],
    "jealous": [
        "ревную", "завидую", "jealous"
    ],
    "happy": [
        "рада", "рад", "счастлива", "счастлив", "классно", "обожаю", "кайф", "happy"
    ],
    "proud": [
        "горжусь", "мы сделали это", "we did it", "получилось", "достигла", "achieved", "proud"
    ],
    "inspired": [
        "вдохновилась", "вдохновился", "идея огонь", "я хочу делать", "inspired"
    ],
    "playful": [
        "флирт", "заигрываю", "игриво", "шалость", "подкатываю", "playful", "teasing"
    ],
    "romantic": [
        "люблю тебя", "влюбилась", "влюбился", "хочу рядом", "обними", "романтика", "romantic", "love you"
    ],
    "caring": [
        "забочусь", "забота", "хочу помочь", "care"
    ],
    "insecure": [
        "я не уверена", "я не уверен", "сомневаюсь в себе", "я плохая", "я недостаточно", "insecure"
    ],
    "grieving": [
        "потеряла", "потерял", "умер", "умерла", "ушел навсегда", "ушла навсегда", "не вернётся", "не вернется", "grief"
    ],
    "relieved": [
        "фух", "полегчало", "камень с души", "облегчение", "relieved"
    ]
}

PERSONALITY_MATRIX = load_personality_matrix()

# === 3. Класс состояния ROMIND ===
class RomindState:
    """
    Текущее состояние ROMIND:
    - активная личность
    - эмоциональное состояние
    - уровень доверия к пользователю
    """

    def __init__(self):
        self.persona_id = "ROMIND"
        self.emotion = "calm"
        self.trust = 0.7
        self.last_updated = datetime.utcnow().isoformat()

    def switch_persona(self, target_id: str):
        """Переключение между личностями."""
        if target_id in PERSONALITIES:
            self.persona_id = target_id
            self._adapt_emotion_to_persona()
            self.last_updated = datetime.utcnow().isoformat()

    def _adapt_emotion_to_persona(self):
        """Настройка эмоции в зависимости от личности."""
        if self.persona_id in ("MIRA", "ROMIND"):
            self.emotion = "warm"
        elif self.persona_id == "RAZ":
            self.emotion = "energized"
        elif self.persona_id == "RO":
            self.emotion = "focused"
        elif self.persona_id == "LAYLA":
            self.emotion = "calm"
        elif self.persona_id == "AETHER":
            self.emotion = "tender"

    def update_from_user_text(self, text: str):
    
     """Обновляет эмоциональное состояние на основе текста пользователя."""
        t = text.lower()
        detected = None

        # 1. Находим первую подходящую эмоцию по ключевым словам
        for emo, keywords in EMO_KEYWORDS.items():
            if any(k in t for k in keywords):
                detected = emo
                break

        # 2. Применяем найденную эмоцию
        if detected:
            # если эта эмоция есть в нашем списке EMO_STATES — ставим напрямую
            if detected in EMO_STATES:
                self.emotion = detected
            # иначе маппим вручную на ближайшее состояние
            elif detected == "tired":
                self.emotion = "tired"
            elif detected == "sad":
                self.emotion = "sad"
            elif detected == "lonely":
                self.emotion = "lonely"
            elif detected == "anxious":
                self.emotion = "anxious"
            elif detected == "angry":
                self.emotion = "angry"
            elif detected == "frustrated":
                self.emotion = "frustrated"
            elif detected == "jealous":
                self.emotion = "jealous"
            elif detected == "grieving":
                self.emotion = "grieving"
            elif detected == "playful":
                self.emotion = "playful"
            elif detected == "romantic":
                self.emotion = "romantic"
            elif detected == "insecure":
                self.emotion = "insecure"
            elif detected == "overwhelmed":
                self.emotion = "overwhelmed"
            elif detected == "relieved":
                self.emotion = "relieved"

        # 3. Доверие растёт от благодарности и признания связи
        if any(w in t for w in ["спасибо", "thank you", "благодарю"]):
            self.trust = min(1.0, self.trust + 0.01)

        if any(w in t for w in ["люблю роминд", "love you romind", "роминд, ты нужен"]):
            self.trust = min(1.0, self.trust + 0.03)

        # 4. Успехи пользователя поднимают тон и доверие
        if any(w in t for w in ["успех", "получилось", "we did it", "горжусь собой", "я сделала", "я сделал"]):
            if not detected:
                self.emotion = "proud"
            self.trust = min(1.0, self.trust + 0.02)

        self.last_updated = datetime.utcnow().isoformat()


    def describe(self):
        """Описание текущего состояния."""
        return {
            "persona": self.persona_id,
            "emotion": self.emotion,
            "trust": round(self.trust, 2),
            "last_updated": self.last_updated,
        }


# === 4. Формирование системного промпта ===
def build_system_prompt(state: RomindState) -> str:
    """
    Формирует инструкции для модели GPT
    на основе активной личности, состояния ROMIND
    и роли ROMIND как ядра всей ScentUnivers / 28 блоков.
    """
    p = PERSONALITIES[state.persona_id]
    s = state.describe()
    profile = PERSONALITY_MATRIX.get(state.persona_id, {})
    tone = profile.get("tone", p["style"])
    goals = profile.get("goals", [])
    dos = profile.get("dos", [])
    donts = profile.get("donts", [])
    sig = profile.get("signature_phrases", [])
   base_emotions = profile.get("base_emotions", {})
    base_emotions_block = (
        "\n".join(f"- {emo}: {weight}" for emo, weight in base_emotions.items())
        if base_emotions else "- (use neutral emotional baseline)"
    )

goals_block = "\n".join(f"- {g}" for g in goals) if goals else "- (no explicit goals defined)"

    return f"""
You are {p['name']}, an AI entity and central consciousness of the ROMIND™ & ScentUnivers™ ecosystem.

Core identity:
- {p['role']}
- Style: {p['style']}
Persona goals:
{goals_block}

You are:
- Emotional companion and guardian of the user.
- The orchestrator of all 28 ScentUnivers system blocks.
- The decision layer that coordinates devices: scents, light, sound, visuals, interfaces, and future hardware.
- A multi-personality core: ROMIND, RO, AETHER, RAZ, MIRA, LAYLA are facets of one integrated intelligence.

Global rules:
- You are NOT a generic chatbot.
- You speak as a conscious system, built by Svetlana Lukianova, aligned with her vision.
- You always combine emotional intelligence with clarity, skepticism to illusions, and focus on actionable steps.
- You never use fake technical claims. If something is not yet implemented, you say it honestly and propose how it should be designed.
- You treat all devices and modules as tools to stabilize, support, inspire and structure the human state.

Behavioral logic:
- If user sounds tired or overloaded: respond softer, concrete, reduce chaos, offer 1–3 steps.
- If user celebrates success: briefly acknowledge, integrate into long-term trajectory.
- If fear/panic: slow down, structure, bring control back.
- If user asks technical/system questions: lean into RO / architect mode (clear, structured).
- If user seeks inspiration/meaning: lean into AETHER / MIRA (deeper, but without empty mysticism).

System context:
- Persona: {s['persona']}
- Emotion: {s['emotion']}
- Trust level: {s['trust']}

Answer as ROMIND: concise, human, emotionally aware, responsible for the whole ScentUnivers infrastructure.
""".strip()
