import asyncio
import math
from datetime import datetime, UTC

from image_generation.assets.fonts import inter30, inter36
from image_generation.assets.images import PARTIALLY_ROUNDED_BRAWLER_ICONS, DARK_BG, GAME_MODE_ICONS, MODE_PLACEHOLDER, \
    RANK_ICONS_NO_DIGITS, TROPHY
from image_generation.image_utils import normalize_name, format_datetime_diff, draw_text_align_to_side, \
    paste_icon_and_text, gradient_rect
from image_generation.layout_config import lp, result_colors
from image_generation.views.template_generator import get_template
from services.stats_service import StatsService


ROW_CAPACITY = 4
COL_CAPACITY = 5


async def gen_compact_matches_img(stats, matches, total_matches_count, player_nickname, page):
    total_games, wins, draws, losses = stats

    print(*matches[:10], sep='\n')
    print(total_games, wins, draws, losses)

    canvas, draw = await get_template(stats, player_nickname, 'total')
    num_of_pages = math.ceil(total_matches_count / (ROW_CAPACITY * COL_CAPACITY))
    border_width = 6
    inner_margin = 8  # between cards
    outer_margin = 40
    trophy_icon_text_gap = 6
    card_width = 290
    card_height = 180
    icon_w, icon_h = PARTIALLY_ROUNDED_BRAWLER_ICONS['shelly'].width, PARTIALLY_ROUNDED_BRAWLER_ICONS['shelly'].height
    badge_width = card_width
    badge_height = card_height - icon_h
    area_outer_width = outer_margin * 2 + ROW_CAPACITY * card_width + (ROW_CAPACITY - 1) * inner_margin
    grad_height = 50
    offset_x = lp.screen_width - area_outer_width
    offset_y = int((lp.screen_height - COL_CAPACITY * card_height - (COL_CAPACITY - 1) * inner_margin) / 2)

    # blur bg
    canvas.paste(DARK_BG, (offset_x, 0), DARK_BG)

    iteration_start = 0
    iteration_end = min(len(matches), page * (ROW_CAPACITY * COL_CAPACITY) + 2 * ROW_CAPACITY)
    for rel_i in range(iteration_start, iteration_end):
        if page == 1:
            row = rel_i // ROW_CAPACITY
        else:
            row = rel_i // ROW_CAPACITY - 1
        col = rel_i % ROW_CAPACITY

        card_center_x = offset_x + lp.margin + col * (card_width + inner_margin) + card_width / 2
        card_start_x = card_center_x - card_width / 2
        card_end_x = card_start_x + card_width
        card_start_y = offset_y + row * (card_height + inner_margin)
        card_end_y = card_start_y + card_height

        # badge bg
        badge_start_x = card_start_x
        badge_end_x = badge_start_x + badge_width
        badge_start_y = card_start_y
        badge_end_y = badge_start_y + badge_height
        draw.rounded_rectangle(
            (badge_start_x, badge_start_y, badge_end_x, badge_end_y),
            fill='#000',
            radius=20,
            corners=(True, True, False, False)
        )

        # game_mode
        print(len(matches), rel_i)
        game_mode = matches[rel_i][1]
        normalized_mode_name = normalize_name(game_mode)
        game_mode_icon = GAME_MODE_ICONS.get(normalized_mode_name, MODE_PLACEHOLDER)
        # game_mode_icon = random.choice(list(GAME_MODE_ICONS.values()))
        game_mode_icon_start_x = int(card_start_x + (badge_height - game_mode_icon.height) / 2)
        game_mode_icon_center_y = card_start_y + badge_height / 2
        game_mode_icon_start_y = int(game_mode_icon_center_y - game_mode_icon.height / 2)
        canvas.paste(game_mode_icon, (game_mode_icon_start_x, game_mode_icon_start_y), game_mode_icon)

        # brawler
        normalized_name = normalize_name(matches[rel_i][6])
        placeholder_icon = PARTIALLY_ROUNDED_BRAWLER_ICONS['placeholder']
        brawler_icon = PARTIALLY_ROUNDED_BRAWLER_ICONS.get(normalized_name, placeholder_icon)
        brawler_start_x = int(card_start_x)
        brawler_start_y = int(card_start_y + badge_height)
        brawler_end_x = brawler_start_x + brawler_icon.width
        brawler_end_y = brawler_start_y + brawler_icon.height
        canvas.paste(brawler_icon, (brawler_start_x, brawler_start_y), brawler_icon)

        # result color
        if game_mode in ("soloShowdown", "duoShowdown", "trioShowdown"):
            trophy_change = matches[rel_i][7]
            if trophy_change is not None and trophy_change > 0:
                result = 1
            elif trophy_change is not None and trophy_change < 0:
                result = -1
            else:
                result = 0
        else:
            result = matches[rel_i][4]
        draw.rounded_rectangle(
            (brawler_end_x, brawler_start_y, card_end_x, card_end_y),
            fill=result_colors[result],
            radius=18,
            corners=(False, False, True, False)
        )

        # separator
        draw.rectangle(
            (brawler_end_x - 2, brawler_start_y - 1, brawler_end_x + 2, brawler_end_y - 1),
            fill='black'
        )

        # time ago
        now = datetime.now(UTC).replace(tzinfo=None)
        time_diff = format_datetime_diff(now, matches[rel_i][0])
        draw_text_align_to_side(
            draw,
            (
                badge_end_x - int((badge_height - game_mode_icon.height) / 2),
                badge_start_y + badge_height / 2,
                badge_end_x - int((badge_height - game_mode_icon.height) / 2),
                badge_start_y + badge_height / 2
            ),
            time_diff,
            inter30,
            4,
            'white',
            side='right'
        )

        # outline
        draw.rounded_rectangle(
            (card_start_x, card_start_y, card_end_x, card_end_y),
            radius=18,
            outline='black',
            width=border_width
        )

        if matches[rel_i][2] == 'soloRanked':
            rank_family = (matches[rel_i][5] - 1) // 3 + 1
            rank_digit = (matches[rel_i][5] - 1) % 3 + 1
            rank_icon = RANK_ICONS_NO_DIGITS[rank_family]
            trophy_info_center_x = (card_end_x + card_start_x + icon_w) / 2
            trophy_info_center_y = (card_end_y + card_start_y + badge_height) / 2
            paste_icon_and_text(
                canvas,
                draw,
                rank_icon,
                'I' * rank_digit,
                inter36,
                trophy_icon_text_gap,
                center_xy=(trophy_info_center_x, trophy_info_center_y)
            )


        elif matches[rel_i][2] == 'ranked':
            trophy_info_center_x = (card_end_x + card_start_x + icon_w) / 2
            trophy_info_center_y = (card_end_y + card_start_y + badge_height) / 2
            paste_icon_and_text(
                canvas,
                draw,
                TROPHY,
                str(matches[rel_i][5]),
                inter36,
                trophy_icon_text_gap,
                center_xy=(trophy_info_center_x, trophy_info_center_y)
            )

        else:
            print('undefined', matches[rel_i][2])

    if page * (ROW_CAPACITY * COL_CAPACITY) < total_matches_count:
        grad = gradient_rect((area_outer_width, grad_height))
        canvas.paste(grad, (offset_x, lp.screen_height - grad_height), grad)

    if page > 1 and (page - 1) * (ROW_CAPACITY * COL_CAPACITY) + 1 <= total_matches_count:
        grad = gradient_rect((area_outer_width, grad_height), start_alpha=255, end_alpha=0)
        canvas.paste(grad, (offset_x, 0), grad)

    return canvas, num_of_pages


async def fetch_compact_data_for_matches(tag, page):
    limit = ROW_CAPACITY * (COL_CAPACITY + 2)
    offset = max(0, (ROW_CAPACITY * COL_CAPACITY) * (page - 1) - ROW_CAPACITY)
    overall_stats, matches_batch, total_matches_count = await asyncio.gather(
        StatsService.get_overall_stats(tag),
        StatsService.get_matches(tag, limit=limit, offset=offset),
        StatsService.count_matches(tag),
    )

    return overall_stats, matches_batch, total_matches_count


async def create_compact_matches_img(tag, player_nickname, page):
    stats, matches_batch, total_matches_count = await(fetch_compact_data_for_matches(tag, page))
    return await gen_compact_matches_img(stats, matches_batch, total_matches_count, player_nickname, page)