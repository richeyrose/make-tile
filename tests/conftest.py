import pytest
import bpy

@pytest.fixture
def bpy_module(cache):
    return cache.get("bpy_module", None)

@pytest.fixture
def fake_context():
    scene = bpy.data.scenes.new('fake_scene')
    view_layer = bpy.data.scenes['fake_scene'].view_layers[0]
    return {
        'scene': scene,
        'view_layer': view_layer}