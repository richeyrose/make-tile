import pytest
import bmesh
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

@pytest.fixture
def bm_cube():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    return bm

@pytest.fixture
def cube():
    mesh = bpy.data.meshes.new("cube_mesh")
    obj = bpy.data.objects.new("test_cube", mesh)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bm.to_mesh(mesh)
    bm.free()
    bpy.context.layer_collection.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

@pytest.fixture
def straight_wall():
    scene = bpy.context.scene
    scene_props = scene.mt_scene_props
    scene_props.tile_type = "STRAIGHT_WALL"
    bpy.ops.object.make_straight_wall(
        refresh=True,
        main_part_blueprint = 'OPENLOCK',
        base_blueprint = 'OPENLOCK')
    return bpy.data.collections['straight_wall']

