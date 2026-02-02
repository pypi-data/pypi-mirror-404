from bkmrks import md

def test_md_hr():
    assert "\n---" == md.md_hr()

def test_md_a_img():
    tests = []

    url = "https://testing.url"
    name = "name_testing"
    img = ""
    item = {"url":url, "name":name, "img":img, }

    expected_result = f'\n[![{name}]({img})]({url} "{name}")'

    tests.append({"item":item, "expected_result":expected_result})

    name = ""
    img = ""
    item = {"name":name, "img":img, }
    expected_result = ""
    tests.append({"item":item, "expected_result":""})

    item = ""
    expected_result = ""
    tests.append({"item":item, "expected_result":""})

    url = "https://testing.url"
    name = "name_testing"
    img = ""
    item = {"url":url, "name":name, "img":img, }

    expected_result = f'\n[![{name}]({img})]({url} "{name}")'

    tests.append({"item":item, "expected_result":expected_result})

    for test in tests:
        assert test["expected_result"] == md.md_a_img(item=test["item"])
