import os

import markdown

from bkmrks import files, folders, md


def render():
    clean_public_folder()
    bookmarks = os.listdir(folders.catalogs_folder())
    menu = []
    htmls = []
    mds = []
    for catalog in bookmarks:
        md_file_name = folders.public_folder(path=catalog)
        md_generated_file = md.generate(md_file_name=md_file_name, catalog=catalog)
        mds.append(md_generated_file)
        if md_generated_file is not None:
            htmls.append(generate_html(md_file_name))
            menu.append(
                get_file_and_set_variable(
                    file=folders.templates_folder(path="menu_item.html"),
                    variable="menu_item",
                    content=files.extract_file_name_no_ext(catalog),
                )
            )
    menu = " | ".join(menu)
    for html in htmls:
        html_content = get_file_and_set_variable(
            file=html,
            variable="menu",
            content=menu,
        )
        with open(html, "+w") as f:
            f.write(html_content)

    delete_files(files=mds)


def generate_html(md_file=None, template="index"):
    if md_file is None:
        md_file = folders.public_folder(path="index")

    md_file = files.apply_ext(md_file, ext="md")

    with open(md_file, "r") as fm:
        html = set_template_content(
            markdown.markdown(fm.read()), template, extension="html"
        )

        catalog = files.extract_file_name_no_ext(file_path=md_file)
        html = html.replace("{__catalog__}", catalog)

        html_file_name = files.apply_ext(file_path=md_file, ext="html")
        with open(html_file_name, "+w") as fh:
            fh.write(html)
    return html_file_name


def get_file_and_set_variable(file, variable, content):
    with open(file, "r") as f:
        file_content = f.read().replace("{" + variable + "}", content)
    return file_content


def get_template(base_file_name, extension="html"):

    template = "{" + extension + "}"
    path = files.apply_ext(base_file_name, extension)

    template_file = folders.templates_folder(path=path)
    if os.path.exists(template_file):
        with open(template_file, "r") as f:
            template = f.read()

        if extension == "html":
            dirs = os.listdir(folders.templates_folder())
            for file in dirs:
                if files.extract_ext(file) != "html" and files.extract_file_name_no_ext(
                    file
                ) == files.extract_file_name_no_ext(base_file_name):
                    innerextension = files.extract_ext(file)
                    innerfile = folders.templates_folder(path=file)
                    with open(innerfile, "r") as f:
                        innertemplate = f.read()
                        template = template.replace(
                            "{" + innerextension + "}", innertemplate
                        )

    return template


def set_template_content(content, base_file_name, extension="html"):
    template = get_template(base_file_name, extension=extension)
    return template.replace("{" + extension + "}", content)


def clean_public_folder():
    public_folder = folders.public_folder()
    public_folder_files = os.listdir(public_folder)
    delete_files(files=public_folder_files, folder=public_folder)


def delete_files(files: list, folder=""):
    for file in files:
        try:
            file = os.path.join(folder, file)
            if os.path.basename(file) != "":
                os.remove(file)
        except:
            pass
