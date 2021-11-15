# -- coding: utf-8 --

import requests

session = requests.Session()


def call(url, method, params=None, headers=None):
    method = method.lower()
    if method not in ('get', 'post'):
        raise Exception('Invalid request method [%s], should be "get" or "post"' % method)

    if method == 'get':
        return get(url, params, headers)
    elif method == 'post':
        return post(url, params, headers)
    else:
        raise Exception('Should not run into here')


def get(url, params, headers=None):
    resp = session.get(url, params=params, headers=headers)
    return resp


def post(url, params, headers=None):
    resp = session.post(url, data=params, headers=headers)
    return resp
