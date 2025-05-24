from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


def soupParse(project_overview, promoter_details):
    soup = BeautifulSoup(project_overview, "html.parser")
    project_name_el = soup.select_one(
        "#mainContent > div > div > app-project-overview > div > div.project-details.mb-4 > div > div.card-body > div > div:nth-child(1) > div:nth-child(1) > div.details-project.ms-3 > strong"
    )
    rera_regd_no_el = soup.select_one(
        "#mainContent > div > div > app-project-overview > div > div.project-details.mb-4 > div > div.card-body > div > div:nth-child(1) > div:nth-child(4) > div.details-project.ms-3 > strong"
    )
    if project_name_el and rera_regd_no_el:
        project_name = project_name_el.get_text(strip=True)
        rera_regd_no = rera_regd_no_el.get_text(strip=True)
        print("----------------------------------------")
        print(f"Project name: {project_name}")
        print(f"RERA Regd. No.: {rera_regd_no}")

    soup = BeautifulSoup(promoter_details, "html.parser")

    gst_label = soup.find("label", string=re.compile(r"\bGST\s*No\.?\b", re.I))
    if not gst_label:
        return None  # no GST label on this page

    gst_el = gst_label.find_next_sibling("strong")
    if not gst_el:
        return None
    gst_no = gst_el.get_text(strip=True)

    address_label = soup.find(
        "label",
        string=re.compile(
            r"\b(?:Registered\s+Office|Current\s+Residence)\s+Address\.?\b", re.I
        ),
    )

    if not address_label:
        return None

    address_el = address_label.find_next_sibling("strong")
    if not address_el:
        return None
    address = address_el.get_text(strip=True)

    company_name_el = soup.select_one(
        "#mainContent > div > div > app-promoter-details > div.promoter.mb-4 > div > div.card-body > div > div:nth-child(1) > div > div.ms-3 > strong"
    )
    registered_office_addr = soup.select_one(
        "#mainContent > div > div > app-promoter-details > div.promoter.mb-4 > div > div.card-body > div > div:nth-child(6) > div > div.ms-3 > strong"
    )
    if company_name_el and registered_office_addr:
        company_name = company_name_el.get_text(strip=True)

        registered_office_address = registered_office_addr.get_text(strip=True)
        print(f"Company name: {company_name}")
        print(f"GST no: {gst_no}")
        print(f"Reg. office address: {address}")


def selenium_navigator():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://rera.odisha.gov.in/projects/project-list")
        wait.until(
            EC.visibility_of_element_located((By.XPATH, "//app-project-card//a[2]"))
        )

        # grab buttons once
        btn_locator = (By.XPATH, "//app-project-card//a[2]")
        buttons = driver.find_elements(*btn_locator)
        total = len(buttons)
        print(f"Found {total} buttons to click.")

        for idx in range(total):
            # re-fetch after navigation to avoid stale references
            buttons = wait.until(EC.visibility_of_all_elements_located(btn_locator))
            btn = buttons[idx]

            # scroll + JS-click to avoid interception
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            driver.execute_script("arguments[0].click();", btn)

            # wait for the detail view to load
            wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="mainContent"]'
                        "/div/div/app-project-overview"
                        "/div/div[1]/div/div[2]"
                        "/div/div[1]/div[1]/div[2]",
                    )
                )
            )

            element = driver.find_element(
                By.XPATH,
                '//*[@id="mainContent"]'
                "/div/div/app-project-overview"
                "/div/div[1]/div/div[2]"
                "/div/div[1]/div[1]/div[2]",
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )

            project_overview = driver.page_source

            promoter_tab = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//ul[@role='tablist']//a[contains(normalize-space(.), 'Promoter Details')]",
                    )
                )
            )
            promoter_tab.click()

            wait.until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "#mainContent > div > div > app-promoter-details > div.promoter.mb-4",  # pick a class unique to that section
                    )
                )
            )

            gst_xpath = "#mainContent > div > div > app-promoter-details > div > div > div.card-body > div > div:nth-child(1) > div > div.ms-3 > strong"
            WebDriverWait(driver, 15).until(
                lambda d: d.find_element(By.CSS_SELECTOR, gst_xpath).text.strip()
                not in ("--", "")
            )

            promoter_details = driver.page_source

            soupParse(project_overview, promoter_details)

            driver.back()
            wait.until(EC.presence_of_all_elements_located(btn_locator))

    except Exception as e:
        print(e)

    finally:
        driver.quit()


selenium_navigator()
