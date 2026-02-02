import re
import urllib

import requests
from bs4 import BeautifulSoup

from bkmrks import urls


def get_url_icon(url):

    domain = urls.extract_domain_from_url(url=url)
    if len(domain) == 0:
        return get_default_img(text=url)

    meta_icon, url_soup = get_meta_icon_from_url(url=url)
    if meta_icon is not None:
        return meta_icon

    favicon = get_favicon_from_url(url=url)
    if favicon is not None:
        return favicon

    url_first_img = get_first_img_from_url(url=url, url_soup=url_soup)
    if url_first_img is not None:
        return urls.ensure_domain(url_first_img, domain)

    domain_first_img = get_first_img_from_url(url=domain)
    if domain_first_img is not None:
        return urls.ensure_domain(domain_first_img, domain)

    return get_default_img(text=url)


def get_meta_icon_from_url(url, url_soup=None):
    soup_icons, url_soup = get_soup_icons_from_url(url, url_soup)

    if soup_icons is None or len(soup_icons) == 0:
        img = None
        return img, url_soup
    else:
        final_icon = soup_icons[0]
        for soup_icon in soup_icons:
            if get_soup_icon_size(soup_icon) >= get_soup_icon_size(final_icon):
                final_icon = soup_icon
        img = final_icon["href"]

    img = urls.ensure_relative_path(img, url)
    return img, url_soup


def get_soup_icons_from_url(url, url_soup=None):
    if url_soup is None:
        try:
            url_request = requests.get(url)
            url_soup = BeautifulSoup(url_request.text, features="html.parser")
        except:
            return None, None

    soup_icons = url_soup.find_all(
        "link",
        attrs={
            "rel": [
                "icon",
                "apple-touch-icon",
            ]
        },
    )
    return soup_icons, url_soup


def get_soup_icon_size(soup_icon):
    if not soup_icon.has_attr("sizes"):
        return 1
    return int(soup_icon["sizes"].split("x")[0])


def get_favicon_from_url(url):
    domain = urls.extract_domain_from_url(url=url)
    favicon = domain + "/favicon.ico"
    try:
        favicon_request = requests.get(favicon)
    except:
        return None

    if favicon_request.status_code == 404 or "html" in favicon_request.text[:150]:
        return None
    else:
        return favicon


def get_first_img_from_url(url, url_soup=None):
    try:
        url_request = requests.get(url)
    except:
        return None

    if url_request.status_code == 404:
        return None
    if url_soup is None:
        url_soup = BeautifulSoup(url_request.text, features="html.parser")

    first_img = url_soup.find("img")
    if first_img is not None:
        img = urls.ensure_domain(first_img["src"], url)
        return img
    else:
        return None


def get_default_img(text):
    text = re.sub(r"[^a-zA-Z0-9./+]", "", text)
    text = text.replace("www", "").replace("https", "")
    text = text.replace(".", " ").replace("/", " ").strip()
    text = urllib.parse.quote(text, safe="=?&")
    return f"https://ui-avatars.com/api/?name={text}"


def get_img_from_a_soup_item(soup_item, domain):
    soup_item["href"] = urls.ensure_domain(url=soup_item["href"], domain=domain)

    use_soup_img = False
    if len(soup_item.find_all("img")) > 0:
        if len(soup_item.find("img")["src"]) < 200:
            use_soup_img = False
        else:
            use_soup_img = True

    if use_soup_img:
        img = soup_item.find("img")["src"]
    else:
        img = get_url_icon(soup_item["href"])
    return img
