import datetime
import logging
import random
import sys
from collections import defaultdict
from io import BytesIO

import aiogram
from PIL import Image
from dotenv import load_dotenv

import asyncio
import os

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, Filter, CommandObject
from aiogram.types import Message, BufferedInputFile, CallbackQuery, InputMediaPhoto, FSInputFile, ChosenInlineResult
from aiogram import F

from bot.bot_utils import upload_file_to_vps
from bot.keyboards import main_menu_keyboard, ranked_types_keyboard_row, back_keyboard_row, slider_keyboard_row
from collector.api import BrawlAPI, api_context
from db.session import SessionLocal
from repositories.account_repository import AccountRepository
from repositories.user_repository import UserRepository

from services.image_generation.image_service import (
    create_main_ranked_img,
    create_ranked_img_by_modes,
    create_ranked_img_by_brawlers,
)

from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
BS_API_TOKEN = os.getenv('BS_API_TOKEN')
CURRENT_MACHINE_TYPE = os.getenv('CURRENT_MACHINE_TYPE') # local / vps

IMG_SAVE_DIR = 'bot/images/for_tg/'

dp = Dispatcher()

STATE_PARAMS_DEFAULTS = {
    'adding_account': False,
    'current_account_tag': None
}

state = defaultdict(dict)
users = {}
accounts = {}

def get_state(entity_id, param):
    """
    This function can get state of an entity (user / message / ...)
    """
    entity_state = state[entity_id]
    return entity_state.get(param, STATE_PARAMS_DEFAULTS[param])

def set_state(entity_id, param, value):
    """
    This function can set state of an entity (user / message / ...)
    """
    entity_state = state[entity_id]
    entity_state[param] = value

async def get_or_create_user(user_id, username):
    if user_id in users:
        return users[user_id]

    user = await user_repo.get_by_tg_with_accounts(user_id)
    if not user:
        user = await user_repo.create(user_id, username)

    for acc in user.accounts:
        accounts[acc.player_tag] = acc

    users[user_id] = user

    return user

async def get_or_fetch_account(player_tag):
    if player_tag in accounts:
        return accounts[player_tag]

    account = await account_repo.get_by_tag(player_tag)
    if account:
        accounts[player_tag] = account

    return account

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message(Command('accounts'))
async def get_accounts(message: Message) -> None:
    print(message.from_user.id)

    user = await get_or_create_user(message.from_user.id, message.from_user.username)

    response = f'You have {len(user.accounts)} accounts associated'
    if user.accounts:
        response += f': \n'
        for i, acc in enumerate(user.accounts):
            response += f'{i + 1}. {acc.nickname} ({acc.player_tag})\n'

    await message.answer(response)


@dp.message(Command('add_account'))
async def add_account_command(message: Message) -> None:
    set_state(message.from_user.id, 'adding_account', True)

    response = ('Enter your brawl stars tag. Example: \n\n'
                '#VUU08YVR')

    await message.answer(response)


@dp.message(lambda message: get_state(message.from_user.id, 'adding_account'))
async def add_account(message: Message) -> None:
    user = await get_or_create_user(message.from_user.id, message.from_user.username)

    tag = message.text
    if not tag.startswith('#'):
        tag = '#' + tag

    async with api_context(BS_API_TOKEN) as api_client:
        status_code, profile_json = await api_client.get_profile(tag)
    if status_code == 200:
        try:
            account = await account_repo.get_by_tag(tag)
            if account is None:
                account_name = profile_json['name']
                account = await account_repo.create(tag, account_name)
            if account in user.accounts:
                response = 'You have already added that account'
            else:
                user.accounts.append(account)
                await session.commit()
                response = 'Added account successfully'

        except Exception as e:
            response = 'Something went wrong'
            print(e)
    else:
        response = 'Could not add profile. Make sure you entered the tag correctly.'
        print(status_code, profile_json)

    await message.answer(response)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)

    await session.close()


@dp.inline_query()
async def inline_handler(query: InlineQuery):
    user = await get_or_create_user(query.from_user.id, query.from_user.username)


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=main_menu_keyboard()
    )

    results = []
    for i, acc in enumerate(user.accounts):
        results.append(
            InlineQueryResultArticle(
                id=acc.player_tag,
                title=acc.nickname,
                input_message_content=InputTextMessageContent(
                    message_text=acc.nickname
                ),
                reply_markup=keyboard
            )
        )

    await query.answer(results, cache_time=0)


@dp.chosen_inline_result()
async def chosen(result: ChosenInlineResult):
    set_state(result.inline_message_id, 'current_account_tag', result.result_id)


@dp.callback_query()
async def handler(callback: CallbackQuery):
    await callback.answer()

    if callback.data == 'main_menu':
        await callback.bot.edit_message_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=main_menu_keyboard()
            )
        )

    if callback.data == 'ladder':
        ...
    elif callback.data == 'ranked':
        await callback.bot.edit_message_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    ranked_types_keyboard_row(),
                    back_keyboard_row('main_menu')
                ]
            )
        )
    else:
        keyboard = []
        player_tag = get_state(callback.inline_message_id, 'current_account_tag')
        account = await get_or_fetch_account(player_tag)
        if callback.data == 'by_rank':
            img = await create_main_ranked_img(account.player_tag, account.nickname)
            keyboard.append(ranked_types_keyboard_row())
            keyboard.append(back_keyboard_row('main_menu'))
        elif callback.data == 'by_mode':
            img = await create_ranked_img_by_modes(account.player_tag, account.nickname)
            keyboard.append(ranked_types_keyboard_row())
            keyboard.append(back_keyboard_row('main_menu'))
        elif callback.data.startswith('by_brawler'):
            page = int(callback.data.split(':')[1])
            img, num_of_pages = await create_ranked_img_by_brawlers(
                account.player_tag, account.nickname, page=page
            )
            has_prev, has_next = page > 1, page < num_of_pages

            keyboard.append(slider_keyboard_row(page, has_prev, has_next, num_of_pages))
            keyboard.append(back_keyboard_row('ranked'))

        else:
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
        img_filename = f'{timestamp}_{random.randint(900, 999)}.webp'
        img.save(f'{IMG_SAVE_DIR}/{img_filename}', format='WebP')
        if CURRENT_MACHINE_TYPE != 'vps':
            upload_file_to_vps(
                local_file=f'bot/images/for_tg/{img_filename}',
                remote_file=f'/root/wdstats/bot/images/for_tg/{img_filename}',
            )
        # img.show()

        try:
            await callback.bot.edit_message_reply_markup(
                inline_message_id=callback.inline_message_id,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=keyboard
                )
            )
        except aiogram.exceptions.TelegramBadRequest as e:
            print('keyboard stayed the same')

        await callback.bot.edit_message_media(
            inline_message_id=callback.inline_message_id,
            media=InputMediaPhoto(
                media=f"https://wdraft.online/images/{img_filename}",
                # media="https://wdraft.online/images/i-show-speed.jpg"
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            )
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    session = SessionLocal()
    user_repo = UserRepository(session)
    account_repo = AccountRepository(session)

    asyncio.run(main())
