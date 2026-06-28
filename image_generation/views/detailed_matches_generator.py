import asyncio
import math
from datetime import datetime, UTC

from image_generation.assets.fonts import inter30, inter30, inter66, inter20, inter36
from image_generation.assets.images import BIGGER_BRAWLER_ICONS, DARK_BG, GAME_MODE_ICONS, MODE_PLACEHOLDER, \
    RANK_ICONS_NO_DIGITS, TROPHY
from image_generation.image_utils import normalize_name, draw_text_align_to_side, draw_text_centered, \
    format_datetime_diff, paste_image_with_border, get_text_size, paste_icon_and_text, gradient_rect
from image_generation.layout_config import lp, gamemodes_colors, result_titles, result_colors
from image_generation.views.compact_matches_generator import COL_CAPACITY
from image_generation.views.template_generator import get_template
from image_generation.unicode_renderer import render_unicode
from services.stats_service import StatsService


ROW_CAPACITY = 1
COL_CAPACITY = 3


async def gen_detailed_matches_img(stats, matches, total_matches_count, player_nickname, page):
    total_games, wins, draws, losses = stats

    print(*matches[:3], sep='\n')
    print(total_games, wins, draws, losses)

    canvas, draw = await get_template(stats, player_nickname, 'total')

    num_of_pages = math.ceil(total_matches_count / (ROW_CAPACITY * COL_CAPACITY))
    border_width = 6
    inner_margin = 25  # between cards
    outer_margin = 50
    trophy_icon_text_gap = 6
    card_width = 1120
    card_height = 240
    icon_w, icon_h = BIGGER_BRAWLER_ICONS['shelly'].size
    badge_width = card_width
    badge_height = 65
    card_padding = 20
    brawlers_margin = 40
    area_outer_width = outer_margin * 2 + ROW_CAPACITY * card_width + (ROW_CAPACITY - 1) * inner_margin
    grad_height = 50
    offset_x = lp.screen_width - area_outer_width
    offset_y = int((lp.screen_height - COL_CAPACITY * card_height - (COL_CAPACITY - 1) * inner_margin) / 2)

    # blur bg
    canvas.paste(DARK_BG, (offset_x, 0), DARK_BG)

    iteration_start = 0
    iteration_end = min(len(matches), page * (ROW_CAPACITY * COL_CAPACITY) + 2 * ROW_CAPACITY)
    for rel_i in range(iteration_start, iteration_end):
        cur_player_team = None
        for p in matches[rel_i][0].players:
            if p.player_nickname == player_nickname: # todo: compare by tag, not nickname
                cur_player_team = p.team
                break
        print(f'{cur_player_team = }')
        if cur_player_team == -1:
            for p in matches[rel_i][0].players:
                p.team *= -1
        matches[rel_i][0].players.sort(
            key=lambda x: (-x.team, -int(x.player_nickname == player_nickname))
        )

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
        card_center_y = card_start_y + card_height / 2

        # badge bg
        badge_start_x = card_start_x
        badge_end_x = badge_start_x + badge_width
        badge_start_y = card_start_y
        badge_end_y = badge_start_y + badge_height
        draw.rectangle(
            (badge_start_x, badge_start_y, badge_end_x, badge_end_y),
            fill='#766A94',
        )

        # game_mode
        game_mode = matches[rel_i][0].game_mode
        normalized_mode_name = normalize_name(game_mode)
        game_mode_icon = GAME_MODE_ICONS.get(normalized_mode_name, MODE_PLACEHOLDER)
        # game_mode_icon = random.choice(list(GAME_MODE_ICONS.values()))
        game_mode_icon_start_x = int(card_start_x + card_padding)
        game_mode_icon_center_y = card_start_y + badge_height / 2
        game_mode_icon_start_y = int(game_mode_icon_center_y - game_mode_icon.height / 2)
        canvas.paste(game_mode_icon, (game_mode_icon_start_x, game_mode_icon_start_y), game_mode_icon)

        # game_map
        game_map_start_x = int(game_mode_icon_start_x + game_mode_icon.width + card_padding)
        game_map_center_y = int(badge_start_y + badge_height / 2)
        draw_text_align_to_side(
            draw,
            (game_map_start_x, game_map_center_y, game_map_start_x, game_map_center_y),
            matches[rel_i][0].game_map,
            inter30,
            4,
            gamemodes_colors.get(game_mode, '#fff'),
            'left'
        )

        # result
        result_center_x = badge_start_x + badge_width / 2
        result_center_y = badge_start_y + badge_height / 2
        result = matches[rel_i][1]
        draw_text_centered(
            draw,
            (result_center_x, result_center_y, result_center_x, result_center_y),
            result_titles[result],
            inter30,
            4,
            result_colors[result]
        )

        # time ago
        now = datetime.now(UTC).replace(tzinfo=None)
        time_diff = format_datetime_diff(now, matches[rel_i][0].match_time)
        draw_text_align_to_side(
            draw,
            (
                badge_end_x - card_padding,
                badge_start_y + badge_height / 2,
                badge_end_x - card_padding,
                badge_start_y + badge_height / 2
            ),
            time_diff,
            inter30,
            4,
            'white',
            side='right'
        )

        # card body bg
        card_body_start_x = card_start_x
        card_body_end_x = card_start_x + badge_width
        card_body_start_y = card_start_y + badge_height
        card_body_end_y = card_end_y
        draw.rectangle(
            (card_body_start_x, card_body_start_y, card_body_end_x, card_body_end_y),
            fill='#8D82A6',
        )

        # VS
        vs_center_y = (card_start_y + badge_height + card_end_y) / 2
        draw_text_centered(
            draw,
            (card_center_x, vs_center_y, card_center_x, vs_center_y),
            'VS',
            inter66,
            6
        )
        for player_n, player in enumerate(matches[rel_i][0].players):
            team = player_n // 3
            pos_in_team = player_n % 3

            if team == 0:
                team_start_x = card_start_x + card_padding
            else:
                team_start_x = card_end_x - card_padding - 3 * icon_w - 2 * brawlers_margin

            # brawler
            normalized_name = normalize_name(player.brawler)
            placeholder_icon = BIGGER_BRAWLER_ICONS['placeholder']
            brawler_icon = BIGGER_BRAWLER_ICONS.get(normalized_name, placeholder_icon)
            brawler_start_x = int(team_start_x + pos_in_team * (icon_w + brawlers_margin))
            brawler_start_y = int(card_body_start_y + card_padding)
            brawler_end_x = brawler_start_x + icon_w
            brawler_end_y = brawler_start_y + icon_w
            paste_image_with_border(canvas, draw, (brawler_start_x, brawler_start_y), brawler_icon, 4)

            # nickname
            nickname = player.player_nickname
            nickname_width, nickname_height = get_text_size(draw, nickname, inter20)
            nickname_negative_margin = 18
            nickname_start_x = int(
                brawler_start_x + icon_w / 2 - nickname_width / 2
            )
            nickname_start_y = int((brawler_start_y + icon_h + card_end_y) / 2 - nickname_height / 2)
            nickname_img = await render_unicode(
                nickname,
                color="#fff",
                font_size=20,
                outline_width=3,
                outline_color="#000",
            )
            canvas.paste(nickname_img, (nickname_start_x, nickname_start_y), nickname_img)

            if matches[rel_i][0].game_type == 'soloRanked':
                rank_family = (matches[rel_i][3] - 1) // 3 + 1
                rank_digit = (matches[rel_i][3] - 1) % 3 + 1
                rank_icon = RANK_ICONS_NO_DIGITS[rank_family]
                trophy_info_start_x = int(brawler_start_x - rank_icon.width / 2)
                trophy_info_start_y = int(brawler_start_y - rank_icon.height / 2)
                paste_icon_and_text(
                    canvas,
                    draw,
                    rank_icon,
                    'I' * rank_digit,
                    inter36,
                    trophy_icon_text_gap,
                    start_xy=(trophy_info_start_x, trophy_info_start_y)
                )
            elif matches[rel_i][0].game_type == 'ranked':
                trophy_info_start_x = int(brawler_start_x - TROPHY.width / 2)
                trophy_info_start_y = int(brawler_start_y - TROPHY.height / 2)
                paste_icon_and_text(
                    canvas,
                    draw,
                    TROPHY,
                    f'{player.trophies}',
                    inter30,
                    trophy_icon_text_gap,
                    start_xy=(trophy_info_start_x, trophy_info_start_y)
                )

            else:
                print('undefined', matches[rel_i][2])

    if page * (ROW_CAPACITY * COL_CAPACITY) <= total_matches_count:
        grad = gradient_rect((area_outer_width, grad_height))
        canvas.paste(grad, (offset_x, lp.screen_height - grad_height), grad)

    if page > 1 and (page - 1) * (ROW_CAPACITY * COL_CAPACITY) + 1 <= total_matches_count:
        grad = gradient_rect((area_outer_width, grad_height), start_alpha=255, end_alpha=0)
        canvas.paste(grad, (offset_x, 0), grad)

    return canvas, num_of_pages


async def fetch_detailed_data_for_matches(tag, page):
    limit = ROW_CAPACITY * (COL_CAPACITY + 2)
    offset = max(0, (ROW_CAPACITY * COL_CAPACITY) * (page - 1) - ROW_CAPACITY)
    overall_stats, matches_batch, total_matches_count = await asyncio.gather(
        StatsService.get_overall_stats(tag),
        StatsService.get_detailed_matches(tag, limit=limit, offset=offset),
        StatsService.count_matches(tag),
    )

    return overall_stats, matches_batch, total_matches_count


async def create_detailed_matches_img(tag, player_nickname, page):
    stats, matches_batch, total_matches_count = await(fetch_detailed_data_for_matches(tag, page))
    return await gen_detailed_matches_img(stats, matches_batch, total_matches_count, player_nickname, page)
