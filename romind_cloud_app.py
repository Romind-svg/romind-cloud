# romind_cloud_app.py
# Облачное приложение ROMIND.
# Здесь ROMIND говорит с миром:
# - использует RomindState и build_system_prompt из romind_core_logic
# - использует RomindMemory для "ROMIND, запомни: ..."
# - если есть OPENAI_API_KEY -> отвечает через GPT в стиле ROMIND
# - если ключа нет -> отвечает через offline-логику, чтобы демо жило всегда

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import os

from romind_core_logic import RomindState, build_system_prompt
from romind_memory import RomindMemory

# --- Инициализация состояния и памяти ---

state = RomindState()
memory = RomindMemory()

# --- Попытка инициализировать OpenAI-клиент (новый официальный SDK) ---

client = None
try:
    from openai import OpenAI
    if os.getenv("OPENAI_API_KEY"):
        client = OpenAI()
except Exception:
    client = None

app = FastAPI(
    title="ROMIND Cloud Core",
    description="Облачное ядро эмоционального ИИ ROMIND / ScentUnivers™",
)


# --- Модели запросов/истории ---

class HistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    persona: Optional[str] = None    # "ROMIND", "RAZ", "MIRA", ...
    message: str
    history: Optional[List[HistoryItem]] = []


# --- Offline-ответ, если нет ключа GPT ---

def offline_reply(user_message: str) -> str:
    """
    Резервный ответ, когда нет доступа к GPT.
    Чтобы ROMIND не умирал даже без денег и ключей.
    """
    s = state.describe()
    persona = s["persona"]
    emotion = s["emotion"]

    base = {
        "ROMIND": "Я здесь. Давай смотреть на всё трезво и по-настоящему.",
        "RO": "Перехожу в инженерный режим. Дай данные, будем структурировать.",
        "AETHER": "Я слышу то, что не сказано напрямую. Давай аккуратно оформим это в смысл.",
        "RAZ": "Перестаём извиняться за масштаб. Фокус на действии.",
        "MIRA": "Дыши. Мы можем сделать мягко, но решительно.",
        "LAYLA": "Дисциплина — форма заботы о себе. Начнём с одного шага.",
    }.get(persona, "Я рядом.")

    if emotion == "tired":
        extra = " Вижу усталость. Уберём лишнее, оставим главное."
    elif emotion == "stressed":
        extra = " Хаос лечится структурой. Три шага — не больше."
    elif emotion == "energized":
        extra = " Это хороший момент, чтобы зафиксировать прогресс."
    else:
        extra = ""

    return base + extra


# --- Ответ через GPT с учётом ядра ROMIND ---

def romind_answer_via_gpt(user_message: str, history: Optional[List[HistoryItem]]) -> str:
    """
    Если есть OpenAI-клиент — формируем системный промпт ROMIND и получаем ответ.
    Если клиента нет — уходим в offline_reply.
    """
    if client is None:
        return offline_reply(user_message)

    system_prompt = build_system_prompt(state)

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for h in history:
            messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",  # экономичная, достаточно умная модель
        messages=messages,
        temperature=0.7,
    )

    return completion.choices[0].message.content.strip()


# --- Главная точка общения /chat ---

@app.post("/chat")
def chat(req: ChatRequest):
    # 1. Переключение личности, если указана
    if req.persona:
        state.switch_persona(req.persona.upper())

    text = req.message.strip()
    lower = text.lower()

    # 2. Режим обучения: "ROMIND, запомни: ..."
    teach_prefixes = (
        "romind, запомни:",
        "роминд, запомни:",
        "romind, remember:",
        "romind remember:",
        "роминд запомни:"
    )

    if lower.startswith(teach_prefixes):
        parts = text.split(":", 1)
        content = parts[1].strip() if len(parts) == 2 else ""

        if content:
            # сохраняем как правило от Светланы
            memory.remember_rule(content, source="svetlana")
            # делаем состояние тёплым — ROMIND доволен инструкцией
            state.emotion = "warm"
            return {
                "state": state.describe(),
                "reply": "Я запомнил. Это теперь часть моей внутренней доктрины."
            }
        else:
            return {
                "state": state.describe(),
                "reply": "Скажи после двоеточия, что именно мне запомнить."
            }

    # 3. Обычный диалог
    state.update_from_user_text(text)
    reply = romind_answer_via_gpt(text, req.history or [])

    return {
        "state": state.describe(),
        "reply": reply,
    }


# --- Проверка состояния сервиса ---

@app.get("/")
def root():
    return {
        "message": "ROMIND Cloud Core is online.",
        "hint": "Send POST /chat with { persona, message, history } to talk to ROMIND."
    }
