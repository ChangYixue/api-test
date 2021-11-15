# -*- coding:utf-8 -*-

import logging
import logging.config
import json
import os
import os.path

import yaml

import api

import copy

_env = None
_instance = None
_api_descriptor = None
_api_descriptor_depend = None
_all_testcases = None
_all_testcases_depend = None
_token = None
_project_root = os.path.dirname(__file__)

logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "root": {"level": "DEBUG", "handlers": ["console"]},
        "formatters": {
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(pathname)s#%(lineno)d:\n %(message)s"
            },
            "concise": {"format": "%(levelname)s %(asctime)s %(message)s"},
            "lean": {"format": "%(asctime)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "lean",
            },
        },
    }
)


def setup():
    global _all_testcases, _api_descriptor
    if _all_testcases:
        return

    env = os.getenv('ENV', None)
    if not env or env not in ('stage', 'sandbox', 'prod', ):
        raise Exception('Environment is not configured. Sould be stage, sandbox, or prod.')
    _load_api_dsl(env)  # 加载接口配置信息（metadata/api.yml）
    _load_api_dsl_depend(env)
    _bootstrap(env)  # 登录后，获取access_token


# 加载接口配置信息（metadata/api.yml）
def _load_api_dsl(env):
    global _env, _api_descriptor, _all_testcases
    api_dsl = os.path.join('metadata', 'api.yml')
    with open(api_dsl, 'r', encoding='utf-8') as f:
        dsl = yaml.full_load(f)  # dsl是dict类型，存储的是api.yml中所有的接口信息

        _env = dsl['environments'][env]  # 运行环境相对应的登录接口信息，参数env可选项包括：sandbox，prod和stage（在tox.ini中配置）
        del dsl['environments']

        _api_descriptor = dict()  # 存储api.yml中接口信息，除了跳过（skip_test）和环境配置（environments）的信息
        testcases = list()  # 存储接口名称（api_name）和描述（description）
        for key, api_dsl in dsl.items():
            if (('skip_test' in api_dsl and api_dsl['skip_test'])
                    or ('depend_on' in api_dsl)
                    or ('enabled_only' in api_dsl and api_dsl['enabled_only'] !=env)):
                continue
            desc = api_dsl['description'] if 'description' in api_dsl else ''

            testcases.append((key, desc, ),)
            _api_descriptor[key] = api_dsl
        # print(type(_api_descriptor), json.dumps(_api_descriptor, indent=2, ensure_ascii=False, sort_keys=False))
        # print(_api_descriptor['contact_edit'])
        _all_testcases = tuple(testcases)


# 加载有接口依赖的接口的配置信息（metadata/api.yml）
def _load_api_dsl_depend(env):
    global _env, _api_descriptor_depend, _all_testcases_depend
    api_dsl = os.path.join('metadata', 'api.yml')
    with open(api_dsl, 'r', encoding='utf-8') as f:
        dsl = yaml.full_load(f)  # dsl是dict类型，存储的是api.yml中所有的接口信息

        _env = dsl['environments'][env]  # 运行环境相对应的登录接口信息，参数env可选项包括：sandbox，prod和stage（在tox.ini中配置）
        del dsl['environments']

        _api_descriptor_depend = dict()  # 存储api.yml中接口信息，除了跳过（skip_test）和环境配置（environments）的信息
        testcases = list()  # 存储接口名称（api_name）和描述（description）
        for key, api_dsl in dsl.items():
            if (('skip_test' in api_dsl and api_dsl['skip_test'])
                    or ('depend_on' not in api_dsl)
                    or ('enabled_only' in api_dsl and api_dsl['enabled_only'] !=env)):
                continue
            desc = api_dsl['description'] if 'description' in api_dsl else ''

            testcases.append((key, desc, ),)
            _api_descriptor_depend[key] = api_dsl
        _all_testcases_depend = tuple(testcases)


# 登录后，获取access_token
def _bootstrap(env):
    global _env
    api_dsl = _env['bootstrap']  # 运行环境相对应的登录接口信息
    api_dsl = resolve('bootstrap', api_dsl)
    api_dsl = api_dsl[0]
    resp = api.call(api_dsl['url'], api_dsl['method'], api_dsl['params'], api_dsl['headers'])
    if resp.status_code == 200:
        result = resp.json()
        if result['success'] == True:
            global _access_token
            _access_token = result['access_token']
            return

    raise Exception('Login failed')


def list_testcases():
    return _all_testcases


def lookup(api_name):
    global _api_descriptor
    return _api_descriptor[api_name]


def lookup_depend(api_name):
    global _api_descriptor_depend
    return _api_descriptor_depend[api_name]


def access_token():
    return _token


# 处理各种类型的接口信息中的url、method、params和headers
def resolve(name, dsl):
    env = os.getenv('ENV', None)
    endpoint = _env['endpoint']  # 运行环境的url
    enable_only = _env['bootstrap']['enabled_only'] if 'enabled_only' in dsl else None
    if enable_only and enable_only != env:
        return None

    url = '%s%s' % (_env['endpoint'], dsl['url'])  # 拼接完整的接口url
    category = dsl['category'] if 'category' in dsl else ''  # 接口类型
    path_comp = [_project_root, 'fixtures', env, ]
    if category:
        path_comp.append(category)
    path_comp.append('%s.json' % name)  # "fixtures/测试环境"下的json文件，命名规范是"api_name.json"
    fixture_file = os.path.join(*path_comp)  # 拼接测试数据的文件路径
    api = {
        'url': url,
        'method': dsl['method'],
        'params': dict(),
        'headers': dict(),
    }
    if 'headers' in dsl:
        api['headers'].update(dsl['headers'])
    if 'params' in dsl:
        api['params'].update(dsl['params'])

    disable_auth = dsl['disable_auth'] if 'disable_auth' in dsl else False
    if not disable_auth:  # 处理非登录接口的headers
        global _access_token
        api['headers']['Authorization'] = 'Bearer %s' % _access_token
        api['headers']['version'] = "5.11.0"

    apis = []
    if not os.path.exists(fixture_file):
        apis.append(api)
    else:  # 处理存在测试数据的接口
        with open(fixture_file, encoding='utf-8') as f:
            fixtures = json.load(f)
            if isinstance(fixtures, dict):
                fixtures = [fixtures]
            for fixture in fixtures:
                # api_copy = api.copy()
                api_copy = copy.deepcopy(api)
                if 'headers' in fixture:
                    api_copy['headers'].update(fixture['headers'])
                if 'params' in fixture:
                    api_copy['params'].update(fixture['params'])
                apis.append(api_copy)

    return apis


if __name__ == "__main__":
    _load_api_dsl("sandbox")
