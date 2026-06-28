import asyncio
import math

from image_generation.assets.fonts import inter20
from image_generation.assets.images import DARK_BG, ROUNDED_BRAWLER_ICONS
from image_generation.image_utils import normalize_name, draw_text_align_to_side, draw_text_centered, gradient_rect
from image_generation.layout_config import lp, result_colors
from image_generation.views.template_generator import get_template
from services.stats_service import StatsService


async def gen_ranked_img_by_brawler(ranked_stats, top_ranked_brawlers, player_nickname, page):
    # top_ranked_brawlers = (top_ranked_brawlers * (150 // len(top_ranked_brawlers)))[:104] # for tests
    total_games, wins, draws, losses = ranked_stats

    print(top_ranked_brawlers)
    print(total_games, wins, draws, losses)

    canvas, draw = await get_template(ranked_stats, player_nickname, 'ranked')

    row_capacity = 4
    col_capacity = 8
    num_of_pages = math.ceil(len(top_ranked_brawlers) / (row_capacity * col_capacity))
    border_width = 6
    inner_margin = 18 # between cards
    badge_width = 170
    badge_height = 100
    badge_inner_height = badge_height - 2 * border_width
    badge_inner_width = badge_width - 2 * border_width
    icon_w = icon_h = badge_height - border_width * 2
    card_width = 2 * border_width + icon_w + badge_width
    card_height = icon_h + 2 * border_width
    area_outer_width = lp.margin * 2 + row_capacity * card_width + (row_capacity - 1) * inner_margin
    grad_height = 50
    offset_x = lp.screen_width - area_outer_width
    offset_y = int((lp.screen_height - col_capacity * badge_height - (col_capacity - 1) * inner_margin) / 2)

    # blur bg
    canvas.paste(DARK_BG, (offset_x, 0), DARK_BG)

    iteration_start = (page - 1) * (row_capacity * col_capacity) - row_capacity
    iteration_end = min(len(top_ranked_brawlers), page * (row_capacity * col_capacity) + row_capacity)
    for abs_i in range(iteration_start, iteration_end):
        if abs_i < 0:
            continue
        rel_i = abs_i - iteration_start
        row = rel_i // row_capacity - 1
        col = rel_i % row_capacity
        card_center_x = offset_x + lp.margin + col * (card_width + inner_margin) + card_width / 2
        card_start_x = card_center_x - card_width / 2
        card_end_x = card_start_x + card_width
        card_start_y = offset_y + row * (card_height + inner_margin)
        card_end_y = card_start_y + card_height

        # bg
        draw.rounded_rectangle(
            (card_start_x, card_start_y, card_end_x, card_end_y),
            fill='black',
            radius=20
        )

        # brawler
        normalized_name = normalize_name(top_ranked_brawlers[abs_i][0])
        placeholder_icon = ROUNDED_BRAWLER_ICONS['placeholder']
        brawler_icon = ROUNDED_BRAWLER_ICONS.get(normalized_name, placeholder_icon)
        brawler_center_x = card_start_x + border_width + icon_w / 2
        brawler_center_y = card_start_y + card_height / 2
        brawler_start_x = int(brawler_center_x - icon_w / 2)
        brawler_end_x = brawler_center_x + icon_w / 2
        brawler_start_y = int(brawler_center_y - icon_h / 2)
        brawler_end_y = brawler_center_y + icon_h / 2
        canvas.paste(brawler_icon, (brawler_start_x, brawler_start_y), brawler_icon)

        # badge
        # inner coordinates (inside borders)
        badge_start_x = brawler_end_x + border_width * 2
        badge_end_x = card_end_x - border_width
        badge_start_y = card_start_y + border_width
        badge_end_y = card_end_y - border_width

        # position (#1, #2, ...)
        position_center_y = int(badge_start_y + (badge_inner_height / 3) * 0.5)
        draw_text_align_to_side(
            draw,
            (badge_start_x, position_center_y, badge_end_x, position_center_y),
            f'#{abs_i + 1}',
            inter20,
            fill='white',
            stroke_width=4,
            side='right'
        )

        # total games with brawler
        total_brawler_center_y = int(badge_start_y + (badge_inner_height / 3) * 1.5)
        draw_text_align_to_side(
            draw,
            (badge_start_x, total_brawler_center_y, badge_end_x, total_brawler_center_y),
            f'{top_ranked_brawlers[abs_i][1]} games',
            inter20,
            fill='white',
            stroke_width=4,
            side='right'
        )

        # percentages
        if top_ranked_brawlers[abs_i][1]:
            win_percent = round(top_ranked_brawlers[abs_i][2] / top_ranked_brawlers[abs_i][1] * 100)
            draw_percent = round(top_ranked_brawlers[abs_i][3] / top_ranked_brawlers[abs_i][1] * 100)
            loss_percent = round(top_ranked_brawlers[abs_i][4] / top_ranked_brawlers[abs_i][1] * 100)
        else:
            win_percent = draw_percent = loss_percent = 0
        percentage_center_y = int(badge_start_y + (badge_inner_height / 3) * 2.5)
        wins_w, wins_h = draw_text_align_to_side(
            draw,
            (badge_start_x, percentage_center_y, badge_end_x, percentage_center_y),
            f'{win_percent}%',
            inter20,
            fill=result_colors[1],
            stroke_width=4,
            side='left'
        )
        losses_w, losses_h = draw_text_align_to_side(
            draw,
            (badge_start_x, percentage_center_y, badge_end_x, percentage_center_y),
            f'{loss_percent}%',
            inter20,
            fill=result_colors[-1],
            stroke_width=4,
            side='right'
        )
        draw_text_centered(
            draw,
            (badge_start_x + wins_w, percentage_center_y, badge_end_x - losses_w, percentage_center_y),
            f'{draw_percent}%',
            inter20,
            fill=result_colors[0],
            stroke_width=4,
        )
    if page * (row_capacity * col_capacity) <= len(top_ranked_brawlers):
        grad = gradient_rect((area_outer_width, grad_height))
        canvas.paste(grad, (offset_x, lp.screen_height - grad_height), grad)

    if page > 1 and (page - 1) * (row_capacity * col_capacity) + 1 <= len(top_ranked_brawlers):
        grad = gradient_rect((area_outer_width, grad_height), start_alpha=255, end_alpha=0)
        canvas.paste(grad, (offset_x, 0), grad)

    return canvas, num_of_pages


async def fetch_data_for_ranked_by_brawlers(tag):
    ranked_stats, top_ranked_brawlers = await asyncio.gather(
        StatsService.get_ranked_stats(tag),
        StatsService.get_top_ranked_brawlers(tag, lim=1000), # arbitrary lim grater than the amount of brawlers
    )

    return ranked_stats, top_ranked_brawlers


async def create_ranked_img_by_brawler(tag, player_nickname, page):
    ranked_stats, top_ranked_brawlers = await(fetch_data_for_ranked_by_brawlers(tag))
    return await gen_ranked_img_by_brawler(ranked_stats, top_ranked_brawlers, player_nickname, page)