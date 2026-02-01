from bkmrks import files

def test_apply_ext():
    tests = []
    tests.append({"ext":"yaml", "file_path":"", "expected_result":""})
    tests.append({"ext":"yaml", "file_path":"/", "expected_result":"/"})
    tests.append({"ext":"yaml", "file_path":"/folder/", "expected_result":"/folder/"})
    tests.append({"ext":"yaml", "file_path":"/folder/subfolder/", "expected_result":"/folder/subfolder/"})

    tests.append({"ext":"yaml", "file_path":"/folder/fi.le.py", "expected_result":"/folder/fi.le.yaml"})
    tests.append({"ext":"yaml", "file_path":"/folder/file.py", "expected_result":"/folder/file.yaml"})
    tests.append({"ext":"yaml", "file_path":"/folder/file", "expected_result":"/folder/file.yaml"})
    tests.append({"ext":"yaml", "file_path":"/file.py", "expected_result":"/file.yaml"})
    tests.append({"ext":"yaml", "file_path":"file.py", "expected_result":"file.yaml"})
    tests.append({"ext":"yaml", "file_path":"file", "expected_result":"file.yaml"})

    for test in tests:
        assert files.apply_ext(ext=test["ext"], file_path=test["file_path"]) == test["expected_result"]


def test_extract_file_name_no_ext():
    tests = []
    tests.append({"file_path":"", "expected_result":""})
    tests.append({"file_path":"/", "expected_result":""})
    tests.append({"file_path":"/folder/", "expected_result":""})
    tests.append({"file_path":"/folder/subfolder/", "expected_result":""})

    tests.append({"file_path":"/folder/fi.le.py", "expected_result":"fi.le"})
    tests.append({"file_path":"/folder/file.py", "expected_result":"file"})
    tests.append({"file_path":"/folder/file", "expected_result":"file"})
    tests.append({"file_path":"/file.py", "expected_result":"file"})
    tests.append({"file_path":"file.py", "expected_result":"file"})
    tests.append({"file_path":"file", "expected_result":"file"})

    for test in tests:
        assert files.extract_file_name_no_ext(file_path=test["file_path"]) == test["expected_result"]

def test_extract_ext():
    tests = []
    tests.append({"file_path":"", "expected_result":""})
    tests.append({"file_path":"/", "expected_result":""})
    tests.append({"file_path":"/folder/", "expected_result":""})
    tests.append({"file_path":"/folder/subfolder/", "expected_result":""})
    tests.append({"file_path":"/folder/fi.le.py", "expected_result":"py"})
    tests.append({"file_path":"/folder/file.py", "expected_result":"py"})
    tests.append({"file_path":"/folder/file", "expected_result":""})
    tests.append({"file_path":"/file.py", "expected_result":"py"})
    tests.append({"file_path":"file.py", "expected_result":"py"})
    tests.append({"file_path":"file", "expected_result":""})

    for test in tests:
        assert files.extract_ext(file_path=test["file_path"]) == test["expected_result"]
