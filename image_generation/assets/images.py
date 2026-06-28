from PIL import Image

from image_generation.image_utils import round_img, load_ranked_ranks, load_game_mode_icons, load_brawler_icons

CANVAS = Image.open('image_generation/assets/images/bg.jpg')
BRAWLER_ICONS = load_brawler_icons('image_generation/assets/images/brawler_icons', (70, 70))
SMALLER_BRAWLER_ICONS = {
    brawler: img.resize((60, 60))
    for brawler, img in BRAWLER_ICONS.items()
}
BIGGER_BRAWLER_ICONS = {
    brawler: img.resize((110, 110))
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
    'image_generation/assets/images/ranked_ranks/', up_to=22, height=60)
RANK_ICONS_NO_DIGITS = load_ranked_ranks(
    'image_generation/assets/images/ranked_ranks_no_digits/', up_to=8, height=50
)
GAME_MODE_ICONS = load_game_mode_icons('image_generation/assets/images/mode_icons', 60)
DARK_BG = Image.open('image_generation/assets/images/dark_rect.png').convert('RGBA')
alpha = DARK_BG.getchannel('A')
alpha = alpha.point(lambda p: p * 0.7)
DARK_BG.putalpha(alpha)
TROPHY = Image.open('image_generation/assets/images/trophy.png').convert('RGBA')
MODE_PLACEHOLDER = (Image.open('image_generation/assets/images/mode_icons/placeholder.png')
                    .convert('RGBA')
                    .resize((60, 60)))