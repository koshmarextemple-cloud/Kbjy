import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from openai import OpenAI

# Инициализация логов и токенов
logging.basicConfig(level=logging.INFO)

# Сюда вставляются ключи (ниже написано, где их взять)
TELEGRAM_TOKEN = "8873107248:AAEWF9M8rSut5IJYEdKay5BxWyVaqzb7NV8"
OPENAI_API_KEY = "sk-QVhpkcBBLmEtN0SYRz7gLzSOAkETdErt"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# Инструкция для ИИ, как именно обрабатывать еду
SYSTEM_PROMPT = (
    "Ты — профессиональный ИИ-нутрициолог и фитнес-тренер. Твоя задача — "
    "распознать продукты из текста или аудио, определить их примерный вес и "
    "выдать четкий ответ строго по форме:\n"
    "🍏 Продукт | Вес | Ккал | Б | Ж | У\n"
    "В конце обязательно выведи ИТОГО за этот прием пищи. "
    "Будь краток, не пиши лишней воды, только цифры и факты. Если цель пользователя — сушка, "
    "сделай акцент на белке."
)

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "Привет! Я твой ИИ-помощник по КБЖУ. 🎯\n\n"
        "Просто надиктуй мне голосом или напиши текстом, что ты съел "
        "(например: 'две куриные котлеты на пару и 150г гречки').\n"
        "Я мгновенно посчитаю калории и макронутриенты!"
    )

@dp.message()
async def handle_food_message(message: Message):
    user_text = ""

    # Если пользователь прислал голосовое сообщение
    if message.voice:
        await message.answer("🎙 Расшифровываю твой голос, секунду...")
        
        # Скачиваем аудиофайл
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        await bot.download_file(file_path, "voice.ogg")
        
        # Отправляем аудио в OpenAI Whisper для перевода в текст
        with open("voice.ogg", "rb") as audio_file:
            transcript = ai_client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        user_text = transcript.text
        await message.answer(Text=f"📋 Распознал: *{user_text}*", parse_mode="Markdown")
    
    # Если пользователь написал текстом
    elif message.text:
        user_text = message.text

    if not user_text:
        await message.answer("Я понимаю только текст или голосовые сообщения.")
        return

    # Отправляем текст в GPT для анализа КБЖУ
    await message.answer("🔄 Считаю КБЖУ...")
    
    response = ai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    
    ai_answer = response.choices[0].message.content
    await message.answer(ai_answer)

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
