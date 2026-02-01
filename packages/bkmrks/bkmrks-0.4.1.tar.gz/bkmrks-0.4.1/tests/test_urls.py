from bkmrks import urls
import pytest

def test_ensure_domain():
    tests = []
    tests.append({"url":"", "domain":"https://domain.com", "expected_result":"https://domain.com"})
    tests.append({"url":"/", "domain":"https://domain.com", "expected_result":"https://domain.com/"})
    tests.append({"url":"?param=1", "domain":"https://domain.com", "expected_result":"https://domain.com?param=1"})
    tests.append({"url":"/?param=1", "domain":"https://domain.com", "expected_result":"https://domain.com/?param=1"})
    tests.append({"url":"#anchor", "domain":"https://domain.com", "expected_result":"https://domain.com#anchor"})
    tests.append({"url":"/#anchor", "domain":"https://domain.com", "expected_result":"https://domain.com/#anchor"})
    tests.append({"url":"path", "domain":"https://domain.com", "expected_result":"https://domain.com/path"})
    tests.append({"url":"/path", "domain":"https://domain.com", "expected_result":"https://domain.com/path"})
    tests.append({"url":"/path", "domain":"https://domain.com", "expected_result":"https://domain.com/path"})
    tests.append({"url":"https://domain.com/path", "domain":"https://otherdomain.com", "expected_result":"https://domain.com/path"})
    tests.append({"url":"https://domain.com/path", "domain":"https://domain.com", "expected_result":"https://domain.com/path"})
    tests.append({"url":"https://domain.com/path", "domain":"", "expected_result":"https://domain.com/path"})
    tests.append({"url":"/path", "domain":"https://domain.com/other-path", "expected_result":"https://domain.com/path"})

    for test in tests:
        assert urls.ensure_domain(url=test["url"], domain=test["domain"]) == test["expected_result"]

    with pytest.raises(TypeError):
        urls.ensure_domain(url="/path")

    with pytest.raises(ValueError):
        urls.ensure_domain(url="/path",domain="not-a-domain.com")

def test_get_name_from_domain():
    with pytest.raises(TypeError):
        urls.get_name_from_domain()
    with pytest.raises(ValueError):
        urls.get_name_from_domain(url="testing.com.br")

    tests = []
    tests.append({"expected_result":"testing",         "url":"http://www.testing.com.br"})
    tests.append({"expected_result":"testing",         "url":"http://testing.com.br"})
    tests.append({"expected_result":"testing",         "url":"http://testing.com"})
    tests.append({"expected_result":"testing",         "url":"http://testing.cc"})
    tests.append({"expected_result":"google_gservice", "url":"http://gservice.google.com"})
    tests.append({"expected_result":"google_gservice", "url":"http://subdomain.gservice.google.com"})
    for test in tests:
        assert urls.get_name_from_domain(url=test["url"]) == test["expected_result"]

def test_extract_domain_from_url():
    with pytest.raises(TypeError):
        urls.extract_domain_from_url()

    tests = []
    tests.append({"url":"http://www.testing.com.br", "expected_result":"http://www.testing.com.br"})
    tests.append({"url":"http://www.testing.com.br/path?param1#anchor", "expected_result":"http://www.testing.com.br"})
    tests.append({"url":"www.testing.com.br", "expected_result":""})
    tests.append({"url":"/asdf", "expected_result":""})

    for test in tests:
        assert urls.extract_domain_from_url(url=test["url"]) == test["expected_result"]

def test_read_from_url_or_path():
    #TODO: To implement
    return
