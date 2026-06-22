from aiogram.types import InlineKeyboardButton


def main_menu_keyboard():
    return \
        [
            [
                InlineKeyboardButton(
                    text="ranked",
                    callback_data="ranked"
                ),
                InlineKeyboardButton(
                    text="ladder",
                    callback_data="ladder"
                )
            ]
        ]

def ranked_types_keyboard_row():
    return \
        [
            InlineKeyboardButton(
                text="By rank",
                callback_data="by_rank"
            ),
            InlineKeyboardButton(
                text="By mode",
                callback_data="by_mode"
            ),
            InlineKeyboardButton(
                text="By brawler",
                callback_data="by_brawler:1"
            )
        ]

def back_keyboard_row(callback_data):
    return \
        [
            InlineKeyboardButton(
                text="Back",
                callback_data=callback_data
            ),
        ]

def slider_keyboard_row(page, has_prev, has_next, num_of_pages):
    return \
        [
            InlineKeyboardButton(
                text="⟵" if has_prev else '·',
                callback_data=f"by_brawler:{page - 1}" if has_prev else 'noop'
            ),
            InlineKeyboardButton(
                text=f"page {page}/{num_of_pages}",
                callback_data=f"noop"
            ),
            InlineKeyboardButton(
                text="⟶" if has_next else '·',
                callback_data=f"by_brawler:{page + 1}" if has_next else 'noop'
            )
        ]