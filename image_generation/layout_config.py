from PIL import ImageFont


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

    # bar
    "bar_width": 330,
    "bar_height": 50,
    "bar_border_width": 6,
    "bar_inner_border_width": 4,
    "outer_border_radius": 20,
    "inner_border_radius": 10,
    "padding_for_numbers": 6,
    "bar_stroke_width": 2,
})

REQUIRED_MODES = {"brawlBall", "gemGrab", "heist", "hotZone", "knockout", "bounty"}

gamemodes_colors = {
    'bounty': '#0BCDFF',
    'brawlBall': '#8CA0DF',
    'gemGrab': '#9B3DF3',
    'heist': '#CE59CC',
    'hotZone': '#DD394F',
    'knockout': '#FF7F14',
}

result_colors = {
    1: '#67B000',
    0: '#F3D600',
    -1: '#E62727'
}

result_titles = {
    1: 'VICTORY',
    0: 'DRAW',
    -1: 'LOSS'
}