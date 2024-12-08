import psycopg2 
from telegram import Update 
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
# Подключение к базе данных
def connect_to_db():
    return psycopg2.connect(
        dbname="railway",
        user="postgres",
        password="",
        host="junction.proxy.rlwy.net",
        port="15353"
    )
# Команда /start
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username

# Сохранение пользователя в базу данных    
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
                        INSERT INTO users (user_id, username)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id) DO NOTHING
                        """, (user_id, username))
        conn.commit()
    finally:
            cursor.close()
            conn.close()
    update.message.reply_text("Привет! Добро пожаловать в SQL Бот. Используй /task для получения задания.")
# Команда /task
def task(update: Update, context: CallbackContext):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, question FROM tasks ORDER BY RANDOM() LIMIT 1")
        task = cursor.fetchone()
        if task:
            context.user_data["current_task_id"] = task[0]
            update.message.reply_text(f"Задание: {task[1]}")
        else:
            update.message.reply_text("Нет доступных заданий. Попробуйте позже.")
    finally:
        cursor.close()
        conn.close()
# Проверка ответа пользователя
def check(update: Update, context: CallbackContext):
    user_query = update.message.text.strip()
    task_id = context.user_data.get("current_task_id")

    if not task_id:
        update.message.reply_text("Сначала получите задание с помощью команды /task.")
        return
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT correct_query FROM tasks WHERE id = %s", (task_id,))
        correct_query = cursor.fetchone()
        if correct_query and user_query.lower() == correct_query[0].lower():
            update.message.reply_text("Правильно! Молодец.")
        # Обновляем статистику пользователя            
            cursor.execute("""
                       UPDATE users
                       SET completed_tasks = completed_tasks + 1
                       WHERE user_id = %s
                       """, (update.effective_user.id,))
            conn.commit()
        else:
            update.message.reply_text("Неправильно. Попробуйте еще раз.")
    finally:
        cursor.close()
        conn.close()

# Основной код
def main():
    # Инициализация бота    
    updater = Updater("")
    dispatcher = updater.dispatcher
# Обработчики команд    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("task", task))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check))
# Запуск бота    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
