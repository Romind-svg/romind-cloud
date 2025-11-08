# romind_cloud_app.py
# Тест запуска ROMIND Cloud Core — проверка подключения матрицы личностей

from romind_core_logic import PERSONALITY_MATRIX

def test_personality_matrix():
    """Проверка, что JSON загружен и данные доступны."""
    print("=== ROMIND Personality Matrix Test ===")

    if not PERSONALITY_MATRIX:
        print("⚠️ Матрица не загружена. Проверь файл romind_personality_matrix.json.")
        return

    print(f"Всего личностей: {len(PERSONALITY_MATRIX)}")
    print("\nДоступные личности:", ", ".join(PERSONALITY_MATRIX.keys()))

    # Берём одну личность для примера
    persona = PERSONALITY_MATRIX.get("AETHER", {})
    if persona:
        print("\n=== Пример: AETHER ===")
        print(f"Тон: {persona.get('tone', '—')}")
        print("Цели:")
        for goal in persona.get("goals", []):
            print(" •", goal)
        print("\nКлючевые фразы:")
        for phrase in persona.get("signature_phrases", []):
            print(" •", phrase)
    else:
        print("⚠️ Личность AETHER не найдена в матрице.")

if __name__ == "__main__":
    test_personality_matrix()
