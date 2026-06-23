from datetime import datetime, UTC
import math
import random
import time
import asyncio

from PIL import Image, ImageDraw, ImageFont

from services.image_generation.config import (
    lp,
    nickname_font, stats_font, bar_font, smaller_stats_font, time_ago_font,
    badge_font, gamemodes_colors, result_colors,
)
from services.image_generation.db_utils import (
    fetch_data_for_main_ranked, fetch_data_for_ranked_by_modes,
    REQUIRED_MODES, fetch_data_for_ranked_by_brawlers, fetch_data_for_matches
)

from services.image_generation.image_utils import (
    load_brawler_icons,
    load_ranked_ranks,
    load_game_mode_icons,
    normalize_name,
    get_text_bbox,
    draw_text_centered,
    draw_bar,
    paste_image_with_border,
    round_img,
    draw_text_align_to_side,
    gradient_rect,
    get_text_size,
    format_datetime_diff,
    paste_icon_and_text
)


def get_template(stats, player_nickname, matches_type_name):
    total_games, wins, draws, losses = stats

    profile_icon = Image.open('services/image_generation/images/profile_icon_placeholder.jpg')
    canvas_copy = CANVAS.copy()
    canvas_copy.paste(profile_icon, (lp.margin, lp.margin))

    draw = ImageDraw.Draw(canvas_copy)

    # nickname
    draw_text_centered(
        draw,
        [
            lp.margin + profile_icon.width + lp.margin / 2,
            lp.margin,
            lp.margin + profile_icon.width + lp.margin / 2,
            lp.margin + profile_icon.height
        ],
        player_nickname,
        nickname_font,
        4,
        center_x=False,
        center_y=True
    )

    # total
    total_games_text = f'{total_games} {matches_type_name} games'
    total_games_text_x = lp.margin
    total_games_text_y = lp.margin + profile_icon.height + lp.margin
    total_games_text_bbox = get_text_bbox(draw, total_games_text, stats_font)
    draw.text(
        (total_games_text_x, total_games_text_y),
        total_games_text,
        fill="white",
        font=stats_font,
        stroke_width=4,
        stroke_fill="black"
    )

    # stats
    gap = 20
    stats_start_x = lp.margin + gap
    stats_start_y = total_games_text_y + total_games_text_bbox[3] + gap

    wins_w, wins_h = draw_text_align_to_side(
        draw,
        (stats_start_x, stats_start_y, stats_start_x, stats_start_y),
        text=f'{wins} wins  ',
        font=smaller_stats_font,
        fill=result_colors[1],
        stroke_width=4,
        side='left',
        center_y=False
    )
    draw_text_align_to_side(
        draw,
        (stats_start_x, stats_start_y + gap + wins_h,
         stats_start_x, stats_start_y + gap + wins_h),
        text=f'{draws} draws  ',
        font=smaller_stats_font,
        fill=result_colors[0],
        stroke_width=4,
        side='left',
        center_y=False
    )
    draw_text_align_to_side(
        draw,
        (stats_start_x, stats_start_y + 2 * (gap + wins_h),
         stats_start_x, stats_start_y + 2 * (gap + wins_h)),
        text=f'{losses} losses',
        font=smaller_stats_font,
        fill=result_colors[-1],
        stroke_width=4,
        side='left',
        center_y=False
    )

    return canvas_copy, draw

async def gen_main_ranked_img(ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers, player_nickname):
    total_games, wins, draws, losses = ranked_stats
    per_rank_dict = {i[0]: i[1:] for i in ranked_stats_by_ranks}
    print(ranked_stats_by_ranks)
    print(total_games, wins, draws, losses)
    print(top_ranked_brawlers)

    canvas, draw = get_template(ranked_stats, player_nickname, 'ranked')

    # blur bg
    canvas.paste(DARK_BG, (0, int(lp.screen_height / 2)), DARK_BG)

    # ranks
    offset_top = lp.screen_height / 2
    offset_left = lp.margin
    available_width = (lp.screen_width - lp.margin * 2 - lp.margin * 3)
    available_height = lp.screen_height / 2 - 3 * lp.margin
    group_height = available_height / 2
    item_height = group_height / 3
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
        draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_rank_stats, bar_font)

    # top brawlers
    placeholder_icon = BRAWLER_ICONS['placeholder']
    num_brawlers = len(top_ranked_brawlers)
    offset_top = (lp.screen_height / 2 - num_brawlers * lp.brawler_icons_height - (num_brawlers - 1) * lp.brawlers_gap) / 2
    for i in range(len(top_ranked_brawlers)):
        center_x = lp.screen_width - lp.margin - lp.bar_width - lp.brawlers_gap - lp.brawler_icons_height / 2
        center_y = (
            + offset_top
            + (lp.brawler_icons_height + lp.brawlers_gap) * i
            + 0.5 * lp.brawler_icons_height
        )

        cur_brawler_stats = top_ranked_brawlers[i][1:]
        rank_bar_start_x = center_x + lp.brawlers_gap + lp.brawler_icons_height / 2
        rank_bar_start_y = int(center_y - lp.bar_height / 2)
        draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_brawler_stats, bar_font)

        normalized_name = normalize_name(top_ranked_brawlers[i][0])
        cur_brawler_icon = BRAWLER_ICONS.get(normalized_name, placeholder_icon)
        icon_start_x = int(center_x - lp.brawler_icons_height / 2)
        icon_start_y = int(center_y - lp.brawler_icons_height / 2)
        paste_image_with_border(canvas, draw, (icon_start_x, icon_start_y), cur_brawler_icon, 4)

        cur_position = f'#{i + 1}'
        position_end_x = center_x - lp.brawler_icons_height / 2 - lp.brawlers_gap
        position_start_x = position_end_x - 50
        draw_text_centered(draw, (position_start_x, center_y, position_end_x, center_y), cur_position, stats_font, 4)

    return canvas

async def gen_ranked_img_by_modes(ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes, player_nickname):
    total_games, wins, draws, losses = ranked_stats

    print(ranked_stats_by_modes)
    print(total_games, wins, draws, losses)
    print(top_ranked_brawlers_by_modes)

    canvas, draw = get_template(ranked_stats, player_nickname, 'ranked')

    cards_inner_horizontal_margin = 20
    cards_outer_margin = 20
    modes_card_width = lp.bar_width + lp.mode_icons_height * 2 + 4 * cards_inner_horizontal_margin
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
        game_mode_color = gamemodes_colors[game_mode]

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
        draw_bar(draw, (bar_start_x, bar_start_y), *mode_stats, bar_font)

        # game_mode icon
        normalized_mode_name = normalize_name(game_mode)
        game_mode_icon = GAME_MODE_ICONS[normalized_mode_name]
        mode_icon_start_x = int(card_start_x + cards_inner_horizontal_margin)
        mode_icon_center_y = card_start_y + card_row_height / 2
        mode_icon_start_y = int(mode_icon_center_y - lp.mode_icons_height / 2)
        canvas.paste(game_mode_icon, (mode_icon_start_x, mode_icon_start_y), game_mode_icon)

        # top-3 brawlers
        for j in range(3):
            # position (#1 / #2 / #2)
            position_start_x = int(card_start_x + cards_inner_horizontal_margin)
            position_center_y = card_start_y + card_row_height / 2 + card_row_height * (j + 1)
            position_start_y = position_center_y - lp.mode_icons_height / 2
            position_end_x = position_start_x + lp.mode_icons_height
            position_end_y = position_start_y + lp.mode_icons_height
            draw_text_centered(
                draw,
                (position_start_x, position_start_y, position_end_x, position_end_y),
                f'#{j + 1}',
                stats_font,
                4
            )

            # brawler
            placeholder_icon = SMALLER_BRAWLER_ICONS['placeholder']
            normalized_brawler_name = normalize_name(top_ranked_brawlers_by_modes[game_mode][j][0])
            brawler_icon = SMALLER_BRAWLER_ICONS.get(normalized_brawler_name, placeholder_icon)
            brawler_start_x = int(card_start_x + cards_inner_horizontal_margin + lp.mode_icons_height + cards_inner_horizontal_margin)
            brawler_center_y = card_start_y + card_row_height / 2 + card_row_height * (j + 1)
            brawler_start_y = int(brawler_center_y - lp.mode_icons_height / 2)
            brawler_end_x = brawler_start_x + lp.mode_icons_height
            brawler_end_y = brawler_start_y + lp.mode_icons_height
            paste_image_with_border(canvas, draw, (brawler_start_x, brawler_start_y), brawler_icon, 5)

            # bar
            brawler_bar_start_x = card_end_x - cards_inner_horizontal_margin - lp.bar_width
            brawler_bar_center_y = card_start_y + card_row_height / 2 + card_row_height * (j + 1)
            brawler_bar_start_y = brawler_bar_center_y - lp.bar_height / 2
            mode_stats = top_ranked_brawlers_by_modes[game_mode][j][1:-1]
            draw_bar(draw, (brawler_bar_start_x, brawler_bar_start_y), *mode_stats, bar_font)


    return canvas


async def gen_ranked_img_by_brawlers(ranked_stats, top_ranked_brawlers, player_nickname, page):
    # top_ranked_brawlers = (top_ranked_brawlers * (150 // len(top_ranked_brawlers)))[:104] # for tests
    total_games, wins, draws, losses = ranked_stats

    print(top_ranked_brawlers)
    print(total_games, wins, draws, losses)

    canvas, draw = get_template(ranked_stats, player_nickname, 'ranked')

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
            badge_font,
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
            badge_font,
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
            badge_font,
            fill=result_colors[1],
            stroke_width=4,
            side='left'
        )
        losses_w, losses_h = draw_text_align_to_side(
            draw,
            (badge_start_x, percentage_center_y, badge_end_x, percentage_center_y),
            f'{loss_percent}%',
            badge_font,
            fill=result_colors[-1],
            stroke_width=4,
            side='right'
        )
        draw_text_centered(
            draw,
            (badge_start_x + wins_w, percentage_center_y, badge_end_x - losses_w, percentage_center_y),
            f'{draw_percent}%',
            badge_font,
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


async def gen_matches_img(stats, matches, player_nickname, page):
    # top_ranked_brawlers = (top_ranked_brawlers * (150 // len(top_ranked_brawlers)))[:104] # for tests
    total_games, wins, draws, losses = stats

    print(*matches[:10], sep='\n')
    print(total_games, wins, draws, losses)

    canvas, draw = get_template(stats, player_nickname, 'total')

    row_capacity = 4
    col_capacity = 5
    num_of_pages = math.ceil(len(matches) / (row_capacity * col_capacity))
    border_width = 6
    inner_margin = 8  # between cards
    outer_margin = 40
    trophy_icon_text_gap = 6
    card_width = 290
    card_height = 180
    icon_w, icon_h = PARTIALLY_ROUNDED_BRAWLER_ICONS['shelly'].width, PARTIALLY_ROUNDED_BRAWLER_ICONS['shelly'].height
    badge_width = card_width
    badge_height = card_height - icon_h
    area_outer_width = outer_margin * 2 + row_capacity * card_width + (row_capacity - 1) * inner_margin
    grad_height = 50
    offset_x = lp.screen_width - area_outer_width
    offset_y = int((lp.screen_height - col_capacity * card_height - (col_capacity - 1) * inner_margin) / 2)

    # blur bg
    canvas.paste(DARK_BG, (offset_x, 0), DARK_BG)

    iteration_start = (page - 1) * (row_capacity * col_capacity) - row_capacity
    iteration_end = min(len(matches), page * (row_capacity * col_capacity) + row_capacity)
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
        game_mode = matches[abs_i][1]
        normalized_mode_name = normalize_name(game_mode)
        game_mode_icon = GAME_MODE_ICONS.get(normalized_mode_name, MODE_PLACEHOLDER)
        # game_mode_icon = random.choice(list(GAME_MODE_ICONS.values()))
        game_mode_icon_start_x = int(card_start_x + (badge_height - game_mode_icon.height) / 2)
        game_mode_icon_center_y = card_start_y + badge_height / 2
        game_mode_icon_start_y = int(game_mode_icon_center_y - game_mode_icon.height / 2)
        canvas.paste(game_mode_icon, (game_mode_icon_start_x, game_mode_icon_start_y), game_mode_icon)

        # brawler
        normalized_name = normalize_name(matches[abs_i][6])
        placeholder_icon = PARTIALLY_ROUNDED_BRAWLER_ICONS['placeholder']
        brawler_icon = PARTIALLY_ROUNDED_BRAWLER_ICONS.get(normalized_name, placeholder_icon)
        brawler_start_x = int(card_start_x)
        brawler_start_y = int(card_start_y + badge_height)
        brawler_end_x = brawler_start_x + brawler_icon.width
        brawler_end_y = brawler_start_y + brawler_icon.height
        canvas.paste(brawler_icon, (brawler_start_x, brawler_start_y), brawler_icon)

        # result color
        result = matches[abs_i][4]
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
        time_diff = format_datetime_diff(now, matches[abs_i][0])
        draw_text_align_to_side(
            draw,
            (
                badge_end_x - int((badge_height - game_mode_icon.height) / 2),
                badge_start_y + badge_height / 2,
                badge_end_x - int((badge_height - game_mode_icon.height) / 2),
                badge_start_y + badge_height / 2
            ),
            time_diff,
            time_ago_font,
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

        if matches[abs_i][2] == 'soloRanked':
            rank_family = (matches[abs_i][5] - 1) // 3 + 1
            rank_digit = (matches[abs_i][5] - 1) % 3 + 1
            rank_icon = RANK_ICONS_NO_DIGITS[rank_family]
            trophy_info_center_x = (card_end_x + card_start_x + icon_w) / 2
            trophy_info_center_y = (card_end_y + card_start_y + badge_height) / 2
            paste_icon_and_text(
                canvas,
                draw,
                (trophy_info_center_x, trophy_info_center_y),
                rank_icon,
                'I' * rank_digit,
                smaller_stats_font,
                trophy_icon_text_gap)

        elif matches[abs_i][2] == 'ranked':
            trophy_info_center_x = (card_end_x + card_start_x + icon_w) / 2
            trophy_info_center_y = (card_end_y + card_start_y + badge_height) / 2
            paste_icon_and_text(
                canvas,
                draw,
                (trophy_info_center_x, trophy_info_center_y),
                TROPHY,
                str(matches[abs_i][5]),
                smaller_stats_font,
                trophy_icon_text_gap)

        else:
            print('undefined', matches[abs_i][2])

    if page * (row_capacity * col_capacity) <= len(matches):
        grad = gradient_rect((area_outer_width, grad_height))
        canvas.paste(grad, (offset_x, lp.screen_height - grad_height), grad)

    if page > 1 and (page - 1) * (row_capacity * col_capacity) + 1 <= len(matches):
        grad = gradient_rect((area_outer_width, grad_height), start_alpha=255, end_alpha=0)
        canvas.paste(grad, (offset_x, 0), grad)

    return canvas, num_of_pages


async def create_main_ranked_img(tag, player_nickname):
    ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers = await(fetch_data_for_main_ranked(tag))
    return await gen_main_ranked_img(ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers, player_nickname)

async def create_ranked_img_by_modes(tag, player_nickname):
    ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes = await(fetch_data_for_ranked_by_modes(tag))
    return await gen_ranked_img_by_modes(ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes, player_nickname)

async def create_ranked_img_by_brawlers(tag, player_nickname, page):
    ranked_stats, top_ranked_brawlers = await(fetch_data_for_ranked_by_brawlers(tag))
    return await gen_ranked_img_by_brawlers(ranked_stats, top_ranked_brawlers, player_nickname, page)

async def create_matches_img(tag, player_nickname, page):
    stats, matches = await(fetch_data_for_matches(tag))
    return await gen_matches_img(stats, matches, player_nickname, page)



async def main():
    tag = '#2RJUQQ0Q8Y'
    # tag = '#9JQ888Y8U'
    # tag = '#VC9QCRUYC'
    # tag = '#2ULGU8UQG0'
    # tag = '#2V0UL0GQV8'
    player_nickname = 'HMB|ℝĭ̈𝘤𝓴ꪗツ'

    start = time.time()
    # img_ = await create_main_ranked_img(tag, player_nickname)
    # img_ = await create_ranked_img_by_modes(tag, player_nickname)
    # img_, _ = await create_ranked_img_by_brawlers(tag, player_nickname, 1)
    img_, _ = await create_matches_img(tag, player_nickname, 3)
    img_.show()
    print(time.time() - start)

CANVAS = Image.open('services/image_generation/images/bg.jpg')
BRAWLER_ICONS = load_brawler_icons('services/image_generation/images/brawler_icons')
SMALLER_BRAWLER_ICONS = {
    brawler: img.resize((lp.mode_icons_height, lp.mode_icons_height))
    for brawler, img in BRAWLER_ICONS.items()
}
ROUNDED_BRAWLER_ICONS = {
    brawler: round_img(img, 18, (88, 88))
    for brawler, img in BRAWLER_ICONS.items()
}
PARTIALLY_ROUNDED_BRAWLER_ICONS = {
    brawler: round_img(img, 18, (100, 100), (False, False, False, True))
    for brawler, img in BRAWLER_ICONS.items()
}
RANK_ICONS = load_ranked_ranks(
    'services/image_generation/images/ranked_ranks/', up_to=22, height=lp.ranked_icons_height)
RANK_ICONS_NO_DIGITS = load_ranked_ranks(
    'services/image_generation/images/ranked_ranks_no_digits/', up_to=8, height=50
)
GAME_MODE_ICONS = load_game_mode_icons('services/image_generation/images/mode_icons')
DARK_BG = Image.open('services/image_generation/images/dark_rect.png').convert('RGBA')
alpha = DARK_BG.getchannel('A')
alpha = alpha.point(lambda p: p * 0.7)
DARK_BG.putalpha(alpha)
TROPHY = Image.open('services/image_generation/images/trophy.png').convert('RGBA')
MODE_PLACEHOLDER = (Image.open('services/image_generation/images/mode_icons/placeholder.png')
                    .convert('RGBA')
                    .resize((lp.mode_icons_height, lp.mode_icons_height)))


if __name__ == '__main__':
    asyncio.run(main())
