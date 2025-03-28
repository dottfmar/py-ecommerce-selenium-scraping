import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import requests
from selenium.common import (
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
TOUCHES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

LINKS_F_NAME = {
    HOME_URL: "home",
    COMPUTERS_URL: "computers",
    PHONES_URL: "phones",
    LAPTOPS_URL: "laptops",
    TABLETS_URL: "tablets",
    TOUCHES_URL: "touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS = [field.name for field in fields(Product)]


def clean_text(text: str) -> str:
    return text.replace("\xa0", " ").strip()


def reviews_from_row(row: str) -> int:
    return int(str(row).replace("\t", "").replace("\n", "").split()[0])


def parse_single_card(card: Tag) -> Product:
    title = clean_text(card.select(".title")[0]["title"])
    description = clean_text(str(card.select(".description")[0].contents[0]))
    price = float(str(card.select(".price")[0].contents[0]).replace("$", ""))
    review = card.select(".review-count")[0]
    r_count = reviews_from_row(review.text)
    r_rating = len(card.select(".ws-icon-star"))

    return Product(
        title=title,
        description=description,
        price=price,
        rating=r_rating,
        num_of_reviews=r_count
    )


def get_soup_page_by_url(url: str) -> BeautifulSoup:
    res = requests.get(url).content
    return BeautifulSoup(res, "html.parser")


def get_soup_page_with_more_button(page_link: str) -> BeautifulSoup:
    browser = Chrome()
    browser.get(page_link)

    if browser.find_elements(By.CSS_SELECTOR, ".acceptCookies"):
        browser.find_elements(By.CSS_SELECTOR, ".acceptCookies")[0].click()
    while True:
        try:
            more_button = browser.find_elements(
                By.CSS_SELECTOR,
                ".ecomerce-items-scroll-more")[0]
            more_button.click()
        except (
            ElementNotInteractableException,
            ElementClickInterceptedException
        ):
            break

    page_html = browser.page_source
    browser.quit()
    return BeautifulSoup(page_html, "html.parser")


def get_cards(soup_page: BeautifulSoup) -> list[Tag]:
    return soup_page.select(".card")


def write_to_csv(products: list[Product], name: str) -> None:
    with open(f"{name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS)
        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    for page_link, f_name in LINKS_F_NAME.items():
        bs_page = get_soup_page_by_url(page_link)

        if bs_page.select(".ecomerce-items-scroll-more"):
            bs_page = get_soup_page_with_more_button(page_link)

        cards = get_cards(bs_page)
        parsed_cards = [parse_single_card(card) for card in cards]

        write_to_csv(parsed_cards, f_name)


if __name__ == "__main__":
    get_all_products()
