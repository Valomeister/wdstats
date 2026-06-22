from pathlib import Path

from PIL import Image, ImageDraw

from services.image_generation.config import lp


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

def draw_text_centered(draw, box, text, font, stroke_width, fill='white', center_x=True, center_y=True):
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
        fill=fill,
        font=font,
        stroke_width=stroke_width,
        stroke_fill="black"
    )

    return text_w, text_h

def draw_text_align_to_side(draw, box, text, font, stroke_width, fill, side, center_y=True):
    x1, y1, x2, y2 = get_text_bbox(draw, text, font)

    text_w = x2 - x1
    text_h = y2 - y1

    if center_y:
        text_y = (box[1] + box[3]) / 2 - text_h / 2 - y1
    else:
        text_y = box[1] - y1

    if side == 'right':
        text_x = box[2] - text_w
    else:
        text_x = box[0]

    draw.text(
        (text_x, text_y),
        text,
        fill=fill,
        font=font,
        stroke_width=stroke_width,
        stroke_fill="black"
    )

    return text_w, text_h

def draw_bar_segment(draw, box, bg_color, border_radius, round_left, round_right, text, font, stroke_width):
    draw.rounded_rectangle(
        box,
        radius=border_radius,
        fill=bg_color,
        corners=(round_left, round_right, round_right, round_left)
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
            round_left=True,
            round_right=not draws and not losses,
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
            round_left=wins == 0,
            round_right=losses == 0,
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
            round_left=not wins and not draws,
            round_right=True,
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
                inner_pos[1] + bar_inner_height + 2
            ),
            fill="#000000"
        )
    if draws and losses:
        draw.rectangle(
            (
                inner_pos[0] + bar_inner_width - losses_bar_width - lp.inner_border_width / 2,
                inner_pos[1],
                inner_pos[0] + bar_inner_width - losses_bar_width + lp.inner_border_width / 2,
                inner_pos[1] + bar_inner_height + 2
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

def load_game_mode_icons(folder_path):
    icons = {}
    for file in Path(folder_path).iterdir():
        if file.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            img = Image.open(file)
            initial_w, initial_h = img.size
            target_h = lp.mode_icons_height
            target_w = int(initial_w / initial_h * target_h)
            mode_name = file.name[:file.name.index('.')]
            icons[mode_name] = img.resize((target_w, target_h)).convert('RGBA')

    return icons

def normalize_name(name):
    return name.lower().replace(' ', '_').replace('-', '_')

def paste_image_with_border(canvas, draw, pos, img, brawler_icon_border_width):
    w, h = img.size
    draw.rectangle(
        (
            pos[0] - brawler_icon_border_width,
            pos[1] - brawler_icon_border_width,
            pos[0] + w + brawler_icon_border_width - 1,
            pos[1] + h + brawler_icon_border_width - 1,
        ),
        outline='black',
        width=brawler_icon_border_width
    )
    canvas.paste(img, (pos[0], pos[1]))


def round_img(img, radius, size=None):
    img = img.convert("RGBA")

    if size:
        img = img.resize(size, Image.LANCZOS)

    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)

    draw.rounded_rectangle(
        (0, 0, img.width, img.height),
        radius=radius,
        fill=255
    )

    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    return result

def gradient_rect(size, color=(0, 0, 0), start_alpha=0, end_alpha=255):
    width, height = size

    img = Image.new("RGBA", size)

    pixels = img.load()

    for y in range(height):
        alpha = int(
            start_alpha + (end_alpha - start_alpha) * y / (height - 1)
        )

        for x in range(width):
            pixels[x, y] = (*color, alpha)

    return img