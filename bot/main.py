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
from bot.keyboards import (
    setup_menu,
    main_menu_keyboard,
    ranked_menu_keyboard,
    ladder_menu_keyboard,
    history_menu_keyboard,
    back_keyboard_row,
    slider_keyboard_row,
)

from collector.api import BrawlAPI, api_context
from db.session import SessionLocal
from image_generation.views.ladder_by_brawler_generator import create_ladder_img_by_brawler
from image_generation.views.ladder_by_mode_generator import create_ladder_img_by_mode
from image_generation.views.main_ladder_generator import create_main_ladder_img
from repositories.account_repository import AccountRepository
from repositories.user_repository import UserRepository

from image_generation.views.main_ranked_generator import create_main_ranked_img
from image_generation.views.ranked_by_mode_generator import create_ranked_img_by_mode
from image_generation.views.ranked_by_brawler_generator import create_ranked_img_by_brawler
from image_generation.views.compact_matches_generator import create_compact_matches_img
from image_generation.views.detailed_matches_generator import create_detailed_matches_img

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
inline_mode_state = defaultdict(list)

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

    if user:
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
                response = f'Added {account.nickname} successfully'
                set_state(message.from_user.id, 'adding_account', False)

        except Exception as e:
            response = 'Something went wrong'
            print(e)
    else:
        response = 'Could not add profile. Make sure you entered the tag correctly.'
        print(status_code, profile_json)

    await message.answer(response)


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
    inline_mode_state[(result.from_user.id, result.inline_message_id)].extend([
        {
            'view': 'PROFILE_CHOICE',
            'params': {
                'chosen_tag': result.result_id
            }
        },
        {
            'view': 'MAIN_MENU',
            'params': {}
        }
    ])


@dp.callback_query()
async def handler(callback: CallbackQuery):
    await callback.answer()

    key = (callback.from_user.id, callback.inline_message_id)
    stack = inline_mode_state[key]
    print(stack)

    if callback.data == 'back':
        print('back')
        stack.pop()
        view_to_render = stack[-1]['view']
    elif callback.data == 'noop':
        return
    else:
        view_to_render = str(callback.data)

    await renderers[view_to_render](stack[-1], callback, key, stack)


async def main_menu_renderer(state, callback: CallbackQuery, key, stack):
    print(f'main_menu_renderer()')
    print(inline_mode_state[key])
    await callback.bot.edit_message_reply_markup(
        inline_message_id=callback.inline_message_id,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=main_menu_keyboard()
        )
    )

async def ranked_menu_renderer(state, callback: CallbackQuery, key, stack):
    print(f'ranked_menu_renderer()')
    if callback.data != 'back':
        stack.append(
            {
                'view': callback.data,
                'params': {}
            }
        )
    print(inline_mode_state[key])
    await callback.bot.edit_message_media(
        inline_message_id=callback.inline_message_id,
        media=InputMediaPhoto(
            media=f"https://wdraft.online/images/black.png",
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=ranked_menu_keyboard()
        )
    )


async def ranked_by_rank_gen_renderer(state, callback: CallbackQuery, key, stack):
    print(f'ranked_by_rank_gen_renderer()')
    if stack[-1]['view'] != 'RANKED_MENU':
        stack.pop()
    stack.append(
        {
            'view': callback.data,
            'params': {}
        }
    )
    print(inline_mode_state[key])

    player_tag = stack[0]['params']['chosen_tag']
    account = await get_or_fetch_account(player_tag)

    img = await create_main_ranked_img(account.player_tag, account.nickname)
    await send_img(img, callback, ranked_menu_keyboard())


async def ranked_by_mode_gen_renderer(state, callback: CallbackQuery, key, stack):
    print(f'ranked_by_mode_gen_renderer()')
    if stack[-1]['view'] != 'RANKED_MENU':
        stack.pop()
    stack.append(
        {
            'view': callback.data,
            'params': {}
        }
    )

    print(inline_mode_state[key])

    player_tag = stack[0]['params']['chosen_tag']
    account = await get_or_fetch_account(player_tag)

    img = await create_ranked_img_by_mode(account.player_tag, account.nickname)
    await send_img(img, callback, ranked_menu_keyboard())


async def ladder_menu_renderer(state, callback: CallbackQuery, key, stack):
    print(f'ladder_menu_renderer()')
    if callback.data != 'back':
        stack.append(
            {
                'view': callback.data,
                'params': {}
            }
        )
    print(inline_mode_state[key])
    await callback.bot.edit_message_media(
        inline_message_id=callback.inline_message_id,
        media=InputMediaPhoto(
            media=f"https://wdraft.online/images/black.png",
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=ladder_menu_keyboard()
        )
    )


async def ladder_by_rank_gen_renderer(state, callback: CallbackQuery, key, stack):
    print(f'ladder_by_rank_gen_renderer()')
    if stack[-1]['view'] != 'LADDER_MENU':
        stack.pop()
    stack.append(
        {
            'view': callback.data,
            'params': {}
        }
    )
    print(inline_mode_state[key])

    player_tag = stack[0]['params']['chosen_tag']
    account = await get_or_fetch_account(player_tag)

    img = await create_main_ladder_img(account.player_tag, account.nickname)
    await send_img(img, callback, ladder_menu_keyboard())


async def history_menu_renderer(state, callback: CallbackQuery, key, stack):
    print(f'history_menu_renderer()')
    if callback.data != 'back':
        stack.append(
            {
                'view': callback.data,
                'params': {}
            }
        )
    print(inline_mode_state[key])
    await callback.bot.edit_message_media(
        inline_message_id=callback.inline_message_id,
        media=InputMediaPhoto(
            media=f"https://wdraft.online/images/black.png",
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=history_menu_keyboard()
        )
    )


async def slideable_renderer(state, callback: CallbackQuery, key, stack):
    slideable_view = callback.data
    if slideable_view[-5:] in ('_PREV', '_NEXT'):
        slideable_view = slideable_view[:-5]

    img_create_func = slideable_params[slideable_view]['img_create_func']
    parent_view = slideable_params[slideable_view]['parent_view']
    prev_page_view = slideable_view + '_PREV'
    next_page_view = slideable_view + '_NEXT'

    print(f'slideable_renderer({slideable_view=})')
    page = 1
    if stack[-1]['view'] == slideable_view:
        page = stack[-1]['params']['page']
    else:
        if stack[-1]['view'] != parent_view:
            stack.pop()
        stack.append(
            {
                'view': callback.data,
                'params': {
                    'page': 1
                }
            }
        )

    print(inline_mode_state[key])

    player_tag = stack[0]['params']['chosen_tag']
    account = await get_or_fetch_account(player_tag)

    img, num_of_pages = await img_create_func(
        account.player_tag, account.nickname, page=page
    )
    has_prev, has_next = page > 1, page < num_of_pages

    await send_img(img, callback, [
        slider_keyboard_row(
            page, has_prev, has_next, num_of_pages,
            prev_view=prev_page_view, next_view=next_page_view
        ),
        back_keyboard_row()
    ])


async def slideable_prev_renderer(state, callback: CallbackQuery, key, stack):
    state['params']['page'] -= 1
    await slideable_renderer(state, callback, key, stack)

async def slideable_next_renderer(state, callback: CallbackQuery, key, stack):
    state['params']['page'] += 1
    await slideable_renderer(state, callback, key, stack)


async def send_img(img, callback: CallbackQuery, keyboard):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
    img_filename = f'{timestamp}_{random.randint(900, 999)}.webp'
    img.save(f'{IMG_SAVE_DIR}/{img_filename}', format='WebP')
    if CURRENT_MACHINE_TYPE != 'vps':
        upload_file_to_vps(
            local_file=f'bot/images/for_tg/{img_filename}',
            remote_file=f'/root/wdstats/bot/images/for_tg/{img_filename}',
        )
    # img.show()


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

async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await setup_menu(bot)

    await dp.start_polling(bot)

    await session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    session = SessionLocal()
    user_repo = UserRepository(session)
    account_repo = AccountRepository(session)

    slideable_params = {
        'HISTORY_COMPACT_GEN': {
            'img_create_func': create_compact_matches_img,
            'parent_view': 'HISTORY_MENU'
        },
        'HISTORY_DETAILED_GEN': {
            'img_create_func': create_detailed_matches_img,
            'parent_view': 'HISTORY_MENU'
        },
        'RANKED_BY_BRAWLER_GEN': {
            'img_create_func': create_ranked_img_by_brawler,
            'parent_view': 'RANKED_MENU'
        },
        'LADDER_BY_MODE_GEN': {
            'img_create_func': create_ladder_img_by_mode,
            'parent_view': 'LADDER_MENU'
        },
        'LADDER_BY_BRAWLER_GEN': {
            'img_create_func': create_ladder_img_by_brawler,
            'parent_view': 'LADDER_MENU'
        },
    }

    renderers = {
        # main
        'MAIN_MENU': main_menu_renderer, # actually only called when we get to main menu by pressing "back"

        # ranked
        'RANKED_MENU': ranked_menu_renderer,
        'RANKED_BY_RANK_GEN': ranked_by_rank_gen_renderer,
        'RANKED_BY_MODE_GEN': ranked_by_mode_gen_renderer,
        'RANKED_BY_BRAWLER_GEN': slideable_renderer,
        'RANKED_BY_BRAWLER_GEN_PREV': slideable_prev_renderer,
        'RANKED_BY_BRAWLER_GEN_NEXT': slideable_next_renderer,

        # ladder
        'LADDER_MENU': ladder_menu_renderer,
        'LADDER_BY_RANK_GEN': ladder_by_rank_gen_renderer,
        'LADDER_BY_MODE_GEN': slideable_renderer,
        'LADDER_BY_MODE_GEN_PREV': slideable_prev_renderer,
        'LADDER_BY_MODE_GEN_NEXT': slideable_next_renderer,
        'LADDER_BY_BRAWLER_GEN': slideable_renderer,
        'LADDER_BY_BRAWLER_GEN_PREV': slideable_prev_renderer,
        'LADDER_BY_BRAWLER_GEN_NEXT': slideable_next_renderer,

        #history
        'HISTORY_MENU': history_menu_renderer,
        'HISTORY_COMPACT_GEN': slideable_renderer,
        'HISTORY_COMPACT_GEN_PREV': slideable_prev_renderer,
        'HISTORY_COMPACT_GEN_NEXT': slideable_next_renderer,
        'HISTORY_DETAILED_GEN': slideable_renderer,
        'HISTORY_DETAILED_GEN_PREV': slideable_prev_renderer,
        'HISTORY_DETAILED_GEN_NEXT': slideable_next_renderer,

    }

    asyncio.run(main())
