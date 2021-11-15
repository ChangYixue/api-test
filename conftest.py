# -*- coding: utf-8 -*-
import pytest

import settings


def pytest_sessionstart(session):
    settings.setup()
