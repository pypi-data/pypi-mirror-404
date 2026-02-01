import os

import yaml
from bs4 import BeautifulSoup

from bkmrks import files, folders, icons, urls


def get_catalog_data(catalog="index"):
    catalog = files.apply_ext(catalog, ext="yaml")
    catalog_path = os.path.join(folders.catalogs_folder(), catalog)

    if not os.path.exists(catalog_path):
        return {}

    with open(catalog_path, "r") as f:
        catalog_data = yaml.safe_load(f.read())
        if catalog_data is None:
            return {}
        else:
            return catalog_data


def set_catalog_data(data, catalog="index"):
    catalog = files.apply_ext(catalog, ext="yaml")
    catalog_path = os.path.join(folders.catalogs_folder(), catalog)

    with open(catalog_path, "+w") as f:
        yaml.dump(data, f)
    return get_catalog_data(catalog=catalog)


def html2catalog(html_file_name, catalog):
    domain = urls.extract_domain_from_url(url=html_file_name)
    html = urls.read_from_url_or_path(url_path=html_file_name)

    soup = BeautifulSoup(html, features="html.parser")
    soup_all_hr_a_tags = soup.find_all(["hr", "a"])

    line_index = 1
    item_index = 1
    catalog_data = {}
    line_name = create_line_name(line_index=line_index)
    catalog_data[line_name] = {}

    for soup_item in soup_all_hr_a_tags:
        if soup_item.has_attr("href") and not soup_item["href"].startswith("#"):

            img = icons.get_img_from_a_soup_item(soup_item=soup_item, domain=domain)
            url = urls.ensure_domain(url=soup_item["href"], domain=domain)
            name = urls.get_name_from_domain(url=url)

            bookmark_item = get_bookmark_item(url=url, name=name, img=img)

            item_name = create_item_name(item_index=item_index)
            catalog_data[line_name][item_name] = bookmark_item.copy()

            item_index += 1

    set_catalog_data(data=catalog_data, catalog=catalog)


def move_url(
    from_catalog="index",
    from_line_index=1,
    from_item_index=0,
    to_catalog="index",
    to_line_index=1,
    to_item_index=0,
):
    url = get_url(
        catalog=from_catalog,
        line_index=from_line_index,
        item_index=from_item_index,
    )

    if url is None:
        return
    add_url(
        url=url,
        catalog=to_catalog,
        line_index=to_line_index,
        item_index=to_item_index,
    )
    remove_url(
        catalog=from_catalog,
        line_index=from_line_index,
        item_index=from_item_index,
    )
    return True


def add_url(url, catalog="index", line_index=1, item_index=1):
    catalog_data = get_catalog_data(catalog=catalog)
    line_index, line_alias = get_line_index_alias_from_catalog(
        line_index_alias=line_index, catalog_data=catalog_data
    )
    item_index = at_least_1(item_index)

    new_item = create_item_from_url(url=url)
    new_catalog_data = {}

    if len(catalog_data) < line_index:
        line_index = len(catalog_data) + 1
        new_line_name = create_line_name(line_index=line_index, line_alias=line_alias)
        new_item_name = create_item_name(item_index=1)

        new_catalog_data = catalog_data.copy()
        new_catalog_data[new_line_name] = {}
        new_catalog_data[new_line_name][new_item_name] = new_item
    else:
        line_to_add_name = get_dict_key_by_index(
            dict_index=line_index, dict_data=catalog_data
        )

        for line_name in catalog_data.keys():
            line_items_list = list(catalog_data[line_name].values())
            if line_name == line_to_add_name:
                line_items_list.insert(item_index - 1, new_item)

            new_catalog_data[line_name] = list2line_items(
                line_items_list=line_items_list
            )

    set_catalog_data(data=new_catalog_data, catalog=catalog)
    return True


def remove_url(catalog="index", line_index=1, item_index=0):
    catalog_data = get_catalog_data(catalog=catalog)
    line_index, line_alias = get_line_index_alias_from_catalog(
        line_index_alias=line_index, catalog_data=catalog_data
    )
    item_index = at_least_1(item_index)

    line_name = get_dict_key_by_index(dict_index=line_index, dict_data=catalog_data)
    if line_name is None:
        return False

    item_name = get_dict_key_by_index(
        dict_index=item_index, dict_data=catalog_data[line_name]
    )
    if item_name is None:
        return False

    catalog_data[line_name].pop(item_name)
    set_catalog_data(data=catalog_data, catalog=catalog)

    return True


def move_line(
    from_catalog: str = "index",
    from_line_index=1,
    to_catalog=None,
    new_line_alias=None,
):
    if to_catalog == None:
        to_catalog = from_catalog
    from_catalog_data = get_catalog_data(catalog=from_catalog)
    from_line_index, from_line_alias = get_line_index_alias_from_catalog(
        line_index_alias=from_line_index, catalog_data=from_catalog_data
    )
    from_line_name = get_dict_key_by_index(
        dict_index=from_line_index, dict_data=from_catalog_data
    )

    if new_line_alias is None:
        new_line_alias = from_line_alias
    new_line = from_catalog_data[from_line_name]

    from_catalog_data.pop(from_line_name)
    set_catalog_data(data=from_catalog_data, catalog=from_catalog)
    add_line_to_catalog(
        catalog=to_catalog, new_line=new_line, new_line_alias=new_line_alias
    )

    refresh_catalog_indexes(from_catalog)
    if from_catalog != to_catalog:
        refresh_catalog_indexes(to_catalog)
    return True


def add_line_to_catalog(catalog, new_line, new_line_alias=""):
    new_line_name = create_line_name(line_index=0, line_alias=new_line_alias)

    catalog_data = dict({new_line_name: new_line}, **get_catalog_data(catalog=catalog))
    set_catalog_data(data=catalog_data, catalog=catalog)


def refresh_catalog_indexes(catalog):
    catalog_data = get_catalog_data(catalog=catalog)
    new_catalog_data = {}
    for new_line_index, line_name in enumerate(catalog_data, start=1):
        if str(line_name).find("_") >= 0:
            new_line_alias = line_name.split("_")[1]
        else:
            new_line_alias = ""
        new_line_name = create_line_name(
            line_index=new_line_index, line_alias=new_line_alias
        )
        new_catalog_data[new_line_name] = catalog_data[line_name]
    set_catalog_data(data=new_catalog_data, catalog=catalog)


def get_url(
    catalog="index",
    line_index=1,
    item_index=1,
):
    url = None
    catalog_data = get_catalog_data(catalog=catalog)
    line_index, line_alias = get_line_index_alias_from_catalog(
        line_index_alias=line_index, catalog_data=catalog_data
    )
    item_index = at_least_1(item_index)

    if len(catalog_data) == 0:
        return
    if len(list(catalog_data.values())) >= line_index:
        catalog_line = list(catalog_data.values())[line_index - 1]
        if len(list(catalog_line.values())) >= item_index:
            if "url" in list(catalog_line.values())[item_index - 1]:
                url = list(catalog_line.values())[item_index - 1]["url"]

    return url


def create_line_name(line_index, line_alias=""):
    line_name = f"line{line_index:04d}"
    if len(line_alias) > 0:
        line_name += f"_{line_alias}"
    return line_name


def create_item_name(item_index):
    item_name = f"item{item_index:04d}"
    return item_name


def create_item_from_url(url, domain=None):
    if domain is not None:
        url = urls.ensure_domain(url=url, domain=domain)
    name = urls.get_name_from_domain(url=url)
    img = icons.get_url_icon(url=url)

    bookmark_item = get_bookmark_item(url=url, name=name, img=img)
    return bookmark_item


def get_bookmark_item(url, name, img):
    bookmark_item = {}
    bookmark_item["name"] = name
    bookmark_item["url"] = url
    bookmark_item["img"] = img

    return bookmark_item


def get_line_index_alias_from_catalog(line_index_alias, catalog_data):
    catalog_lines = list(catalog_data.keys())

    try:
        line_index = int(line_index_alias)
        line_index = at_least_1(line_index)
        if len(catalog_lines) >= line_index:
            line_alias = catalog_lines[line_index - 1][9:]
        else:
            line_alias = ""
    except:
        line_alias = str(line_index_alias)
        line_index = len(catalog_lines) + 1

        for catalog_line_index, catalog_line_name in enumerate(catalog_lines, start=1):
            if line_alias == catalog_line_name[9:]:
                line_index = catalog_line_index
                break
    return line_index, line_alias


def list2line_items(line_items_list: list) -> dict:
    items = {}
    for item_index, item in enumerate(line_items_list, start=1):
        item_name = create_item_name(item_index)
        items[item_name] = item
    return items


def at_least_1(number):
    number = int(number)
    if number < 1:
        number = 1

    return number


def get_dict_key_by_index(dict_index, dict_data):
    dict_index = int(dict_index)
    dict_key = ""
    if len(dict_data) < dict_index:
        return None

    dict_key = list(dict_data.keys())[dict_index - 1]
    return dict_key


def get_alias_from_line_name(line_name: str) -> str:
    line_alias = ""
    if line_name.find("_") > 0:
        line_alias = line_name.split("_")[1]
    return line_alias
