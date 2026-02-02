import pytest


@pytest.mark.ui
def should_open_browser():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.terminalx.com")
        WebDriverWait(driver, 10).until(
            lambda driver: "terminal x" in driver.title.lower()
        )
    finally:
        driver.quit()
