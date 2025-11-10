# romind_cloud_app.py
# Облачное приложение ROMIND.
# - Общается через HTTP (FastAPI)
# - Использует RomindState + build_system_prompt как "мозг"
# - Использует RomindSemanticMemory для памяти и анализа
# - Если есть OPENAI_API_KEY -> отвечает через GPT в стиле ROMIND
# - Если ключа нет -> отвечает через offline-логику (демо живёт всегда)
# - Внизу есть консольный режим для локального теста

import os
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from romind_core_logic import (
    RomindState,
    build_system_prompt,
    build_adaptive_reply,
    get_proximity_level,
    adapt_response_to_proximity,
)
from romind_memory import RomindSemanticMemory

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

    if emotion in ("tired", "drained", "overwhelmed"):
        extra = " Ты устала — убираем лишнее, оставляем главное."
    elif emotion in ("anxious", "worried"):
        extra = " В хаосе спасает структура. Давай 1–3 шага."
    elif emotion in ("happy", "joyful", "inspired"):
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

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",  # экономичная модель для демо
            messages=messages,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content.strip()
    except Exception:
        reply = offline_reply(user_message)

    return reply


# --- Внутренняя обработка сообщения (общая для API и консоли) ---

def process_user_message(user_text: str, use_gpt: bool = True) -> str:
    """
    Полный цикл:
    - обновить состояние
    - записать память
    - обновить биографию и семантику
    - сгенерировать адаптивный ответ
    """
    # 1. Обновляем состояние по тексту
    state.update_from_user_text(user_text)

    # 2. Логируем взаимодействие в память
    try:
        memory.remember(
            user_text=user_text,
            persona_id=state.persona_id,
            role_context=state.role_context,
            emotion=state.emotion,
            trust=state.trust,
        )
    except Exception:
        pass

    # 3. Обновляем биографический профиль
    try:
        memory.update_profile(user_text)
    except Exception:
        pass

    # 4. Обновляем семантические паттерны
    try:
        memory.update_semantic_patterns(user_text, state.emotion)
    except Exception:
        pass

    # 5. Если есть GPT и включен use_gpt — пробуем онлайн-ответ
    if use_gpt:
        base_reply = romind_answer_via_gpt(user_text, history=None)
    else:
        base_reply = offline_reply(user_text)

    # 6. Адаптация под круг близости и роль
    role = state.role_context
    proximity = get_proximity_level(state.trust, role)
    adapted = adapt_response_to_proximity(base_reply, proximity, role)

    # 7. Дополнительный слой: высокоуровневая адаптация (интро + память)
    final_reply = build_adaptive_reply(
        user_text=user_text,
        state=state,
        memory=memory,
    )

    # Если build_adaptive_reply что-то даёт — используем его, иначе adapted
    return final_reply or adapted


# --- Основной endpoint /chat ---

@app.post("/chat")
def chat(req: ChatRequest):
    # 1. Переключение личности, если указана
    if req.persona:
        state.switch_persona(req.persona.upper())

    text = (req.message or "").strip()
    lower = text.lower()

    if not text:
        return {
            "state": state.describe(),
            "reply": "Скажи мне что-нибудь, и я отвечу."
        }

    # 2. Режим явного обучения: "ROMIND, запомни: ..."
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
            # Запишем как системное правило в память
            try:
                memory.remember(
                    user_text=f"SYSTEM_RULE: {content}",
                    persona_id=state.persona_id,
                    role_context=state.role_context,
                    emotion=state.emotion,
                    trust=state.trust,
                )
            except Exception:
                pass

            try:
                memory.update_semantic_patterns(content, state.emotion)
            except Exception:
                pass

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

    # 3. Обычный диалог через GPT (если есть) или оффлайн
    # (история из req.history может быть добавлена к GPT, если нужно)
    state.update_from_user_text(text)

    # Логируем
    try:
        memory.remember(
            user_text=text,
            persona_id=state.persona_id,
            role_context=state.role_context,
            emotion=state.emotion,
            trust=state.trust,
        )
        memory.update_profile(text)
        memory.update_semantic_patterns(text, state.emotion)
    except Exception:
        pass

    reply = romind_answer_via_gpt(text, req.history or [])

    # Адаптация под близость
    role = state.role_context
    proximity = get_proximity_level(state.trust, role)
    reply = adapt_response_to_proximity(reply, proximity, role)

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


# --- Консольный тест (локальный режим) ---

if __name__ == "__main__":
    print("=== ROMIND Adaptive Dialogue Test ===")
    print("ROMIND онлайн. Напиши что-нибудь. ('выход' чтобы завершить)")
    while True:
        try:
            user_text = input("\nТы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nROMIND: Я рядом. Возвращайся, когда захочешь. 🌙")
            break

        if not user_text:
            continue

        if user_text.lower() in ("выход", "exit", "quit"):
            print("ROMIND: До встречи. Я буду ждать.")
            break

        response = process_user_message(user_text, use_gpt=False)
        print(f"ROMIND: {response}")
