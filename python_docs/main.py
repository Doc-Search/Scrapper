from bs4 import BeautifulSoup
import requests
import time
from typing import Dict, Optional, Tuple, Union
import pandas as pd
import os
import json

BASE_URL = "https://docs.python.org/3/"


def process_class_name(st: str) -> str:
    return ".".join(st.split(" "))


def write_html_to_file(fname: str, html: BeautifulSoup) -> None:
    s = str(html.html)
    try:
        with open(fname, "w+", encoding="utf-8") as f:
            f.write(s)
    except Exception as e:
        raise Exception(f"Error in writing html to file : {e}")


def scrape_page(url: str) -> Tuple[int, Union[BeautifulSoup, None]]:
    try:
        page = requests.get(url)
        html = BeautifulSoup(page.content, "html.parser")
        return (page.status_code, html)
    except Exception as e:
        raise Exception(f"Error in scraping page {url} : {e}")


def get_content(page: BeautifulSoup, name: str) -> str:
    try:
        main_article = page.select_one("article.content div.text")
        return main_article.text
    except Exception as e:
        raise Exception(f"Error in getting main content of {str} : {e}")


def save_as_json(data, fname: str) -> None:
    try:
        if not os.path.isdir("save_data"):
            os.mkdir("save_data")
        with open(f"save_data/{fname}", "w") as f:
            json.dump(data, f, indent=4)
        print(f"File saved to : save_data/{fname}")
    except Exception as e:
        raise Exception(f"Error in saving data as csv : {e}")


def generate_sub_url(url: str, tail: str):
    root = url[: url.rindex("/")]
    return root + "/" + tail


def scrape_pydocs() -> None:
    p = 0
    f = 0

    def scrape_sub_page(
        page: BeautifulSoup, 
        url: str
    ) -> Dict:
        p = 0
        f = 0
        data = {}
        texts = []
        codes = []
        paras = page.select("div.body > section > p")
        for para in paras:
            texts.append(para.text)
        for component in page.select(".highlight"):
            codes.append(component.text)
        for component in page.select("body p"):
            texts.append(component.text)
        data["texts"] = texts
        data["codeBlocks"] = codes
        children = []
        for i in page.select("li.toctree-l1 > a"):
            sub_url = generate_sub_url(url, i.attrs["href"])
            sub_status, sub_page = scrape_page(sub_url)

            if sub_status != 200:
                f += 1
                print(
                    f"Failure ---- Problem scraping sub page {sub_text}. Status : {sub_status}"
                )
                continue
            
            g_data, gp, gf =  scrape_sub_page(sub_page, sub_url)
            p += gp
            f += gf
            children.append(
                {"name": i.text, "data": g_data}
            )
            p += 1
            print(f"Success ---- Scraped page {sub_url}")

        if len(children) != 0:
            data["children"] = children
        return data, p, f

    try:
        data = {}
        status, page = scrape_page(BASE_URL)
        assert status == 200, f"Status {status}"

        section_headers = page.select("p>strong")
        link_tables = page.select("table.contentstable")

        l = len(section_headers)

        for i in range(l):
            links = link_tables[i].select("a.biglink")
            for link in links:
                try:
                    sub_text = link.text
                    sub_url = BASE_URL + link.attrs["href"]
                    sub_status, sub_page = scrape_page(sub_url)
                    if sub_status != 200:
                        f += 1
                        print(
                            f"Failure ---- Problem scraping sub page {sub_text}. Status : {sub_status}"
                        )
                        continue
                    
                    g_data, gp, gf = scrape_sub_page(sub_page, sub_url)
                    p += gp
                    f += gf
                    data[sub_text] = {
                        "name": sub_text,
                        "children": g_data,
                    }

                except Exception as e:
                    f += 1
                    print(
                        f"Failure ---- Problem in getting content of sub page {sub_text}. Error : {e}"
                    )
                    continue
                p += 1
                print(f"Success ---- Scraped page {sub_text}")
                time.sleep(0.5)  # avoid ddos ban

        save_as_json(data, "pydoc_data.json")
        print("\n===================================")
        print(f"Total : {p+f}\tPass : {p}\tFail : {f}")
    except Exception as e:
        print(f"Error in main : {e}")


if __name__ == "__main__":
    print("Scanning python documentation starting... ")
    scrape_pydocs()
