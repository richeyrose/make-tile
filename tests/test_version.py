import pytest
from addon_helper import get_version


def test_versionID_pass(bpy_module):
    expect_version = (0, 0, 29)
    return_version = get_version(bpy_module)
    assert expect_version == return_version


def test_versionID_fail(bpy_module):
    expect_version = (0, 1, 1)
    return_version = get_version(bpy_module)
    assert not expect_version == return_version
