from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class JupiterScrapper:
    def __init__(self):
        self.driver = webdriver.Firefox()

    def scrape(self):
        self.driver.get(
            "https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275"
        )
