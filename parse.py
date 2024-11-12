import asyncio
import logging
import sys
from dataclasses import dataclass
from urllib.parse import urljoin
from bs4 import BeautifulSoup

import httpx
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

URL = "https://webscraper.io/"
HOME_URL = urljoin(URL, "test-sites/e-commerce/static/computers/laptops")


_driver: WebDriver | None = None


def get_driver() -> WebDriver:  # worse but easiest way to fix browser opening in every operation
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s %(levelname)8s] %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


async def get_content_from_url(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()  # Raises an exception for HTTP errors
        return response.content  # returns raw bytes


def parse_hdd_block_prices(product_soup: BeautifulSoup) -> dict[str, float]:
    detailed_url = urljoin(URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(detailed_url)
    swatches = driver.find_element(By.CLASS_NAME, "swatches")
    buttons = swatches.find_elements(By.TAG_NAME, "button")

    prices = {}
    for button in buttons:
        if not button.get_property("disabled"):
            button.click()
            prices[button.get_property("value")] = float(driver.find_element(By.CLASS_NAME, "price").text.replace("$", ""))
    return prices


async def parse_single_product(product_soup: BeautifulSoup) -> Product:
    hdd_prices = parse_hdd_block_prices(product_soup)

    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one("p.description").text,
        price=float(product_soup.select_one("h4.price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(
            product_soup.select_one("p.review-count").text.replace("reviews", "")
        ),
        additional_info={"hdd_prices": hdd_prices},
    )


async def get_num_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select("li.page-item")
    if not pagination:
        return 1
    return int(page_soup.select("li.page-item")[-2].text)


async def parse_page(last_page: int):
    for page_num in range(1, last_page + 1):
        logging.info(f"Start parsing page #{page_num}")
        page_content = await get_content_from_url(HOME_URL + f"?page={page_num}")
        soup = BeautifulSoup(page_content, "html.parser")
        products = soup.select(".thumbnail")  # calling css selector

        result_of_page = await asyncio.gather(
            *(parse_single_product(product) for product in products)
        )

        formatted_results = "\n".join(map(str, result_of_page))
        print(f"Results for Page {page_num}:\n{formatted_results}")


async def get_products():
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        page_content = await get_content_from_url(HOME_URL)
        soup = BeautifulSoup(page_content, "html.parser")

        last_page = await get_num_pages(soup)
        await parse_page(last_page)


if __name__ == "__main__":
    result = asyncio.run(get_products())
    print(result)
