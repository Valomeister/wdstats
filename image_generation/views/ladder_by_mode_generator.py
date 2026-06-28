import asyncio
import math

from image_generation.assets.fonts import inter22, inter42
from image_generation.assets.images import DARK_BG, GAME_MODE_ICONS, SMALLER_BRAWLER_ICONS
from image_generation.image_utils import draw_bar, normalize_name, draw_text_centered, paste_image_with_border, \
    gradient_rect
from image_generation.layout_config import lp, REQUIRED_MODES, gamemodes_colors
from image_generation.views.template_generator import get_template
from services.stats_service import StatsService


async def gen_ladder_img_by_mode(ladder_stats, ladder_stats_by_modes, top_ladder_brawlers_by_modes, player_nickname, page):
    total_games, wins, draws, losses = ladder_stats

    print(ladder_stats_by_modes)
    print(total_games, wins, draws, losses)
    print(top_ladder_brawlers_by_modes)

    canvas, draw = await get_template(ladder_stats, player_nickname, 'ladder')

    row_capacity = 2
    col_capacity = 3
    num_of_pages = math.ceil(len(top_ladder_brawlers_by_modes) / (row_capacity * col_capacity))

    cards_inner_horizontal_margin = 20 # inside cards
    cards_outer_margin = 20 # between cards
    mode_icons_height = 60
    modes_card_width = lp.bar_width + mode_icons_height * 2 + 4 * cards_inner_horizontal_margin
    modes_card_height = (lp.screen_height - 2 * lp.margin - 2 * cards_outer_margin) / 3
    modes_area_width = 2 * modes_card_width + 2 * lp.margin + cards_outer_margin
    card_row_height = modes_card_height / 4
    offset_x = lp.screen_width - modes_area_width
    offset_y = lp.margin

    area_outer_width = lp.screen_width - offset_x
    grad_height = 50

    # blur bg
    canvas.paste(DARK_BG, (offset_x, 0), DARK_BG)

    iteration_start = (page - 1) * (row_capacity * col_capacity) - row_capacity
    iteration_end = min(len(top_ladder_brawlers_by_modes), page * (row_capacity * col_capacity) + row_capacity)
    for abs_i in range(iteration_start, iteration_end):
        if abs_i < 0:
            continue
        rel_i = abs_i - iteration_start
        row = rel_i // row_capacity - 1
        col = rel_i % row_capacity
        card_center_x = offset_x + lp.margin + col * (modes_card_width + cards_outer_margin) + modes_card_width / 2
        card_start_x = card_center_x - modes_card_width / 2
        card_end_x = card_start_x + modes_card_width
        card_start_y = offset_y + row * (modes_card_height + cards_outer_margin)
        card_end_y = card_start_y + modes_card_height

        center_x = (
            + offset_x
            + lp.margin
            + col * (modes_card_width + cards_outer_margin)
            + modes_card_width / 2
        )
        center_y = (
            + lp.margin
            + row * (modes_card_height + cards_outer_margin)
            + modes_card_height / 2
        )
        card_start_x = center_x - modes_card_width / 2
        card_start_y = center_y - modes_card_height / 2
        card_end_x = center_x + modes_card_width / 2
        card_end_y = center_y + modes_card_height / 2

        game_mode = sorted(top_ladder_brawlers_by_modes.keys())[abs_i]
        game_mode_color = gamemodes_colors.get(game_mode, '#fff')

        draw.rounded_rectangle(
            (card_start_x, card_start_y, card_end_x, card_start_y + card_row_height),
            radius=20,
            fill='black',
            corners=(True, True, False, False)
        )
        draw.rounded_rectangle(
            (card_start_x, card_start_y + card_row_height, card_end_x, card_end_y + 3),
            radius=20,
            fill=game_mode_color,
            corners=(False, False, True, True)
        )
        draw.rounded_rectangle(
            (card_start_x, card_start_y, card_end_x, card_end_y + 3),
            radius=20,
            width=5,
            outline='black'
        )

        # game_mode bar
        bar_start_x = card_end_x - cards_inner_horizontal_margin - lp.bar_width
        bar_center_y = card_start_y + card_row_height / 2
        bar_start_y = bar_center_y - lp.bar_height / 2
        mode_stats = ladder_stats_by_modes[game_mode]
        draw_bar(draw, (bar_start_x, bar_start_y), *mode_stats, inter22)

        # game_mode icon
        normalized_mode_name = normalize_name(game_mode)
        placeholder_mode_icon = GAME_MODE_ICONS['placeholder']
        game_mode_icon = GAME_MODE_ICONS.get(normalized_mode_name, placeholder_mode_icon)
        mode_icon_start_x = int(card_start_x + cards_inner_horizontal_margin)
        mode_icon_center_y = card_start_y + card_row_height / 2
        mode_icon_start_y = int(mode_icon_center_y - mode_icons_height / 2)
        canvas.paste(game_mode_icon, (mode_icon_start_x, mode_icon_start_y), game_mode_icon)

        # top-3 brawlers
        for j in range(3):
            # position (#1 / #2 / #2)
            position_start_x = int(card_start_x + cards_inner_horizontal_margin)
            position_center_y = card_start_y + card_row_height / 2 + card_row_height * (j + 1)
            position_start_y = position_center_y - mode_icons_height / 2
            position_end_x = position_start_x + mode_icons_height
            position_end_y = position_start_y + mode_icons_height
            draw_text_centered(
                draw,
                (position_start_x, position_start_y, position_end_x, position_end_y),
                f'#{j + 1}',
                inter42,
                4
            )

            # brawler
            placeholder_icon = SMALLER_BRAWLER_ICONS['placeholder']
            normalized_brawler_name = normalize_name(top_ladder_brawlers_by_modes[game_mode][j][0])
            brawler_icon = SMALLER_BRAWLER_ICONS.get(normalized_brawler_name, placeholder_icon)
            brawler_start_x = int(card_start_x + cards_inner_horizontal_margin + mode_icons_height + cards_inner_horizontal_margin)
            brawler_center_y = card_start_y + card_row_height / 2 + card_row_height * (j + 1)
            brawler_start_y = int(brawler_center_y - mode_icons_height / 2)
            brawler_end_x = brawler_start_x + mode_icons_height
            brawler_end_y = brawler_start_y + mode_icons_height
            paste_image_with_border(canvas, draw, (brawler_start_x, brawler_start_y), brawler_icon, 5)

            # bar
            brawler_bar_start_x = card_end_x - cards_inner_horizontal_margin - lp.bar_width
            brawler_bar_center_y = card_start_y + card_row_height / 2 + card_row_height * (j + 1)
            brawler_bar_start_y = brawler_bar_center_y - lp.bar_height / 2
            mode_stats = top_ladder_brawlers_by_modes[game_mode][j][1:-1]
            draw_bar(draw, (brawler_bar_start_x, brawler_bar_start_y), *mode_stats, inter22)

    if page * (row_capacity * col_capacity) < len(top_ladder_brawlers_by_modes):
        grad = gradient_rect((area_outer_width, grad_height))
        canvas.paste(grad, (offset_x, lp.screen_height - grad_height), grad)

    if page > 1 and (page - 1) * (row_capacity * col_capacity) + 1 <= len(top_ladder_brawlers_by_modes):
        grad = gradient_rect((area_outer_width, grad_height), start_alpha=255, end_alpha=0)
        canvas.paste(grad, (offset_x, 0), grad)

    return canvas, num_of_pages

    return canvas


async def fetch_data_for_ranked_by_mode(tag):
    ladder_stats, ladder_stats_by_modes, top_ladder_brawlers_by_modes = await asyncio.gather(
        StatsService.get_ladder_stats(tag),
        StatsService.get_ladder_stats_by_modes(tag),
        StatsService.get_top_ladder_brawlers_by_modes(tag),
    )

    return ladder_stats, ladder_stats_by_modes, top_ladder_brawlers_by_modes


async def create_ladder_img_by_mode(tag, player_nickname, page):
    ladder_stats, ladder_stats_by_modes, top_ladder_brawlers_by_modes = await(fetch_data_for_ranked_by_mode(tag))
    return await gen_ladder_img_by_mode(ladder_stats, ladder_stats_by_modes, top_ladder_brawlers_by_modes, player_nickname, page)