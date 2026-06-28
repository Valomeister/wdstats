import asyncio

from image_generation.assets.fonts import inter22, inter42, inter36, inter30
from image_generation.assets.images import DARK_BG, RANK_ICONS, BRAWLER_ICONS, TROPHY
from image_generation.image_utils import draw_bar, normalize_name, paste_image_with_border, draw_text_centered, \
    paste_icon_and_text, get_text_size
from image_generation.layout_config import lp
from image_generation.views.template_generator import get_template
from services.stats_service import StatsService


ROW_CAPACITY = 3
COL_CAPACITY = 5


async def gen_main_ladder_img(ladder_stats, ladder_stats_by_ranges, top_ladder_brawlers, player_nickname):
    total_games, wins, draws, losses = ladder_stats
    per_range_dict = {int(i[0]): i[1:] for i in ladder_stats_by_ranges}
    print(ladder_stats_by_ranges)
    print(total_games, wins, draws, losses)
    print(top_ladder_brawlers)

    canvas, draw = await get_template(ladder_stats, player_nickname, 'ladder')

    footer_width = lp.screen_width
    available_width = footer_width - 2 * lp.margin
    trophy_icon_text_gap = 10
    col_widths = [
        TROPHY.width + trophy_icon_text_gap + get_text_size(draw, '800 - 999', inter30)[0] + 12 + lp.bar_width,
        TROPHY.width + trophy_icon_text_gap + get_text_size(draw, '1800 - 1999', inter30)[0] + 12 + lp.bar_width,
        TROPHY.width + trophy_icon_text_gap + get_text_size(draw, '2800 - 2999', inter30)[0] + 12 + lp.bar_width,
    ]
    gap_x = (available_width - sum(col_widths)) / 2
    gap_y = 12
    footer_height = 2 * lp.margin + lp.bar_height * 6 + gap_y * 4 + gap_x

    # blur bg
    canvas.paste(DARK_BG, (0, int(lp.screen_height - footer_height)), DARK_BG)

    # ranks
    offset_top = lp.screen_height - footer_height
    offset_left = 0
    available_height = footer_height - 2 * lp.margin
    item_height = lp.bar_height

    brawlers_gap = 20
    brawler_icons_height = 70
    for i in range(ROW_CAPACITY * COL_CAPACITY):
        col = i // COL_CAPACITY
        row = i % COL_CAPACITY

        start_x = round(offset_left + lp.margin + gap_x * col + sum(col_widths[:col]))
        end_x = round(offset_left + lp.margin + gap_x * col + sum(col_widths[:col + 1]))
        start_y = round(offset_top + lp.margin + (item_height + gap_y) * row)
        end_y = round(offset_top + lp.margin + item_height * (row + 1) + gap_y * row)
        center_y = (start_y + end_y) / 2

        # trophy range
        range_start = i * 200
        range_end = i * 200 + 199
        text = f'{range_start} - {range_end}'
        paste_icon_and_text(
            canvas, draw,
            TROPHY,
            text,
            inter30,
            trophy_icon_text_gap,
            start_xy=(start_x, start_y)
        )

        # bar
        cur_range_stats = per_range_dict.get(i, [0, 0, 0, 0])
        rank_bar_start_x = end_x - lp.bar_width
        rank_bar_start_y = int(center_y - lp.bar_height / 2)
        draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_range_stats, inter22)

    # 3000+ trophies separately
    start_x = round(offset_left + lp.margin)
    end_x = round(offset_left + lp.margin + col_widths[0])
    start_y = round(offset_top + lp.margin + lp.bar_height * 5 + gap_y * 4 + gap_x)
    end_y = round(offset_top + lp.margin + lp.bar_height * 5 + gap_y * 4 + gap_x + item_height)
    center_y = (start_y + end_y) / 2

    # trophy range
    text = f'3000+'
    paste_icon_and_text(
        canvas, draw,
        TROPHY,
        text,
        inter30,
        trophy_icon_text_gap,
        start_xy=(start_x, start_y)
    )

    # bar
    cur_range_stats = per_range_dict.get(15, [0, 0, 0, 0])
    rank_bar_start_x = end_x - lp.bar_width
    rank_bar_start_y = int(center_y - lp.bar_height / 2)
    draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_range_stats, inter22)


    # top brawlers
    placeholder_icon = BRAWLER_ICONS['placeholder']
    num_brawlers = len(top_ladder_brawlers)
    offset_top = (lp.screen_height - footer_height - num_brawlers * brawler_icons_height - (num_brawlers - 1) * brawlers_gap) / 2
    for i in range(len(top_ladder_brawlers)):
        center_x = lp.screen_width - lp.margin - lp.bar_width - brawlers_gap - brawler_icons_height / 2
        center_y = (
            + offset_top
            + (brawler_icons_height + brawlers_gap) * i
            + 0.5 * brawler_icons_height
        )

        cur_brawler_stats = top_ladder_brawlers[i][1:]
        rank_bar_start_x = center_x + brawlers_gap + brawler_icons_height / 2
        rank_bar_start_y = int(center_y - lp.bar_height / 2)
        draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_brawler_stats, inter22)

        normalized_name = normalize_name(top_ladder_brawlers[i][0])
        cur_brawler_icon = BRAWLER_ICONS.get(normalized_name, placeholder_icon)
        icon_start_x = int(center_x - brawler_icons_height / 2)
        icon_start_y = int(center_y - brawler_icons_height / 2)
        paste_image_with_border(canvas, draw, (icon_start_x, icon_start_y), cur_brawler_icon, 4)

        cur_position = f'#{i + 1}'
        position_end_x = center_x - brawler_icons_height / 2 - brawlers_gap
        position_start_x = position_end_x - 50
        draw_text_centered(draw, (position_start_x, center_y, position_end_x, center_y), cur_position, inter42, 4)

    return canvas


async def fetch_data_for_main_ladder(tag):
    ladder_stats, ladder_stats_by_ranges, top_ladder_brawlers = await asyncio.gather(
        StatsService.get_ladder_stats(tag),
        StatsService.get_ladder_stats_by_trophy_ranges(tag),
        StatsService.get_top_ladder_brawlers(tag, lim=5),
    )

    return ladder_stats, ladder_stats_by_ranges, top_ladder_brawlers


async def create_main_ladder_img(tag, player_nickname):
    ladder_stats, ladder_stats_by_ranges, top_ladder_brawlers = await(fetch_data_for_main_ladder(tag))
    return await gen_main_ladder_img(ladder_stats, ladder_stats_by_ranges, top_ladder_brawlers, player_nickname)