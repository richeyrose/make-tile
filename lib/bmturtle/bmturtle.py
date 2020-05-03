from math import radians
import bpy
import bmesh
from mathutils import Vector


def create_turtle(name, vert_groups=None):
    cursor = bpy.context.scene.cursor
    # create new empty turtle world
    mesh = bpy.data.meshes.new("mesh")
    obj = bpy.data.objects.new(name, mesh)
    obj['penstate'] = True

    # create vertex groups
    if vert_groups:
        for i in range(len(vert_groups)):
            obj.vertex_groups.new(name=vert_groups[i])

    # link object to active collection
    bpy.context.layer_collection.collection.objects.link(obj)

    # make object active
    bpy.context.view_layer.objects.active = obj

    # update depgraph
    bpy.context.view_layer.update()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    vert = bmesh.ops.create_vert(bm, co=cursor.location)
    vert['vert'][0].select = True
    return bm, obj


def pu(bm):
    for v in bm.verts:
        v.select_set(False)
    bm.select_flush(False)

    bpy.context.view_layer.objects.active['penstate'] = False


def pd(bm):
    bpy.context.view_layer.objects.active['penstate'] = True


def fd(bm, distance, del_original=True):
    extrude_translate(bm, (0.0, distance, 0.0), del_original)


def bk(bm, distance, del_original=True):
    extrude_translate(bm, (0.0, -distance, 0.0), del_original)


def up(bm, distance, del_original=True):
    extrude_translate(bm, (0.0, 0.0, distance), del_original)


def dn(bm, distance, del_original=True):
    extrude_translate(bm, (0.0, 0.0, -distance), del_original)


def ri(bm, distance, del_original=True):
    extrude_translate(bm, (distance, 0.0, 0.0), del_original)


def lf(bm, distance, del_original=True):
    extrude_translate(bm, (-distance, 0.0, 0.0), del_original)


def extrude_translate(bm, local_trans, del_original=True):
    # use cursor as turtle
    turtle = bpy.context.scene.cursor

    # work out transform in turtle's local space and convert to global
    local_trans = Vector(local_trans)
    world_trans = turtle.matrix.to_3x3() @ local_trans
    turtle.location = turtle.matrix.translation + world_trans

    if bpy.context.view_layer.objects.active['penstate'] is 1:
        if bm.select_mode == {'VERT'}:
            bm.select_flush(True)
            # get selected verts
            selected = [v for v in bm.verts if v.select]
            ret = bmesh.ops.extrude_vert_indiv(bm, verts=selected)
            verts = ret['verts']

            # translate along turtle's local Y
            bmesh.ops.translate(bm, vec=(world_trans), verts=verts)

            # deselect original verts
            for v in bm.verts:
                v.select_set(False)
            bm.select_flush(False)

            # select extruded verts
            for v in verts:
                v.select_set(True)
            bm.select_flush(True)

        if bm.select_mode == {'EDGE'}:
            bm.select_flush(True)
            selected = [e for e in bm.edges if e.select]
            ret = bmesh.ops.extrude_edge_only(bm, edges=selected)
            geom = ret["geom"]
            edges = [e for e in geom
                     if isinstance(e, bmesh.types.BMEdge)]
            verts = [v for v in geom
                     if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=(world_trans), verts=verts)

            # deselect original edges
            for e in bm.edges:
                e.select_set(False)
            for v in bm.verts:
                v.select_set(False)
            bm.select_flush(False)

            # select extruded edges
            for e in edges:
                e.select_set(True)
            bm.select_flush(True)

        if bm.select_mode == {'FACE'}:
            bm.select_flush(True)
            sel_f = [f for f in bm.faces if f.select]
            ret = bmesh.ops.extrude_face_region(bm, geom=sel_f)
            geom = ret["geom"]

            faces = [f for f in geom
                     if isinstance(f, bmesh.types.BMFace)]
            edges = [e for e in geom
                     if isinstance(e, bmesh.types.BMEdge)]
            verts = [v for v in geom
                     if isinstance(v, bmesh.types.BMVert)]

            bmesh.ops.translate(bm, vec=(world_trans), verts=verts)

            if del_original is True:
                bmesh.ops.delete(bm, geom=sel_f, context='FACES')

            # deselect original faces and edges
            bm_deselect_all(bm)

            #select extruded faces
            for f in faces:
                f.select_set(True)


def lt(degrees):
    turtle = bpy.context.scene.cursor
    turtle.rotation_euler = (
        turtle.rotation_euler[0],
        turtle.rotation_euler[1],
        turtle.rotation_euler[2] + radians(degrees))


def rt(degrees):
    lt(-degrees)


def home(obj):
    turtle = bpy.context.scene.cursor
    turtle.location = obj.location
    turtle.rotation_euler = obj.rotation_euler


def finalise_turtle(bm, obj):
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()


def bm_select_all(bm):
    for v in bm.verts:
        v.select_set(True)
        bm.select_flush(True)


def bm_deselect_all(bm):
    for v in bm.verts:
        v.select_set(False)
    bm.select_flush(False)


def draw_cuboid(dimensions, name):
    bm, obj = create_turtle(name=name)

    bm.select_mode = {'VERT'}

    fd(bm, dimensions[1])
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)
    ri(bm, dimensions[0])
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, dimensions[2], False)
    pu(bm)
    home(obj)
    finalise_turtle(bm, obj)

    return obj
