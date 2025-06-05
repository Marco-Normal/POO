from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


class JupiterScrapper:
    def __init__(self):
        self.driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install())
        )

    def scrape(self):
        self.driver.get(
            "https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275"
        )
        campo_unidade = self.driver.find_element(By.ID, "comboUnidade")
        dropdown_unidade = Select(campo_unidade)
        enviar = self.driver.find_element(By.ID, "enviar")
        grade_horaria = self.driver.find_element(By.ID, "step4-tab")
        buscas = self.driver.find_element(By.ID, "step1-tab")
        for i in range(len(dropdown_unidade.options)):
            dropdown_unidade.select_by_index(i)
            campo_curso = self.driver.find_element(By.ID, "comboCurso")
            dropdown_curso = Select(campo_curso)
            for j in range(len(dropdown_curso.options)):
                dropdown_curso.select_by_index(j)


def main():
    scrapper = JupiterScrapper()
    scrapper.scrape()


if __name__ == "__main__":
    main()
