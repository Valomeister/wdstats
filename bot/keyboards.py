from aiogram import Bot
from aiogram.types import InlineKeyboardButton, BotCommand


async def setup_menu(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(
                command="start",
                description="Launch bot"
            ),
            BotCommand(
                command="accounts",
                description="Your brawl accounts"
            ),
            BotCommand(
                command="add_account",
                description="Add brawl account"
            ),
        ]
    )

def main_menu_keyboard():
    return \
        [
            [
                InlineKeyboardButton(
                    text="ranked",
                    callback_data="RANKED_MENU"
                ),
                InlineKeyboardButton(
                    text="ladder",
                    callback_data="LADDER_MENU"
                ),
                InlineKeyboardButton(
                    text="history",
                    callback_data="HISTORY_MENU"
                )
            ]
        ]

def ranked_menu_keyboard():
    return \
        [
            [
                InlineKeyboardButton(
                    text="Main",
                    callback_data="RANKED_BY_RANK_GEN"
                ),
                InlineKeyboardButton(
                    text="By mode",
                    callback_data="RANKED_BY_MODE_GEN"
                ),
                InlineKeyboardButton(
                    text="By brawler",
                    callback_data="RANKED_BY_BRAWLER_GEN"
                )
            ],
            back_keyboard_row()
        ]

def ladder_menu_keyboard():
    return \
        [
            [
                InlineKeyboardButton(
                    text="Main",
                    callback_data="LADDER_BY_RANK_GEN"
                ),
                InlineKeyboardButton(
                    text="By mode",
                    callback_data="LADDER_BY_MODE_GEN"
                ),
                InlineKeyboardButton(
                    text="By brawler",
                    callback_data="LADDER_BY_BRAWLER_GEN"
                )
            ],
            back_keyboard_row()
        ]

def back_keyboard_row():
    return \
        [
            InlineKeyboardButton(
                text="Back",
                callback_data='back'
            ),
        ]

def slider_keyboard_row(page, has_prev, has_next, num_of_pages, prev_view, next_view):
    return \
        [
            InlineKeyboardButton(
                text="⟵" if has_prev else '·',
                callback_data=prev_view if has_prev else 'noop'
            ),
            InlineKeyboardButton(
                text=f"page {page}/{num_of_pages}",
                callback_data=f"noop"
            ),
            InlineKeyboardButton(
                text="⟶" if has_next else '·',
                callback_data=next_view if has_next else 'noop'
            )
        ]

def history_menu_keyboard():
    return \
        [
            [
                InlineKeyboardButton(
                    text="compact",
                    callback_data="HISTORY_COMPACT_GEN"
                ),
                InlineKeyboardButton(
                    text="detailed",
                    callback_data="HISTORY_DETAILED_GEN"
                )
            ],
            back_keyboard_row()
        ]

