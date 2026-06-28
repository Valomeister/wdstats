import asyncio

from image_generation.assets.fonts import inter22, inter42
from image_generation.assets.images import DARK_BG, GAME_MODE_ICONS, SMALLER_BRAWLER_ICONS
from image_generation.image_utils import draw_bar, normalize_name, draw_text_centered, paste_image_with_border
from image_generation.layout_config import lp, REQUIRED_MODES, gamemodes_colors
from image_generation.views.template_generator import get_template
from services.stats_service import StatsService


async def gen_ranked_img_by_mode(ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes, player_nickname):
    total_games, wins, draws, losses = ranked_stats

    print(ranked_stats_by_modes)
    print(total_games, wins, draws, losses)
    print(top_ranked_brawlers_by_modes)

    canvas, draw = await get_template(ranked_stats, player_nickname, 'ranked')

    cards_inner_horizontal_margin = 20
    cards_outer_margin = 20
    mode_icons_height = GAME_MODE_ICONS['brawlball'].height
    modes_card_width = lp.bar_width + mode_icons_height * 2 + 4 * cards_inner_horizontal_margin
    modes_card_height = (lp.screen_height - 2 * lp.margin - 2 * cards_outer_margin) / 3
    modes_area_width = 2 * modes_card_width + 2 * lp.margin + cards_outer_margin
    modes_offset_x = lp.screen_width - modes_area_width
    card_row_height = modes_card_height / 4

    # blur bg
    canvas.paste(DARK_BG, (modes_offset_x, 0), DARK_BG)

    for i in range(6):
        row = i // 2
        col = i % 2
        center_x = (
            + modes_offset_x
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

        game_mode = sorted(REQUIRED_MODES)[i]
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
        mode_stats = ranked_stats_by_modes[game_mode]
        draw_bar(draw, (bar_start_x, bar_start_y), *mode_stats, inter22)

        # game_mode icon
        normalized_mode_name = normalize_name(game_mode)
        game_mode_icon = GAME_MODE_ICONS[normalized_mode_name]
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
            normalized_brawler_name = normalize_name(top_ranked_brawlers_by_modes[game_mode][j][0])
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
            mode_stats = top_ranked_brawlers_by_modes[game_mode][j][1:-1]
            draw_bar(draw, (brawler_bar_start_x, brawler_bar_start_y), *mode_stats, inter22)


    return canvas


async def fetch_data_for_ranked_by_mode(tag):
    ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes = await asyncio.gather(
        StatsService.get_ranked_stats(tag),
        StatsService.get_ranked_stats_by_modes(tag),
        StatsService.get_top_ranked_brawlers_by_modes(tag),
    )

    return ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes


async def create_ranked_img_by_mode(tag, player_nickname):
    ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes = await(fetch_data_for_ranked_by_mode(tag))
    return await gen_ranked_img_by_mode(ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes, player_nickname)