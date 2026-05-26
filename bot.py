# --- bot.py ---

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import BOT_TOKEN, MANAGER_ID, MANAGER_PHONE, MANAGER_USERNAME, SHEET_NAME
from datetime import datetime

# --- Telegram bot ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# --- Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# --- FSM состояния ---
class OrderState(StatesGroup):
    client_type = State()
    city_or_area = State()
    full_address = State()
    bottles = State()
    phone = State()
    comment = State()
    confirm = State()
    edit_choice = State()
    edit_bottles_needed = State()
    edit_phone = State()
    edit_comment = State()
    edit_address = State()
    edit_full_address = State()
    repeat_choice = State()
    assign_delivery_date = State()

# --- Клавиатуры ---
def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Заказать воду")
    keyboard.add("Цены")
    keyboard.add("🔄 Начать заново")
    return keyboard

def reset_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🔄 Начать заново")
    return keyboard

# --- Старт ---
@dp.message_handler(commands=["start"], state="*")
@dp.message_handler(lambda msg: msg.text == "🔄 Начать заново", state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Привет! 👋 Я бот доставки воды «Лесной Источник».",
        reply_markup=main_keyboard()
    )

# --- Цены ---
@dp.message_handler(lambda msg: msg.text == "Цены", state="*")
async def show_prices(message: types.Message, state: FSMContext):
    text = (
        "💧 <b>Актуальные цены на доставку:</b>\n\n"
        "📍 <b>Дмитров</b> и <b>Яхрома</b>:\n"
        "• 1 бутылка — 290 руб\n"
        "• От 2 бутылок — 270 руб/бутылка\n\n"
        "📦 <b>Дмитровский район</b>:\n"
        "• Доставка только от 5 бутылок — 330 руб/бутылка\n\n"
        "⚠️ <b>Обратите внимание:</b> при первом заказе также оплачивается "
        "<b>залоговая стоимость за тару — 250 руб за одну бутылку.</b>"
    )
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Заказать воду")
    keyboard.add("🔄 Начать заново")
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

# --- Заказать воду ---
@dp.message_handler(lambda msg: msg.text == "Заказать воду", state="*")
async def choose_client_type(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Новый клиент", "Постоянный клиент")
    keyboard.add("🔄 Начать заново")
    await message.answer("Вы новый или постоянный клиент?", reply_markup=keyboard)
    await OrderState.client_type.set()

# --- Выбор клиента и города/района ---
@dp.message_handler(state=OrderState.client_type)
async def get_client_type(message: types.Message, state: FSMContext):
    client_type = message.text
    await state.update_data(client_type=client_type)

    if client_type == "Постоянный клиент":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("🔁 Повторить прошлый заказ", "🆕 Создать новый заказ")
        keyboard.add("🔄 Начать заново")
        await message.answer("Что вы хотите сделать?", reply_markup=keyboard)
        await OrderState.repeat_choice.set()
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Дмитров/Яхрома", "Дмитровский район")
        keyboard.add("🔄 Начать заново")
        await message.answer("Выберите город доставки:", reply_markup=keyboard)
        await OrderState.city_or_area.set()

@dp.message_handler(state=OrderState.repeat_choice)
async def handle_repeat_choice(message: types.Message, state: FSMContext):
    choice = message.text
    user_id = str(message.from_user.id)

    if choice == "🔁 Повторить прошлый заказ":
        records = sheet.get_all_values()
        last_order = None
        for row in reversed(records):
            if len(row) >= 11 and row[10] == user_id:
                last_order = row
                break

        if not last_order:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("🆕 Создать новый заказ", "🔄 Начать заново")
            await message.answer(
                "У вас ещё не было заказов 💧\nХотите создать новый заказ?",
                reply_markup=keyboard
            )
            return

        client_type = "Постоянный клиент"
        address = last_order[2]
        bottles = last_order[3]
        price = last_order[4]
        total = last_order[5]
        phone = last_order[6]
        comment = last_order[7]

        await state.update_data(
            client_type=client_type,
            full_address=address,
            bottles=bottles,
            price=price,
            total=total,
            phone=phone,
            comment=comment,
        )

        text = (
            f"🔁 <b>Ваш прошлый заказ:</b>\n\n"
            f"Адрес: {address}\n"
            f"Количество бутылок: {bottles}\n"
            f"Цена за бутыль: {price} руб\n"
            f"<b>Итоговая сумма:</b> {total} руб\n"
            f"Телефон: {phone}\n"
            f"Комментарий: {comment}\n\n"
            f"Повторяем заказ?"
        )

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("✅ Всё верно", "✏️ Изменить данные")
        keyboard.add("🔄 Начать заново")
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        await OrderState.confirm.set()

# --- Ввод города/района ---
@dp.message_handler(state=OrderState.city_or_area)
async def get_city(message: types.Message, state: FSMContext):
    city_or_area = message.text
    await state.update_data(city_or_area=city_or_area)
    await message.answer(
        "Введите полный адрес доставки (город, село, деревня, СНТ, улица, дом и т.д.):",
        reply_markup=reset_keyboard()
    )
    await OrderState.full_address.set()

# --- Ввод полного адреса ---
@dp.message_handler(state=OrderState.full_address)
async def get_full_address(message: types.Message, state: FSMContext):
    await state.update_data(full_address=message.text)
    data = await state.get_data()
    city_or_area = data.get("city_or_area", "").lower()
    bottles = data.get("bottles", 0)

    if "дмитровский район" in city_or_area and bottles < 5:
        await message.answer(
            "Уважаемый клиент, по Дмитровскому району доставка только от 5 бутылок.\n"
            "Введите количество ≥ 5:",
            reply_markup=reset_keyboard()
        )
        await OrderState.bottles.set()
    else:
        await message.answer("Сколько бутылей вы хотите заказать?", reply_markup=reset_keyboard())
        await OrderState.bottles.set()

# --- Количество бутылей ---
@dp.message_handler(state=OrderState.bottles)
async def get_bottles(message: types.Message, state: FSMContext):
    data = await state.get_data()
    city_or_area = data.get("city_or_area", "").lower()
    try:
        bottles = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.", reply_markup=reset_keyboard())
        return

    if "дмитровский район" in city_or_area and bottles < 5:
        await message.answer(
            "Уважаемый клиент, по Дмитровскому району доставка только от 5 бутылок.\n"
            "Введите количество ≥ 5 или начните заново.",
            reply_markup=reset_keyboard()
        )
        return

    await state.update_data(bottles=bottles)
    await message.answer("Введите номер телефона:", reply_markup=reset_keyboard())
    await OrderState.phone.set()

# --- Телефон ---
@dp.message_handler(state=OrderState.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Добавьте комментарий (или напишите 'Нет'):", reply_markup=reset_keyboard())
    await OrderState.comment.set()

# --- Комментарий ---
@dp.message_handler(state=OrderState.comment)
async def get_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_order_check(message, state)

# --- Проверка заказа ---
async def show_order_check(message: types.Message, state: FSMContext):
    data = await state.get_data()
    city_or_area = data.get("city_or_area", "").lower()
    bottles = int(data.get("bottles", 0) or 0)
    full_address = data.get("full_address", "не указан")
    client_type = data.get("client_type", "")

    if "дмитровский район" in city_or_area:
        price = 330
    else:
        price = 290 if bottles == 1 else 270

    deposit_per_bottle = 250
    deposit = deposit_per_bottle * bottles if client_type == "Новый клиент" else 0
    total = bottles * price + deposit

    await state.update_data(price=price, total=total, deposit=deposit, deposit_per_bottle=deposit_per_bottle)

    deposit_text = ""
    if deposit > 0:
        deposit_text = (
            f"\n\n<b>⚠️ Залог за тару:</b> <b>{deposit_per_bottle} руб × {bottles} бут. = {deposit} руб</b>."
        )

    text = (
        f"🧾 <b>Проверьте ваш заказ:</b>\n\n"
        f"Клиент: {client_type}\n"
        f"Город/район: {city_or_area.capitalize()}\n"
        f"Адрес: {full_address}\n"
        f"Количество бутылок: {bottles}\n"
        f"Цена за бутыль: {price} руб\n"
        f"<b>Итоговая сумма:</b> {total} руб\n"
        f"Телефон: {data.get('phone')}\n"
        f"Комментарий: {data.get('comment')}"
        f"{deposit_text}\n\n"
        f"Всё верно?"
    )

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("✅ Всё верно", "✏️ Изменить данные")
    keyboard.add("🔄 Начать заново")
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    await OrderState.confirm.set()

# --- Подтверждение ---
@dp.message_handler(state=OrderState.confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "✅ Всё верно":
        client_type = data.get("client_type")
        bottles = int(data.get("bottles", 0))
        price = int(data.get("price", 0))
        total = int(data.get("total", 0))
        deposit_per_bottle = 250
        deposit = bottles * deposit_per_bottle if client_type == "Новый клиент" else 0
        total_without_deposit = total - deposit if deposit else total

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_id = message.from_user.id

        sheet.append_row([
            timestamp,
            client_type,
            data.get("full_address"),
            bottles,
            price,
            total,
            data.get("phone"),
            data.get("comment"),
            "",
            "False",
            user_id
        ])

        if client_type == "Новый клиент":
            title = "🚨 НОВЫЙ КЛИЕНТ — ПЕРЕЗВОНИТЬ 🚨"
        else:
            title = "🆕 Новый заказ"

        manager_text = (
            f"{title}\n\n"
            f"Клиент: {client_type}\n"
            f"Адрес: {data.get('full_address')}\n"
            f"Количество бутылок: {bottles}\n"
            f"Цена за бутыль: {price} руб\n"
            f"💵 Итого: {total} руб\n\n"
            f"Телефон: {data.get('phone')}\n"
            f"Комментарий: {data.get('comment')}\n\n"
            f"Используйте команду /assign_delivery_date, чтобы назначить дату доставки."
        )

        client_text = (
            f"Спасибо за заказ 💧\n"
            f"Ваш заказ: {bottles} бут. по {price} руб\n"
            f"Сумма: {total} руб\n\n"
            f"🚚 Менеджер свяжется с вами для подтверждения даты доставки.\n\n"
            f"Если хотите внести изменения или отменить заказ, звоните менеджеру:\n"
            f"📞 {MANAGER_PHONE}\nTelegram: {MANAGER_USERNAME}"
        )

        await bot.send_message(MANAGER_ID, manager_text, parse_mode="HTML")
        await message.answer(client_text, reply_markup=main_keyboard())

# --- Команда для менеджера: назначить дату ---
@dp.message_handler(commands=["assign_delivery_date"])
async def assign_date_start(message: types.Message):
    if str(message.from_user.id) != str(MANAGER_ID):
        await message.answer("Эта команда доступна только менеджеру.")
        return

    await message.answer("Введите дату доставки (в формате ДД.MM или ДД.MM.YYYY):")
    await OrderState.assign_delivery_date.set()

# --- Менеджер вводит дату ---
@dp.message_handler(state=OrderState.assign_delivery_date)
async def assign_date_finish(message: types.Message, state: FSMContext):
    delivery_date = message.text.strip()
    records = sheet.get_all_values()

    for i in range(len(records) - 1, 0, -1):
        if len(records[i]) >= 10 and (records[i][9] == "" or records[i][9] == "False"):
            user_id = records[i][10]
            sheet.update_cell(i + 1, 9, delivery_date)
            sheet.update_cell(i + 1, 10, "True")
            try:
                await bot.send_message(
                    user_id,
                    f"Ваш заказ подтверждён ✅\nДата доставки: {delivery_date}\n\n"
                    f"Если хотите внести изменения или отменить заказ, звоните менеджеру:\n"
                    f"📞 {MANAGER_PHONE}\nTelegram: {MANAGER_USERNAME}"
                )
                await message.answer(f"Доставка назначена на {delivery_date}. Клиент уведомлён ✅")
            except Exception as e:
                await message.answer(f"Не удалось отправить уведомление клиенту: {e}")
            break
    else:
        await message.answer("Не найден заказ без даты доставки.")

    await state.finish()

# --- Запуск ---
if __name__ == "__main__":
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
