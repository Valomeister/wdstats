from PIL import Image, ImageDraw

from image_generation.assets.fonts import inter42, inter36
from image_generation.assets.images import CANVAS
from image_generation.image_utils import get_text_bbox, draw_text_align_to_side
from image_generation.layout_config import lp, result_colors
from image_generation.unicode_renderer import render_unicode


async def get_template(stats, player_nickname, matches_type_name):
    total_games, wins, draws, losses = stats
    print(stats)
    print(type(stats), type(stats[0]))

    profile_icon = Image.open('image_generation/assets/images/profile_icon_placeholder.jpg')
    canvas_copy = CANVAS.copy()
    canvas_copy.paste(profile_icon, (lp.margin, lp.margin))

    draw = ImageDraw.Draw(canvas_copy)

    nickname_img = await render_unicode(
        player_nickname,
        color="#fff",
        font_size=48,
        outline_width=6,
        outline_color="#000",

    )

    nickname_start_x = int(lp.margin + profile_icon.width + lp.margin / 2)
    nickname_start_y = int(lp.margin + profile_icon.height / 2 - nickname_img.height / 2)
    canvas_copy.paste(nickname_img, (nickname_start_x, nickname_start_y), nickname_img)

    # total
    total_games_text = f'{total_games} {matches_type_name} games'
    total_games_text_x = lp.margin
    total_games_text_y = lp.margin + profile_icon.height + lp.margin
    total_games_text_bbox = get_text_bbox(draw, total_games_text, inter42)
    draw.text(
        (total_games_text_x, total_games_text_y),
        total_games_text,
        fill="white",
        font=inter42,
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
        font=inter36,
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
        font=inter36,
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
        font=inter36,
        fill=result_colors[-1],
        stroke_width=4,
        side='left',
        center_y=False
    )

    return canvas_copy, draw


