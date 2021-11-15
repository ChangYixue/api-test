# -- coding: utf-8 --

import logging

import pytest

import api
import settings


@pytest.mark.parametrize('api_name, description',[case for case in settings.list_testcases()])
def test_all(api_name, description):
    api_dsl = settings.lookup(api_name)
    requests = settings.resolve(api_name, api_dsl)

    for req in requests:
        resp = api.call(req['url'], req['method'], req['params'], req['headers'])
        result = resp.json()
        # logging.debug(resp.text)
        assert resp.status_code == 200
        if result['success'] == False:
            logging.debug(resp.text)
        assert result['success']

        result = result['result']
        if 'expect' in api_dsl:
            expectations = api_dsl['expect']
            _evaluate(result, expectations)


def _evaluate(result, expectations):
    for key, val in expectations.items():
        if 'exists' == key:
            for field in val:
                assert field in result
        if 'equals' == key:
            assert result[key] == val

