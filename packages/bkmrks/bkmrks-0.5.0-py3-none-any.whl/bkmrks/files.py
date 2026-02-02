import os


def apply_ext(file_path: str, ext: str) -> str:
    file_name = extract_file_name_no_ext(file_path=file_path)
    if file_name != "":
        file_name = ".".join([file_name] + [ext])
    file_path = os.path.join(os.path.dirname(file_path), file_name)
    return file_path


def extract_file_name_no_ext(file_path: str) -> str:
    file_name = os.path.basename(file_path)

    file_name_elements = file_name.split(".")
    if len(file_name_elements) > 1:
        file_name_elements = file_name_elements[:-1]

    file_name = ".".join(file_name_elements)
    return file_name


def extract_ext(file_path: str) -> str:
    file_name = os.path.basename(file_path)

    file_name_elements = file_name.split(".")
    if len(file_name_elements) > 1:
        ext = file_name_elements[-1]
    else:
        ext = ""
    return ext
