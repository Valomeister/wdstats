from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import asyncio

from db.session import SessionLocal
from repositories.stats_repository import StatsRepository


def get_text_bbox(draw, text, font):
    return draw.textbbox(
        (0, 0),
        text,
        font=font
    )

def get_text_size(draw, text, font):
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    # w, h
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_text_centered(draw, box, text, font, stroke_width, center_x=True, center_y=True):
    x1, y1, x2, y2 = get_text_bbox(draw, text, font)

    text_w = x2 - x1
    text_h = y2 - y1

    if center_x:
        text_x = (box[0] + box[2]) / 2 - text_w / 2 - x1
    else:
        text_x = box[0] - x1

    if center_y:
        text_y = (box[1] + box[3]) / 2 - text_h / 2 - y1
    else:
        text_y = box[1] - y1

    draw.text(
        (text_x, text_y),
        text,
        fill="white",
        font=font,
        stroke_width=stroke_width,
        stroke_fill="black"
    )

def draw_rounded_rect(draw, box, color, radius, round_left: bool = False, round_right: bool = False):
    pos, w, h = (box[0], box[1]), box[2] - box[0], box[3] - box[1]
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=color
    )
    if round_left:
        draw.rounded_rectangle(
            (pos[0], pos[1], pos[0] + min(radius, w / 2), pos[1] + h),
            fill=color
        )
    if round_right:
        draw.rounded_rectangle(
            (pos[0] + w - min(radius, w / 2), pos[1], pos[0] + w, pos[1] + h),
            fill=color
        )

def draw_bar_segment(draw, box, bg_color, border_radius, round_left, round_right, text, font, stroke_width):
    draw_rounded_rect(
        draw,
        box,
        bg_color,
        border_radius,
        round_left,
        round_right
    )
    draw_text_centered(
        draw,
        box,
        text,
        font,
        stroke_width=stroke_width,
        center_x=True,
        center_y=True
    )


def draw_bar(draw, pos, total_games, wins, draws, losses, font):
    bar_inner_width = lp.bar_width - lp.bar_border_width * 2
    bar_inner_height = lp.bar_height - lp.bar_border_width * 2
    inner_pos = (pos[0] + lp.bar_border_width, pos[1] + lp.bar_border_width)

    # 4 is the widest digit. the preserved space has to be both uniform and sufficiently large
    draws_min_w = get_text_size(draw, "4" * len(str(draws)), font)[0] + lp.padding_for_numbers * 2
    wins_min_w = get_text_size(draw, "4" * len(str(wins)), font)[0] + lp.padding_for_numbers * 2
    losses_min_w = get_text_size(draw, "4" * len(str(losses)), font)[0] + lp.padding_for_numbers * 2

    draws_bar_width = draws_min_w if draws else 0
    wins_bar_width = wins_min_w if wins else 0
    losses_bar_width = losses_min_w if losses else 0

    free_inner_width = bar_inner_width - (draws_bar_width + wins_bar_width + losses_bar_width)

    if total_games:
        draws_bar_width += free_inner_width * (draws / total_games)
        wins_bar_width += free_inner_width * (wins / total_games)
        losses_bar_width += free_inner_width * (losses / total_games)

    if wins:
        draw_bar_segment(
            draw,
            (inner_pos[0], inner_pos[1], inner_pos[0] + wins_bar_width, inner_pos[1] + bar_inner_height),
            "#67B000",
            lp.inner_border_radius,
            round_left=False,
            round_right=draws or losses,
            text=f'{wins}',
            font=font,
            stroke_width=lp.bar_stroke_width,
        )

    if draws:
        draw_bar_segment(
            draw,
            (
                inner_pos[0] + wins_bar_width,
                inner_pos[1],
                inner_pos[0] + wins_bar_width + draws_bar_width,
                inner_pos[1] + bar_inner_height
            ),
            "#F3D600",
            lp.inner_border_radius,
            round_left=wins > 0,
            round_right=losses > 0,
            text=f'{draws}',
            font=font,
            stroke_width=lp.bar_stroke_width,
        )
    if losses:
        draw_bar_segment(
            draw,
            (
                inner_pos[0] + bar_inner_width - losses_bar_width,
                inner_pos[1],
                inner_pos[0] + bar_inner_width,
                inner_pos[1] + bar_inner_height
            ),
            "#E62727",
            lp.inner_border_radius,
            round_left=wins or draws,
            round_right=False,
            text=f'{losses}',
            font=font,
            stroke_width=lp.bar_stroke_width,
        )
    if not any([wins, draws, losses]):
        draw_bar_segment(
            draw,
            (
                inner_pos[0],
                inner_pos[1],
                inner_pos[0] + bar_inner_width,
                inner_pos[1] + bar_inner_height
            ),
            "#D0D0D0",
            lp.inner_border_radius,
            round_left=True,
            round_right=True,
            text='0',
            font=font,
            stroke_width=lp.bar_stroke_width,
        )
    # draw outer border
    draw.rounded_rectangle(
        (
            pos[0],
            pos[1],
            pos[0] + lp.bar_width,
            pos[1] + lp.bar_height
        ),
        radius=lp.outer_border_radius,
        outline="#000000",
        width=lp.bar_border_width
        )
    # draw inner borders
    if wins and (draws or losses):
        draw.rectangle(
            (
                inner_pos[0] + wins_bar_width - lp.inner_border_width / 2,
                inner_pos[1],
                inner_pos[0] + wins_bar_width + lp.inner_border_width / 2,
                inner_pos[1] + bar_inner_height
            ),
            fill="#000000"
        )
    if draws and losses:
        draw.rectangle(
            (
                inner_pos[0] + bar_inner_width - losses_bar_width - lp.inner_border_width / 2,
                inner_pos[1],
                inner_pos[0] + bar_inner_width - losses_bar_width + lp.inner_border_width / 2,
                inner_pos[1] + bar_inner_height
            ),
            fill="#000000"
        )

def load_ranked_ranks(folder_path, height):
    ranked_icons = {}
    for rank in range(1, 23):
        filename = f'{folder_path}{rank}.png'
        img = Image.open(filename)
        initial_w, initial_h = img.size
        target_h = height
        target_w = int(initial_w / initial_h * target_h)
        ranked_icons[rank] = img.resize((target_w, target_h)).convert('RGBA')

    return ranked_icons

def load_brawler_icons(folder_path):
    icons = {}
    for file in Path(folder_path).iterdir():
        if file.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            img = Image.open(file).resize((lp.brawler_icons_height, lp.brawler_icons_height))
            brawler_name = file.name[:file.name.index('.')]
            icons[brawler_name] = img

    return icons

def normalize_name(name):
    return name.lower().replace(' ', '_').replace('-', '_')

async def gen_image():
    session = SessionLocal()
    stats_repo = StatsRepository(session)
    tag = '#L2YQPPG'
    player_nickname = 'HMB|ℝĭ̈𝘤𝓴ꪗツ'

    total_games, wins, draws, losses = await stats_repo.get_ranked_stats(tag)
    per_rank = await stats_repo.get_ranked_stats_by_ranks(tag)
    per_rank_dict = {i[0]: i[1:] for i in per_rank}
    top_brawlers = await stats_repo.get_top_ranked_brawlers(tag, lim=5)
    print(per_rank)
    print(total_games, wins, draws, losses)
    print(top_brawlers)
    await session.close()

    canvas = Image.open('images/bg.jpg')

    profile_icon = Image.open('images/profile_icon_placeholder.jpg')
    canvas.paste(profile_icon, (lp.margin, lp.margin))

    draw = ImageDraw.Draw(canvas)

    nickname_font = ImageFont.truetype(
        "fonts/Inter_18pt-Bold.ttf",
        48
    )

    stats_font = ImageFont.truetype(
        "fonts/Inter_18pt-Bold.ttf",
        42
    )

    bar_font = ImageFont.truetype(
        "fonts/Inter_18pt-Bold.ttf",
        22
    )

    # nickname
    draw_text_centered(
        draw,
        [
            lp.margin + profile_icon.width + lp.margin,
            lp.margin,
            lp.margin + profile_icon.width + lp.margin,
            lp.margin + profile_icon.height
        ],
        player_nickname,
        nickname_font,
        4,
        center_x=False,
        center_y=True
    )

    # total
    total_games_text = f'{total_games} ranked games'
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

    # total bar
    total_bar_x = lp.margin
    total_bar_y = total_games_text_y + total_games_text_bbox[3] + lp.margin
    draw_bar(draw, (total_bar_x, total_bar_y), total_games, wins, draws, losses, bar_font)

    # blur bg
    dark_bg = Image.open('images/dark_rect.png').convert('RGBA')
    alpha = dark_bg.getchannel('A')
    alpha = alpha.point(lambda p: p * 0.7)
    dark_bg.putalpha(alpha)
    canvas.paste(dark_bg, (0, int(lp.screen_height / 2)), dark_bg)

    # ranks
    rank_icons = load_ranked_ranks('images/ranked_ranks/', height=lp.ranked_icons_height)
    offset_top = lp.screen_height / 2
    offset_left = lp.margin
    available_width = (lp.screen_width - lp.margin * 2 - lp.margin * 3)
    available_height = lp.screen_height / 2 - 3 * lp.margin
    group_height = available_height / 2
    item_height = group_height / 3
    for i in rank_icons:
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

        icon_start_x = int(center_x - rank_icons[i].width / 2)
        icon_start_y = int(center_y - rank_icons[i].height / 2)
        canvas.paste(rank_icons[i], (icon_start_x, icon_start_y), rank_icons[i])

        cur_rank_stats = per_rank_dict.get(i, [0, 0, 0, 0])
        rank_bar_start_x = group_end_x - lp.bar_width
        rank_bar_start_y = int(center_y - lp.bar_height / 2)
        draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_rank_stats, bar_font)

        # draw.circle((center_x, center_y), radius=5, fill="white", outline="black", width=3)
        # draw.circle(((group_start_x + group_end_x - lp.bar_width) / 2, center_y), radius=5, fill="white", outline="black", width=3)
        # draw.circle((
        #     group_start_x,
        #     center_y
        # ), radius=5, fill="red", outline="black", width=3)
        # draw.circle((
        #     group_end_x,
        #     center_y
        # ), radius=5, fill="red", outline="black", width=3)

    # top brawlers
    brawler_icons = load_brawler_icons('images/brawler_icons')
    placeholder_icon = brawler_icons['placeholder']
    num_brawlers = len(top_brawlers)
    offset_top = (lp.screen_height / 2 - num_brawlers * lp.brawler_icons_height - (num_brawlers - 1) * lp.brawlers_gap) / 2
    for i in range(len(top_brawlers)):
        center_x = lp.screen_width - lp.margin - lp.bar_width - lp.brawlers_gap - lp.brawler_icons_height / 2
        center_y = (
            + offset_top
            + (lp.brawler_icons_height + lp.brawlers_gap) * i
            + 0.5 * lp.brawler_icons_height
        )

        cur_brawler_stats = top_brawlers[i][1:]
        rank_bar_start_x = center_x + lp.brawlers_gap + lp.brawler_icons_height / 2
        rank_bar_start_y = int(center_y - lp.bar_height / 2)
        draw_bar(draw, (rank_bar_start_x, rank_bar_start_y), *cur_brawler_stats, bar_font)

        normalized_name = normalize_name(top_brawlers[i][0])
        cur_brawler_icon = brawler_icons.get(normalized_name, placeholder_icon)
        icon_start_x = int(center_x - lp.brawler_icons_height / 2)
        icon_start_y = int(center_y - lp.brawler_icons_height / 2)
        brawler_icon_border_width = 4
        draw.rectangle(
            (
                icon_start_x - brawler_icon_border_width,
                icon_start_y - brawler_icon_border_width,
                icon_start_x + lp.brawler_icons_height + brawler_icon_border_width - 1,
                icon_start_y + lp.brawler_icons_height + brawler_icon_border_width - 1,
            ),
            outline='black',
            width=brawler_icon_border_width
        )
        canvas.paste(cur_brawler_icon, (icon_start_x, icon_start_y))

        cur_position = f'#{i + 1}'
        position_end_x = center_x - lp.brawler_icons_height / 2 - lp.brawlers_gap
        position_start_x = position_end_x - 50
        draw_text_centered(draw, (position_start_x, center_y, position_end_x, center_y), cur_position, stats_font, 4)

        # draw.circle((center_x, center_y - lp.brawler_icons_height / 2), radius=5, fill="red", outline="black", width=3)
        # draw.circle((rank_bar_start_x, center_y), radius=5, fill="white", outline="black", width=3)
        # draw.circle((center_x, center_y + lp.brawler_icons_height / 2), radius=5, fill="red", outline="black", width=3)
        # draw.circle((position_end_x, center_y), radius=5, fill="white", outline="black", width=3)

    canvas.show()

class DotDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

layout_params = lp = DotDict({
    # canvas
    "screen_width": 1920,
    "screen_height": 1080,

    # spacing
    "margin": 50,
    "brawlers_gap": 20,

    # icons
    "ranked_icons_height": 60,
    "brawler_icons_height": 70,

    # bar
    "bar_width": 330,
    "bar_height": 50,
    "bar_border_width": 6,

    # borders
    "inner_border_width": 4,

    # radius
    "outer_border_radius": 20,
    "inner_border_radius": 10,

    # text
    "padding_for_numbers": 6,
    "bar_stroke_width": 2,


})

asyncio.run(gen_image())