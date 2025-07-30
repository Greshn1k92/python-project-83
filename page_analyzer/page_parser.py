import requests
from bs4 import BeautifulSoup


def parse_page(url):
    """Parse page and extract SEO data"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        h1 = soup.find("h1")
        h1_text = h1.get_text().strip() if h1 else ""

        title = soup.find("title")
        title_text = title.get_text().strip() if title else ""

        description = soup.find("meta", attrs={"name": "description"})
        description_text = (
            description.get("content", "").strip() if description else ""
        )

        return {
            "status_code": response.status_code,
            "h1": h1_text,
            "title": title_text,
            "description": description_text,
        }
    except requests.RequestException:
        return None 