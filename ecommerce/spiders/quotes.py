
import scrapy
from scrapy import Selector, Request
from scrapy.http import Response
from selenium import webdriver
from selenium.webdriver.common.by import By


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = [
        "https://quotes.toscrape.com"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver = webdriver.Chrome()

    def close(self, reason):
        self.driver.close()

    def parse(self, response: Response, **kwargs):
        for quote in response.css(".quote"):
            yield {
                "text": quote.css(".text::text").get(),
                "author": quote.css(".author::text").get(),
                # "author_info": self._parse_author_info(response, quote), Implementation with selenium
                "author_info": self._parse_author_info(response, quote),
                "tags": [tag.css(".tag::text").get() for tag in quote.css(".tag")]
            }

        next_page = response.css(".next > a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    # def _parse_author_info(  Implementation with selenium
    #         self,
    #         response: Response,
    #         product: Selector
    # ) -> dict:
    #     detailed_url = response.urljoin(product.css("span > a::attr(href)").get())
    #     self.driver.get(detailed_url)
    #     return {
    #         "born_date": self.driver.find_element(By.CLASS_NAME, "author-born-date").text,
    #         "born_location": self.driver.find_element(By.CLASS_NAME, "author-born-location").text,
    #     }

    def _parse_author_info(self, response: Response, product: Selector) -> Request:
        detailed_url = response.urljoin(product.css("span > a::attr(href)").get())
        yield Request(detailed_url, callback=self.parse_author_page)

    def parse_author_page(self, response: Response) -> dict:
        return {
            "born_date": response.css(".author-born-date::text").get(),
            "born_location": response.css(".author-born-location::text").get(),
        }
