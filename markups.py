from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

btnUrlChannel = InlineKeyboardButton(text="Подписаться 😌", url="https://t.me/+x2s5emOgGXQxOGEy")
btnDoneSub = InlineKeyboardButton(text="Проверить подписку! ✅", callback_data="subchanneldone")

checkSubMenu = InlineKeyboardMarkup(inline_keyboard=[
    [btnUrlChannel],
    [btnDoneSub]
])
