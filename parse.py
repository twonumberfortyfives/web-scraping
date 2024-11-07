import asyncio
from dataclasses import dataclass
from urllib.parse import urljoin
from bs4 import BeautifulSoup

import httpx
from numba import njit

URL = "https://webscraper.io/"
HOME_URL = urljoin(URL, "test-sites/e-commerce/static/computers/laptops")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


async def get_content_from_url(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()  # Raises an exception for HTTP errors
        return response.content  # returns raw bytes


async def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one("p.description").text,
        price=float(product_soup.select_one("h4.price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product_soup.select_one("p.review-count").text.replace("reviews", "")),
    )


async def get_num_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select("li.page-item")
    if not pagination:
        return 1
    return int(page_soup.select("li.page-item")[-2].text)


async def parse_page(last_page: int):
    for page_num in range(1, last_page + 1):
        page_content = await get_content_from_url(HOME_URL + f"?page={page_num}")
        soup = BeautifulSoup(page_content, "html.parser")
        products = soup.select(".thumbnail")  # calling css selector

        result_of_page = await asyncio.gather(*(parse_single_product(product) for product in products))

        formatted_results = "\n".join(map(str, result_of_page))
        print(f"Results for Page {page_num}:\n{formatted_results}")

        # print(f"PAGE NUMBER {page_num}" + f"{[await parse_single_product(product) for product in products]}")


async def get_products():
    page_content = await get_content_from_url(HOME_URL)
    soup = BeautifulSoup(page_content, "html.parser")

    last_page = await get_num_pages(soup)
    await parse_page(last_page)


async def main():
    page_content = await get_content_from_url(HOME_URL)
    soup = BeautifulSoup(page_content, "html.parser")
    products = soup.select(".thumbnail")  # calling css selector
    return products


if __name__ == '__main__':
    result = asyncio.run(get_products())
    print(result)
