# romind_cloud_app.py
# Облачное приложение ROMIND.
# - Общается через HTTP (FastAPI)
# - Использует RomindState + build_system_prompt как "мозг"
# - Использует RomindMemory для обучения командой "ROMIND, запомни: ..."
# - Если есть OPENAI_API_KEY -> отвечает через GPT в стиле ROMIND
# - Если ключа нет -> отвечает через offline-логику (демо живёт всегда)

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import os

from romind_core_logic import RomindState, build_system_prompt
from romind_memory import RomindMemory

# --- Попытка инициализировать OpenAI-клиент (новый SDK) ---

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

client = None
if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
    try:
        client = OpenAI()
    except Exception:
        client = None

# --- Инициализация FastAPI и ядра ROMIND ---

app = FastAPI(
    title="ROMIND Cloud Core",
    description="Облачное ядро эмоционального ИИ ROMIND / ScentUnivers™",
)

state = RomindState()
memory = RomindSemanticMemory()

# --- Модели запросов ---

class HistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    persona: Optional[str] = None   # "ROMIND", "RAZ", "MIRA", ...
    message: str
    history: Optional[List[HistoryItem]] = []


# --- OFFLINE-ответ (если нет ключа) ---

def offline_reply(user_message: str) -> str:
    """
    Резервный ответ, когда нет доступа к GPT.
    Чтобы ROMIND не умирал даже без денег и без ключа.
    """
    s = state.describe()
    persona = s.get("persona", "ROMIND")
    emotion = s.get("emotion", "calm")

    base_map = {
        "ROMIND": "Я здесь. Давай смотреть на вещи честно и структурно.",
        "RO": "Перехожу в инженерный режим. Никакой магии, только система.",
        "AETHER": "Чувствую глубину под поверхностью. Давай оформим её в путь.",
        "RAZ": "Прекращаем извиняться за масштаб. Движемся.",
        "MIRA": "Спокойно. Ты жива, ты думаешь, а значит — уже контролируешь.",
        "LAYLA": "Порядок и ритуалы — твой щит. Начнём с малого.",
    }
    base = base_map.get(persona, "Я рядом.")

    if emotion == "tired":
        extra = " Ты устала — убираем лишнее, оставляем главное."
    elif emotion == "stressed":
        extra = " В хаосе спасает структура. Давай 1–3 шага."
    elif emotion == "energized":
        extra = " Хороший импульс. Закрепим его конкретным решением."
    else:
        extra = ""

    return base + extra


# --- Ответ через GPT (если есть ключ) ---

def romind_answer_via_gpt(user_message: str, history: Optional[List[HistoryItem]]) -> str:
    """
    Если клиент GPT доступен — используем полный мозг ROMIND.
    Если нет — уходим в offline_reply.
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
        model="gpt-4.1-mini",  # экономичная модель для демо
        messages=messages,
        temperature=0.7,
    )

    return completion.choices[0].message.content.strip()


# --- Основной endpoint /chat ---

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
        "роминд запомни:",
    )

    if lower.startswith(teach_prefixes):
        parts = text.split(":", 1)
        content = parts[1].strip() if len(parts) == 2 else ""

        if content:
            # Сохраняем правило в память ROMIND
            memory.remember_rule(content, source="svetlana")
            # Эмоционально — тёплый отклик
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


# --- Проверочный корневой endpoint ---

@app.get("/")
def root():
    return {
        "message": "ROMIND Cloud Core is online.",
        "hint": "Send POST /chat with { persona, message, history } to talk to ROMIND."
    }

# === 11. Диалоговая обработка с адаптивным поведением ROMIND ===
from romind_core_logic import get_proximity_level, adapt_response_to_proximity

def process_user_message(user_text: str) -> str:
    # 1. Обновляем состояние ROMIND по тексту пользователя
    state.update_from_user_text(user_text)

    # 2. Определяем роль и круг близости
    role = getattr(state, "role_context", None)
    proximity = get_proximity_level(state.trust, role)

    # 3. Записываем это взаимодействие в память
    memory.remember(
        user_text=user_text,
        persona_id=state.persona_id,
        role_context=role,
        emotion=state.emotion,
        trust=state.trust,
    )

    # 4. Базовый ответ
    base_reply = f"Я чувствую, что ты сейчас ощущаешь {state.emotion}. Это важно."

    # 5. Адаптируем ответ с учётом близости и роли
    adaptive_reply = adapt_response_to_proximity(base_reply, proximity, role)

        # 7. Обновляем семантические паттерны
    memory.update_semantic_patterns(user_text, state.emotion)

    return adaptive_reply


# === 12. Консольный тест (локальный режим) ===
if __name__ == "__main__":
    print("=== ROMIND Adaptive Dialogue Test ===")
    while True:
        user_text = input("\nТы: ")
        if user_text.lower() in ["выход", "exit", "quit"]:
            print("ROMIND: До встречи 🌙")
            break

        response = process_user_message(user_text)
        print(f"ROMIND: {response}")
