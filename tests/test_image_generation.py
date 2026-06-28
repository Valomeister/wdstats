import pytest

from image_generation.views.compact_matches_generator import create_compact_matches_img
from image_generation.views.detailed_matches_generator import create_detailed_matches_img
from image_generation.views.main_ranked_generator import create_main_ranked_img
from image_generation.views.ranked_by_brawler_generator import create_ranked_img_by_brawler
from image_generation.views.ranked_by_mode_generator import create_ranked_img_by_mode
from image_generation.views.template_generator import get_template


@pytest.mark.asyncio
async def test_template_generator():
    stats = (45, 27, 1, 17)
    canvas, draw = await get_template(stats, 'some nickname', 'ranked')


@pytest.mark.asyncio
async def test_main_ranked_generator():
    tag = '#2RJUQQ0Q8Y'
    nickname = 'ВалеркаБондерка'
    img = await create_main_ranked_img(tag, nickname)


@pytest.mark.asyncio
async def test_ranked_by_mode_generator():
    tag = '#2RJUQQ0Q8Y'
    nickname = 'ВалеркаБондерка'
    img = await create_ranked_img_by_mode(tag, nickname)


@pytest.mark.asyncio
async def test_ranked_by_brawler_generator():
    tag = '#2RJUQQ0Q8Y'
    nickname = 'ВалеркаБондерка'
    img, num_of_pages = await create_ranked_img_by_brawler(tag, nickname, page=1)


@pytest.mark.asyncio
async def test_compact_matches_generator():
    tag = '#2RJUQQ0Q8Y'
    nickname = 'ВалеркаБондерка'
    img, num_of_pages = await create_compact_matches_img(tag, nickname, page=1)


@pytest.mark.asyncio
async def test_detailed_matches_generator():
    tag = '#2RJUQQ0Q8Y'
    nickname = 'ВалеркаБондерка'
    img, num_of_pages = await create_detailed_matches_img(tag, nickname, page=1)
