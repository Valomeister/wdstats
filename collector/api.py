import aiohttp

from contextlib import asynccontextmanager


class BrawlAPI:
    def __init__(self, token):
        self.token = token
        self.session = None

    async def start(self):
        self.session = aiohttp.ClientSession(
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
        )

    async def get_matches(self, tag):
        url = f'https://api.brawlstars.com/v1/players/{tag.replace("#", "%23")}/battlelog'

        async with self.session.get(url) as response:
            return response.status, await response.json()

    async def get_profile(self, tag):
        url = f'https://api.brawlstars.com/v1/players/{tag.replace("#", "%23")}'

        async with self.session.get(url) as response:
            return response.status, await response.json()

    async def close(self):
        await self.session.close()

@asynccontextmanager
async def api_context(token):
    api_client = BrawlAPI(token)

    await api_client.start()

    try:
        yield api_client
    finally:
        await api_client.close()