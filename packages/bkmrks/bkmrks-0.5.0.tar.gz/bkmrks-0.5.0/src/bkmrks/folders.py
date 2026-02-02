import os

from dotenv import load_dotenv

load_dotenv()


def public_folder(path=""):
    ensure_public_folder()
    base_dir = "public"
    return apply_root_folder(path=base_dir, subpath=path)


def catalogs_folder(path=""):
    ensure_catalogs_folder()
    base_dir = "catalogs"
    return apply_root_folder(path=base_dir, subpath=path)


def templates_folder(path=""):
    ensure_template_folder()
    base_dir = "templates"
    return apply_root_folder(path=base_dir, subpath=path)


def apply_root_folder(path, subpath=""):
    root = os.getenv("BKMRKS_DIR_ROOT", ".")
    dir_name = os.path.join(root, path, subpath)
    return dir_name


def ensure_public_folder():
    dir_to_ensure = apply_root_folder(path="public")
    if not os.path.exists(dir_to_ensure):
        os.mkdir(dir_to_ensure)


def ensure_template_folder():
    dir_to_ensure = apply_root_folder(path="templates")
    if not os.path.exists(dir_to_ensure):
        os.mkdir(dir_to_ensure)
        default_templates_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "templates"
        )
        files = os.listdir(default_templates_dir)
        for file in files:
            if file.split(".")[1] in ["css", "html"]:
                with open(os.path.join(default_templates_dir, file), "r+") as fr:
                    with open(os.path.join(dir_to_ensure, file), "+w") as fw:
                        fw.write(fr.read())


def ensure_catalogs_folder():
    dir_to_ensure = apply_root_folder(path="catalogs")
    if not os.path.exists(dir_to_ensure):
        from bkmrks import bkmrks

        os.mkdir(dir_to_ensure)
        data = {
            bkmrks.create_line_name(line_index=1): {
                bkmrks.create_item_name(item_index=1): bkmrks.get_bookmark_item(
                    url="https://github.com/bouli/bkmrks",
                    name="bkmrks_sample_page",
                    img="https://cesarcardoso.cc/README/1_bouli.png",
                )
            }
        }
        bkmrks.set_catalog_data(data=data)
