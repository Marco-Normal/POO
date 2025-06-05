# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import Select
# from selenium.webdriver.common.by import By
# from selenium import webdriver
# from selenium.webdriver.firefox.service import Service as FirefoxService
# from webdriver_manager.firefox import GeckoDriverManager
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.common.action_chains import ActionChains


# class JupiterScrapper:
#     def __init__(self):
#         self.driver = webdriver.Firefox(
#             service=FirefoxService(GeckoDriverManager().install())
#         )
#         self.wait = WebDriverWait(self.driver, 10)

#     def scrape(self):
#         self.driver.get(
#             "https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275"
#         )
#         campo_unidade = self.wait.until(
#             EC.element_to_be_selected((By.ID, "comboUnidade"))
#         )
#         dropdown_unidade = Select(campo_unidade)
#         enviar = self.wait.until(EC.element_to_be_selected((By.ID, "enviar")))
#         for i in range(len(dropdown_unidade.options)):
#             dropdown_unidade.select_by_index(i)
#             campo_curso = self.driver.find_element(By.ID, "comboCurso")
#             dropdown_curso = Select(campo_curso)
#             for j in range(len(dropdown_curso.options)):
#                 dropdown_curso.select_by_index(j)
#                 grade_horaria = self.wait.until(
#                     EC.element_to_be_clickable((By.ID, "step4-tab"))
#                 )
#                 ActionChains(self.driver).click(grade_horaria).perform()
#                 buscas = self.wait.until(
#                     EC.element_to_be_clickable((By.ID, "step1-tab"))
#                 )
#                 ActionChains(self.driver).click(buscas).perform()
# def main():
#     scrapper = JupiterScrapper()
#     scrapper.scrape()


# if __name__ == "__main__":
#     main()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
import json
from unidade import Unidade
from curso import Curso
from disciplina import Disciplina
from typing import List, Dict


class JupiterScrapper:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options,
        )
        self.wait = WebDriverWait(self.driver, 15)
        self.unidades: List[Unidade] = []
        self.all_disciplinas: Dict[str, Disciplina] = {}

    def scrape(self):
        try:
            self.driver.get(
                "https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275"
            )

            # Wait for unit dropdown to load
            dropdown_unidade = self.wait.until(
                EC.presence_of_element_located((By.ID, "comboUnidade"))
            )
            select_unidade = Select(dropdown_unidade)
            unidades_count = len(select_unidade.options)

            # Iterate through all units
            for i in range(1, 2):  # Skip first empty option
                unit_name = select_unidade.options[i].text.strip()
                print(f"\nProcessing Unit: {unit_name} ({i}/{unidades_count-1})")

                # Create unit object
                current_unidade = Unidade(unit_name)

                # Select unit
                select_unidade.select_by_index(i)
                time.sleep(1)  # Allow time for course dropdown to update

                # Get courses dropdown
                dropdown_curso = self.wait.until(
                    EC.presence_of_element_located((By.ID, "comboCurso"))
                )
                select_curso = Select(dropdown_curso)
                cursos_count = len(select_curso.options)
                print(f"\nNumero de cursos: {cursos_count}")
                # Iterate through all courses in the unit
                for j in range(1, cursos_count):  # Skip first empty option
                    curso_name = select_curso.options[j].text.strip()
                    print(f"  - Course: {curso_name} ({j}/{cursos_count-1})")

                    # Select course
                    select_curso.select_by_index(j)
                    time.sleep(0.5)  # Allow time for page to update

                    # Click on 'Grade Curricular' tab
                    try:
                        buscar = self.wait.until(
                            EC.presence_of_element_located((By.ID, "enviar"))
                        )
                        ActionChains(self.driver).click(buscar).perform()
                        time.sleep(2)  # Allow content to load
                        grade_tab = self.wait.until(
                            EC.element_to_be_clickable((By.ID, "step4-tab"))
                        )
                        ActionChains(self.driver).click(grade_tab).perform()
                        time.sleep(2)  # Allow content to load
                        # Extract course data
                        print(f"Extraindo informações do curso {curso_name}")
                        curso_data = self.extract_curso_data()
                        print(f"Dados extraidos: {curso_data}")
                        if curso_data:
                            # Create course object
                            curso_obj = Curso(
                                nome=curso_data["nome"],
                                unidade=current_unidade,
                                dur_ideal=curso_data["dur_ideal"],
                                dur_min=curso_data["dur_min"],
                                dur_max=curso_data["dur_max"],
                                dis_obr=curso_data["obrigatorias"],
                                dis_opt_livre=curso_data["optativas_livres"],
                                dis_opt_ele=curso_data["optativas_eletivas"],
                            )
                            current_unidade.adicionarCurso(curso_obj)
                        voltar_tab = self.wait.until(
                            EC.presence_of_element_located((By.ID, "step1-tab"))
                        )
                        ActionChains(self.driver).click(voltar_tab).perform()
                    except (TimeoutException, NoSuchElementException) as e:
                        print(f"    Error processing course: {str(e)}")
                        continue

                self.unidades.append(current_unidade)

                # Reset for next unit
                select_unidade = Select(self.driver.find_element(By.ID, "comboUnidade"))

            print("\nScraping completed successfully!")
            self.save_data()
            self.query_interface()

        except Exception as e:
            print(f"Fatal error during scraping: {str(e)}")
        finally:
            self.driver.quit()

    def extract_curso_data(self) -> dict:
        """Extract course data from the 'Grade Curricular' tab"""
        try:
            # Wait for curriculum content to load
            self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#step4 .unidade"))
            )

            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            # Extract course details from curriculum tab
            step4 = soup.find("div", id="step4")
            if not step4:
                return None

            # Extract course name
            nome = step4.find("span", class_="curso").get_text(strip=True)

            # Extract durations
            dur_ideal = int(step4.find("span", class_="duridlhab").get_text(strip=True))
            dur_min = int(step4.find("span", class_="durminhab").get_text(strip=True))
            dur_max = int(step4.find("span", class_="durmaxhab").get_text(strip=True))

            # Extract disciplines
            obrigatorias = self.extract_disciplinas(step4, "tb_obr")
            optativas_livres = self.extract_disciplinas(step4, "tb_opt_liv")
            optativas_eletivas = self.extract_disciplinas(step4, "tb_opt_ele")

            return {
                "nome": nome,
                "dur_ideal": dur_ideal,
                "dur_min": dur_min,
                "dur_max": dur_max,
                "obrigatorias": obrigatorias,
                "optativas_livres": optativas_livres,
                "optativas_eletivas": optativas_eletivas,
            }

        except Exception as e:
            print(f"    Error extracting course data: {str(e)}")
            return None

    def extract_disciplinas(self, container, table_id: str) -> List[Disciplina]:
        """Extract disciplines from a specific table"""
        disciplinas = []
        table = container.find("table", id=table_id)

        if table:
            # Get table headers
            headers = []
            header_row = table.find("tr")
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all("th")]

            # Process each data row
            for row in table.find_all("tr")[1:]:  # Skip header row
                cells = row.find_all("td")
                if len(cells) < 8:  # Ensure we have all columns
                    continue

                # Map cell data to headers
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.get_text(strip=True)

                # Create discipline if we have a code
                if "Código" in row_data and row_data["Código"]:
                    disciplina_data = self.parse_disciplina(row_data)

                    # Use existing discipline if we've seen this code before
                    if disciplina_data["codigo"] in self.all_disciplinas:
                        disciplina = self.all_disciplinas[disciplina_data["codigo"]]
                    else:
                        disciplina = Disciplina(**disciplina_data)
                        self.all_disciplinas[disciplina.codigo] = disciplina

                    disciplinas.append(disciplina)

        return disciplinas

    def parse_disciplina(self, row_data: dict) -> dict:
        """Parse discipline data from table row"""

        # Helper function to parse numerical values
        def parse_number(value):
            try:
                return int(value) if value.strip() else 0
            except:
                return 0

        return {
            "codigo": row_data.get("Código", ""),
            "nome": row_data.get("Disciplina", ""),
            "cred_aula": parse_number(row_data.get("Créditos Aula", "0")),
            "cred_trab": parse_number(row_data.get("Créditos Trabalho", "0")),
            "carga_horaria": parse_number(row_data.get("CH Total", "0")),
            "carg_hor_est": parse_number(row_data.get("CH Estágio", "0")),
            "carg_hor_pratica": parse_number(row_data.get("CH Prática", "0")),
            "atvd_teoricas": parse_number(row_data.get("CH Ativ. Teor-Prát.", "0")),
        }

    def save_data(self):
        """Save scraped data to JSON file"""
        try:
            data = {
                "unidades": [
                    {
                        "nome": unidade.nome,
                        "cursos": [
                            {
                                "nome": curso.nome,
                                "dur_ideal": curso.dur_ideal,
                                "dur_min": curso.dur_min,
                                "dur_max": curso.dur_max,
                                "obrigatorias": [d.codigo for d in curso.dis_obr],
                                "optativas_livres": [
                                    d.codigo for d in curso.dis_opt_livre
                                ],
                                "optativas_eletivas": [
                                    d.codigo for d in curso.dis_opt_ele
                                ],
                            }
                            for curso in unidade.cursos
                        ],
                    }
                    for unidade in self.unidades
                ],
                "disciplinas": {
                    code: {
                        "codigo": disc.codigo,
                        "nome": disc.nome,
                        "cred_aula": disc.cred_aula,
                        "cred_trab": disc.cred_trab,
                        "carga_horaria": disc.carga_horaria,
                        "carg_hor_est": disc.carg_hor_est,
                        "carg_hor_pratica": disc.carg_hor_pratica,
                        "atvd_teoricas": disc.atvd_teoricas,
                    }
                    for code, disc in self.all_disciplinas.items()
                },
            }

            with open("usp_courses.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print("Data saved to usp_courses.json")
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def query_interface(self):
        """User interface for querying scraped data"""
        while True:
            print("\n=== USP COURSE DATA QUERY ===")
            print("1. List courses by unit")
            print("2. Show course details")
            print("3. Show discipline details")
            print("4. Disciplines used in multiple courses")
            print("5. Exit")

            choice = input("Enter your choice: ")

            if choice == "1":
                self.list_courses_by_unit()
            elif choice == "2":
                self.show_course_details()
            elif choice == "3":
                self.show_discipline_details()
            elif choice == "4":
                self.find_shared_disciplines()
            elif choice == "5":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

    def list_courses_by_unit(self):
        """List all courses grouped by unit"""
        print("\nCourses by Unit:")
        for unidade in self.unidades:
            print(f"\n{unidade.nome}:")
            for curso in unidade.cursos:
                print(f"  - {curso.nome}")
        print(f"\nTotal units: {len(self.unidades)}")
        print(f"Total courses: {sum(len(u.cursos) for u in self.unidades)}")

    def show_course_details(self):
        """Show details for a specific course"""
        course_name = input("Enter course name: ").strip()
        found = False

        for unidade in self.unidades:
            for curso in unidade.cursos:
                if course_name.lower() in curso.nome.lower():
                    found = True
                    print(f"\nCourse: {curso.nome}")
                    print(f"Unit: {unidade.nome}")
                    print(
                        f"Duration: Ideal={curso.dur_ideal} sem, Min={curso.dur_min} sem, Max={curso.dur_max} sem"
                    )

                    print("\nMandatory Disciplines:")
                    for disc in curso.dis_obr:
                        print(f"  - {disc.codigo}: {disc.nome}")

                    print("\nFree Electives:")
                    for disc in curso.dis_opt_livre:
                        print(f"  - {disc.codigo}: {disc.nome}")

                    print("\nSpecific Electives:")
                    for disc in curso.dis_opt_ele:
                        print(f"  - {disc.codigo}: {disc.nome}")

        if not found:
            print("Course not found!")

    def show_discipline_details(self):
        """Show details for a specific discipline"""
        code = input("Enter discipline code: ").strip().upper()
        discipline = self.all_disciplinas.get(code)

        if discipline:
            print(f"\nDiscipline: {discipline.codigo} - {discipline.nome}")
            print(f"Class Credits: {discipline.cred_aula}")
            print(f"Work Credits: {discipline.cred_trab}")
            print(f"Total Hours: {discipline.carga_horaria}")
            print(f"Internship Hours: {discipline.carg_hor_est}")
            print(f"Practical Hours: {discipline.carg_hor_pratica}")
            print(f"Theory-Practice Hours: {discipline.atvd_teoricas}")

            # Find courses that include this discipline
            courses = []
            for unidade in self.unidades:
                for curso in unidade.cursos:
                    all_disc = curso.dis_obr + curso.dis_opt_livre + curso.dis_opt_ele
                    if any(d.codigo == code for d in all_disc):
                        courses.append(f"{curso.nome} ({unidade.nome})")

            if courses:
                print("\nPart of courses:")
                for course in courses:
                    print(f"  - {course}")
            else:
                print("\nNot found in any courses")
        else:
            print("Discipline not found!")

    def find_shared_disciplines(self, min_courses=2):
        """Find disciplines used in multiple courses"""
        shared = {}

        # Count discipline usage
        for unidade in self.unidades:
            for curso in unidade.cursos:
                all_disc = set(
                    d.codigo
                    for d in curso.dis_obr + curso.dis_opt_livre + curso.dis_opt_ele
                )
                for code in all_disc:
                    shared[code] = shared.get(code, 0) + 1

        # Filter and sort
        filtered = {
            code: count
            for code, count in shared.items()
            if count >= min_courses and code in self.all_disciplinas
        }
        sorted_shared = sorted(filtered.items(), key=lambda x: x[1], reverse=True)

        # Display results
        print(f"\nDisciplines in ≥{min_courses} courses:")
        for code, count in sorted_shared:
            disc = self.all_disciplinas[code]
            print(f"{code}: {disc.nome} ({count} courses)")

        print(f"\nTotal shared disciplines: {len(sorted_shared)}")


def main():
    scrapper = JupiterScrapper()
    scrapper.scrape()


if __name__ == "__main__":
    main()
