import asyncio
from urllib.parse import urljoin

import httpx


URL = "https://webscraper.io/"
HOME_URL = urljoin(URL, "test-sites/e-commerce/allinone")


async def get_content_from_url(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()  # Raises an exception for HTTP errors
        return response.content  # returns raw bytes


async def main():
    page_content = await get_content_from_url(HOME_URL)
    return page_content


if __name__ == '__main__':
    result = asyncio.run(main())
    print(result)
