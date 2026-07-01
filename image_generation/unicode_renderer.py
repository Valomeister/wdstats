# unicode_renderer.py
import asyncio
import base64
import json
import time
from io import BytesIO

from PIL import Image
from playwright.async_api import async_playwright

_pw = None
_browser = None
_page = None


async def _init_browser():
    global _pw, _browser, _page

    if _browser is None:
        _pw = await async_playwright().start()
        _browser = await _pw.chromium.launch()
        _page = await _browser.new_page()

        html = f"""
        <html>
            <body>
                <canvas id="c"></canvas>
            </body>
        </html>
        """

        await _page.set_content(html)

async def render_unicode(
        text: str,
        color: str = "black",
        font_size: int = 48,
        outline_width: int = 0,
        outline_color: str = "white",
):
    await _init_browser()
    script = f"""
            const canvas = document.getElementById("c");
            const ctx = canvas.getContext("2d");

            ctx.reset();

            const text = {json.dumps(text)};

            const fontSize = {font_size};
            const color = {json.dumps(color)};

            const outlineWidth = {outline_width};
            const outlineColor = {json.dumps(outline_color)};

            ctx.font = `900 ${{fontSize}}px Carlito`;

            const metrics = ctx.measureText(text);

            const padding = 2 * outlineWidth;

            const textWidth = metrics.width;

            const textHeight =
                metrics.actualBoundingBoxAscent +
                metrics.actualBoundingBoxDescent;


            canvas.width = Math.ceil(textWidth + padding * 2);
            canvas.height = Math.ceil(textHeight + padding * 2);

            ctx.font = `900 ${{fontSize}}px Carlito`;
            ctx.textBaseline = "middle";


            const x = padding;
            const y = canvas.height / 2;

            if (outlineWidth > 0) {{
                ctx.lineJoin = "round";
                ctx.lineWidth = outlineWidth;
                ctx.strokeStyle = outlineColor;
                ctx.strokeText(text, x, y);
            }}

            ctx.fillStyle = color;
            ctx.fillText(text, x, y);


            window.result = canvas.toDataURL("image/png");
        """
    await _page.evaluate(script)
    data = await _page.evaluate('window.result')

    png = base64.b64decode(
        data.split(",")[1]
    )

    return Image.open(
        BytesIO(png)
    ).convert("RGBA")

async def close_renderer():
    global _browser, _pw

    if _browser:
        await _browser.close()
        _browser = None

    if _pw:
        await _pw.stop()
        _pw = None
