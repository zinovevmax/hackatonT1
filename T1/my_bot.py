import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import asyncpg

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для подключения к базе данных


async def connect_to_db():
    return await asyncpg.connect(user='your_username', password='your_password',
                                 database='your_database', host='localhost')

# Функция для обработки команды /start


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправь мне текст, и я запишу его в файл. Используй /read чтобы прочитать содержимое другого файла.')

# Функция для записи текста в файл


async def write_to_file(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text
    with open('output.txt', 'a', encoding='utf-8') as file:  # Указываем кодировку UTF-8
        file.write(user_text + '\n')
    await update.message.reply_text('Текст записан в output.txt!')

# Функция для чтения текста из другого файла


async def read_from_file(update: Update, context: CallbackContext) -> None:
    try:
        with open('read_output.txt', 'r', encoding='utf-8') as file:  # Указываем кодировку UTF-8
            content = file.read()
            await update.message.reply_text(f'Содержимое файла read_output.txt:\n{content}')
    except FileNotFoundError:
        await update.message.reply_text('Файл read_output.txt пока пуст или не существует.')

# Функция для добавления карты


async def add_card(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Введите данные карты в формате: Название, Банк, Лимит, Бонусные категории (через запятую)")

# Функция для обработки данных карты


async def process_card_data(update: Update, context: CallbackContext) -> None:
    data = update.message.text.split(',')
    card_name, bank_name, credit_limit, bonus_categories = data

    # Сохранение карты в базу данных
    conn = await connect_to_db()
    await conn.execute('''
        INSERT INTO cards (card_name, bank_name, credit_limit, bonus_categories)
        VALUES ($1, $2, $3, $4)
    ''', card_name, bank_name, float(credit_limit), bonus_categories)
    await conn.close()

    await update.message.reply_text("Карта успешно добавлена!")

# Функция для получения рекомендаций


async def recommend_card(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Введите категорию покупки и сумму (например, 'Рестораны 5000')")

# Функция для обработки запроса на рекомендации


async def process_purchase(update: Update, context: CallbackContext) -> None:
    category, amount = update.message.text.split()
    amount = float(amount)

    # Получение рекомендаций
    conn = await connect_to_db()
    user_id = update.message.from_user.id
    preferences = await conn.fetchval('SELECT preferences FROM users WHERE user_id = $1', user_id)
    user_cards = await conn.fetch('''
        SELECT c.card_id, c.card_name, c.bank_name, c.bonus_categories, uc.custom_limit
        FROM user_cards uc
        JOIN cards c ON uc.card_id = c.card_id
        WHERE uc.user_id = $1
    ''', user_id)

    recommendations = []
    for card in user_cards:
        if category in card['bonus_categories'] and card['custom_limit'] >= amount:
            recommendations.append(card)

    recommendations.sort(
        key=lambda x: x['bonus_categories'][category], reverse=True)
    top_recommendations = recommendations[:3]

    if top_recommendations:
        response = "Рекомендуемые карты:\n"
        for card in top_recommendations:
            response += f"{card['card_name']} ({card['bank_name']}) - Бонус: {card['bonus_categories'][category]}%\n"
    else:
        response = "Нет подходящих карт для этой покупки."

    await update.message.reply_text(response)
    await conn.close()

# Функция для обновления лимита карты


async def update_limit(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Введите ID карты и новый лимит (например, '1 50000')")

# Функция для обработки обновления лимита


async def process_limit_update(update: Update, context: CallbackContext) -> None:
    card_id, new_limit = update.message.text.split()
    card_id = int(card_id)
    new_limit = float(new_limit)

    # Обновление лимита в базе данных
    conn = await connect_to_db()
    await conn.execute('''
        UPDATE user_cards
        SET custom_limit = $1
        WHERE card_id = $2 AND user_id = $3
    ''', new_limit, card_id, update.message.from_user.id)
    await conn.close()

    await update.message.reply_text("Лимит успешно обновлен!")

# Функция для обработки ошибок


async def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update {update} caused error {context.error}')


def main() -> None:
    # Вставьте сюда ваш токен
    token = '8085408092:AAFMeZvMge7GvFA2VJd-ycFwfQFdqU-DJ04'

    # Создаем Application и передаем ему токен вашего бота
    application = Application.builder().token(token).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("read", read_from_file))
    application.add_handler(CommandHandler("add_card", add_card))
    application.add_handler(CommandHandler("recommend", recommend_card))
    application.add_handler(CommandHandler("update_limit", update_limit))

    # Регистрируем обработчики текстовых сообщений
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, write_to_file))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, process_card_data))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, process_purchase))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, process_limit_update))

    # Регистрируем обработчик ошибок
    application.add_error_handler(error)

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()
