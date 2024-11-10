from aiogram import Bot, Dispatcher, executor, types
import logging
import requests
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Инициализация бота и диспетчера
API_TOKEN = 'YOUR_BOT_API_TOKEN'
API_BASE_URL = 'https://api.example.com'  # базовый URL для предоставленного API
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)

# Состояния для управления пользователями
class Form(StatesGroup):
    asset_category = State()
    asset_ticker = State()

# Команда /start для инициализации взаимодействия
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я помогу вам следить за активами. Выберите нужную опцию:", reply_markup=main_menu())

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Просмотр активов", "Избранное", "Настройки", "Помощь")
    return markup

# Просмотр списка активов
@dp.message_handler(lambda message: message.text == "Просмотр активов")
async def show_assets(message: types.Message):
    await message.answer("Выберите категорию активов: акции, валюты, криптовалюты.")
    await Form.asset_category.set()

@dp.message_handler(state=Form.asset_category)
async def get_assets(message: types.Message, state: FSMContext):
    category = message.text.lower()
    # Запрос к API для получения списка активов
    response = requests.get(f"{API_BASE_URL}/assets?category={category}")
    if response.status_code == 200:
        assets = response.json()
        assets_list = "\n".join([f"{a['name']} ({a['ticker']}): {a['price']}" for a in assets])
        await message.answer(f"Доступные активы:\n{assets_list}")
    else:
        await message.answer("Ошибка при получении данных о активах.")
    await state.finish()

# Получение информации об активе
@dp.message_handler(commands=['info'])
async def get_asset_info(message: types.Message):
    try:
        ticker = message.get_args()
        response = requests.get(f"{API_BASE_URL}/assets/{ticker}")
        if response.status_code == 200:
            asset = response.json()
            info = f"Название: {asset['name']}\nЦена: {asset['price']}\nОбъем: {asset['volume']}\nРыночная капитализация: {asset['market_cap']}"
            await message.answer(info)
        else:
            await message.answer("Не удалось получить информацию об активе.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# Подписка на уведомления об изменении цены
@dp.message_handler(commands=['subscribe'])
async def subscribe_price_change(message: types.Message):
    args = message.get_args().split()
    if len(args) < 2:
        await message.answer("Использование: /subscribe [тикер] [процент изменения или целевая цена]")
        return
    ticker, value = args[0], args[1]
    # Логика для добавления подписки через API
    response = requests.post(f"{API_BASE_URL}/subscriptions", json={"ticker": ticker, "value": value})
    if response.status_code == 201:
        await message.answer(f"Вы подписались на уведомления для актива {ticker} при изменении цены на {value}%")
    else:
        await message.answer("Не удалось создать подписку.")

# Помощь и поддержка
@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_text = (
        "/start - Инициализация взаимодействия\n"
        "/info [тикер] - Получение текущей информации по активу\n"
        "/chart [ticker] - Отображение графика изменения цены\n"
        "/subscribe [тикер] - Настройка уведомлений для изменения цены\n"
        "/alert [тикер] - Настройка уведомления при достижении определенной цены\n"
        "/favorites - Управление избранными активами\n"
        "/settings - Изменение настроек бота (часовой пояс, валюта)\n"
        "/subscriptions - Просмотр и управление активными подписками"
    )
    await message.answer(help_text)

# Основной запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)