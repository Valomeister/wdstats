from PIL import ImageFont


class DotDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

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
    "mode_icons_height": 60,

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

gamemodes_colors = {
    'bounty': '#0BCDFF',
    'brawlBall': '#8CA0DF',
    'gemGrab': '#9B3DF3',
    'heist': '#CE59CC',
    'hotZone': '#DD394F',
    'knockout': '#FE7E13',
}