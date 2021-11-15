# -- coding: utf-8 --

import logging

import pytest

import api
import settings

address_list = {}
address_id = None
set_white_address = ['email_send_code', 'set_white_address']


# 获取地址列表
@pytest.mark.dependency(name="get_address_list")
@pytest.mark.parametrize('api_name', ['contact_list'])
def test_contact_list(api_name):
    global address_list
    api_dsl = settings.lookup_depend(api_name)
    requests = settings.resolve(api_name, api_dsl)
    req = requests[0]

    resp = api.call(req['url'], req['method'], req['params'], req['headers'])
    result = resp.json()

    assert resp.status_code == 200
    if result['success'] == False:
        logging.debug(resp.text)
    assert result['success']
    for r in result['result']:
        address = r['address']
        address_list[address] = r['address_id']


# 添加地址后获取address_id
@pytest.mark.dependency(depends=["get_address_list"])
@pytest.mark.dependency(name="get_address_id")
@pytest.mark.parametrize('api_name', ['contact_add'])
def test_contact_add(api_name):
    global address_id,address_list
    api_dsl = settings.lookup_depend(api_name)
    requests = settings.resolve(api_name, api_dsl)
    req = requests[0]

    # 若列表中存在地址，则删除后再添加
    if req['params']['address'] in address_list:
        remove_requests = settings.resolve('contact_remove', settings.lookup_depend('contact_remove'))
        remove_req = remove_requests[0]
        remove_req['params'].update(
            {
                'address_id': address_list[req['params']['address']],
            }
        )
        api.call(remove_req['url'], remove_req['method'], remove_req['params'], remove_req['headers'])

    resp = api.call(req['url'], req['method'], req['params'], req['headers'])
    result = resp.json()

    assert resp.status_code == 200
    if result['success'] == False:
        logging.debug(resp.text)
    assert result['success']

    address_id = result['result']['address_id']


# 删除地址
@pytest.mark.dependency(depends=["get_address_id"])
@pytest.mark.parametrize('api_name', ['contact_remove'])
def test_contact_remove(api_name):
    global address_id
    api_dsl = settings.lookup_depend(api_name)
    requests = settings.resolve(api_name, api_dsl)
    req = requests[0]

    req['params'].update(
        {
            "address_id": address_id,
        }
    )

    resp = api.call(req['url'], req['method'], req['params'], req['headers'])
    result = resp.json()

    assert resp.status_code == 200
    if result['success'] == False:
        logging.debug(resp.text)
    assert result['success']

