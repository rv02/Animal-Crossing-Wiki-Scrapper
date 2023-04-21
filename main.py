import os
import requests
from bs4 import BeautifulSoup
import logging
import difflib
import filecmp

logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(message)s', level=logging.INFO)

# Define the URL to be scraped
url = "https://animalcrossing.fandom.com/wiki/Animal_Crossing_Wiki"


def scrape_article(url):
    """
    Scrapes the title, summary, and content of the given article URL.

    :param url: The URL of the article to be scraped.
    :return: A dictionary containing the title, summary, and content of the article.
    """
    try:
        # Make a request to the given URL
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f'Failed to scrape {url}. Status code: {response.status_code}')
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the title of the article
        title = soup.find("h1", class_="page-header__title")
        if title is None:
            logging.warning(f"No title found for {url}")
            title = "N/A"
        title = title.text.strip()

        # Extract the summary of the article
        summary = soup.find("div", class_="pi-data-value pi-font")
        summary = summary.text.strip() if summary is not None else 'N/A'

        # Extract the content of the page
        content_div = soup.find("div", {"class": "mw-parser-output"})
        if content_div is None:
            logging.warning(f"No content found for {url}")
            content = "N/A"
        else: 
            content = ""
            for p in content_div.find_all("p"):
                content += p.text + "\n"
        
        # Create a dictionary containing the scraped data
        data = {
            "title": title,
            "summary": summary,
            "content": content
        }

        return data
    
    except Exception as e:
        logging.error(f'Error occurred while scraping URL {url}: {e}')
    
    # Handle missing data
    return {'title': 'N/A', 'summary': 'N/A', 'content': 'N/A'}


def scrape_articles(url, article_links):
    """
    Recursively scrapes all articles linked to from the given URL.

    :param url: The URL of the page containing the article links to be scraped.
    :param article_links: A list of article links already scraped.
    :return: A list of article links scraped from the given URL, including any recursively scraped links.
    """
    # Make a request to the given URL
    response = requests.get(url)
    logging.info(f'Got response from main page:  {response}')

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all the article links on the page
    exclude = ["//", "?"]
    links = [a["href"] for a in soup.find_all("a", href=lambda href: href and "/wiki/" in href and not any(x in href for x in exclude))]

    # Scrape each article and store the data in a separate text file
    for link in links:
        article_url = "https://animalcrossing.fandom.com" + link
        if article_url not in article_links:
            data = scrape_article(article_url)
            filename = f"{data['title'].replace('/', '.')}"
            textfile = os.path.join(data_dir, f"{filename}.txt")

            # Get the new file data
            new_data = f"{data['title']}\n\n{data['summary']}\n\ndata['content']"

            if os.path.exists(textfile):
                # Read the old data from the file
                with open(textfile, "r") as old_file:
                    old_data = old_file.read()
            else:
                # Set the old data to an empty string if the file doesn't exist
                old_data = ""

            # Write the scraped data to a text file
            with open(textfile, "w", encoding="utf-8") as new_file:
                new_file.write(new_data)

            if old_data != new_data:

                diff = difflib.HtmlDiff()

                # Generate the HTML-formatted diff
                diff_output = diff.make_file(old_data.splitlines(), new_data.splitlines())

                
                with open(os.path.join(report_path, f"{filename}.html"), "w") as diff_file:
                    diff_file.write(diff_output)

            print(f"Scraped {data['title']}")
            article_links.append(article_url)

            # Recursively scrape any linked articles
            article_links = scrape_articles(article_url, article_links)

    return article_links


data_dir = "data"

if not os.path.exists(data_dir):
    os.mkdir(data_dir)

report_dir = "report"
report_path = os.path.join(data_dir, report_dir)
if not os.path.exists(report_path):
    os.mkdir(report_path)

# Scrape all articles linked to from the given URL
article_links = scrape_articles(url, [])

print("Scraping complete!")
