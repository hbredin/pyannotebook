#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Hervé Bredin.
# Distributed under the terms of the Modified BSD License.

import pytest

from ..labels import LabelsWidget


def test_example_creation_blank():
    w = LabelsWidget()
    assert w.labels == dict()
