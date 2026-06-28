import asyncio

from image_generation.assets.fonts import inter22, inter42
from image_generation.assets.images import DARK_BG, RANK_ICONS, BRAWLER_ICONS
from image_generation.image_utils import draw_bar, normalize_name, paste_image_with_border, draw_text_centered
from image_generation.layout_config import lp
from image_generation.views.template_generator import get_template
from services.stats_service import StatsService


async def gen_main_ranked_img(ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers, player_nickname):
    print("LOOP", id(asyncio.get_running_loop()))
    total_games, wins, draws, losses = ranked_stats
    per_rank_dict = {i[0]: i[1:] for i in ranked_stats_by_ranks}
    print(ranked_stats_by_ranks)
    print(total_games, wins, draws, losses)
    print(top_ranked_brawlers)

    canvas, draw = await get_template(ranked_stats, player_nickname, 'ranked')

    # blur bg
    canvas.paste(DARK_BG, (0, int(lp.screen_height / 2)), DARK_BG)

    # ranks
    offset_top = lp.screen_height / 2
    offset_left = lp.margin
    available_width = (lp.screen_width - lp.margin * 2 - lp.margin * 3)
    available_height = lp.screen_height / 2 - 3 * lp.margin
    group_height = available_height / 2
    item_height = group_height / 3
    brawlers_gap = 20
    brawler_icons_height = 70
    for i in RANK_ICONS:
        group_number = (i - 1) // 3
        position_in_group = (i - 1) % 3
        row_number = group_number // 4
        position_in_row = group_number % 4
        group_start_x = offset_left + (available_width / 4 + lp.margin) * position_in_row
        group_end_x = group_start_x + available_width / 4

        center_y = int(
            + offset_top
            + (available_height / 2) * row_number
            + lp.margin * (row_number + 1)
            + item_height * position_in_group
            + item_height / 2
        )
        center_x = int(
            + offset_left
            + (available_width / 4 + lp.margin) * position_in_row
            + item_height / 2
        )

        icon_start_x = int(center_x - RANK_ICONS[i].width / 2)
        icon_start_y = int(center_y - RANK_ICONS[i].height / 2)
        canvas.paste(RANK_ICONS[i], (icon_start_x, icon_start_y), RANK_ICONS[i])

        cur_rank_stats = per_rank_dict.get(i, [0, 0, 0, 0])
        rank_bar_start_x = group_end_x - lp.bar_width
        rank_bar_start_y = int(center_y - lp.bar_height / 2)
        draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_rank_stats, inter22)

    # top brawlers
    placeholder_icon = BRAWLER_ICONS['placeholder']
    num_brawlers = len(top_ranked_brawlers)
    offset_top = (lp.screen_height / 2 - num_brawlers * brawler_icons_height - (num_brawlers - 1) * brawlers_gap) / 2
    for i in range(len(top_ranked_brawlers)):
        center_x = lp.screen_width - lp.margin - lp.bar_width - brawlers_gap - brawler_icons_height / 2
        center_y = (
            + offset_top
            + (brawler_icons_height + brawlers_gap) * i
            + 0.5 * brawler_icons_height
        )

        cur_brawler_stats = top_ranked_brawlers[i][1:]
        rank_bar_start_x = center_x + brawlers_gap + brawler_icons_height / 2
        rank_bar_start_y = int(center_y - lp.bar_height / 2)
        draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_brawler_stats, inter22)

        normalized_name = normalize_name(top_ranked_brawlers[i][0])
        cur_brawler_icon = BRAWLER_ICONS.get(normalized_name, placeholder_icon)
        icon_start_x = int(center_x - brawler_icons_height / 2)
        icon_start_y = int(center_y - brawler_icons_height / 2)
        paste_image_with_border(canvas, draw, (icon_start_x, icon_start_y), cur_brawler_icon, 4)

        cur_position = f'#{i + 1}'
        position_end_x = center_x - brawler_icons_height / 2 - brawlers_gap
        position_start_x = position_end_x - 50
        draw_text_centered(draw, (position_start_x, center_y, position_end_x, center_y), cur_position, inter42, 4)

    return canvas


async def fetch_data_for_main_ranked(tag):
    ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers = await asyncio.gather(
        StatsService.get_ranked_stats(tag),
        StatsService.get_ranked_stats_by_ranks(tag),
        StatsService.get_top_ranked_brawlers(tag, lim=5),
    )

    return ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers


async def create_main_ranked_img(tag, player_nickname):
    print("LOOP", id(asyncio.get_running_loop()))
    ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers = await(fetch_data_for_main_ranked(tag))
    return await gen_main_ranked_img(ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers, player_nickname)