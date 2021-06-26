from math import inf, tan, radians, acos, pi, modf
import bmesh
import bpy
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree
from ..utils.selection import in_bbox

def bmesh_array(
    source_obj,
    start_cap=None,
    end_cap=None,
    count=0,
    use_relative_offset=True,
    relative_offset_displace=(0, 0, 0),
    use_constant_offset=False,
    constant_offset_displace=(0, 0, 0),
    use_merge_vertices=True,
    merge_threshold=0.0001,
    fit_type='FIT_LENGTH',
    fit_length=0):
    """A bmesh version of the array modifier. 
    
    Produces a bmesh that has the modifier applied. This is much faster
    than calling depsgraph_update_get() on scenes with more than a few polys.

    Args:
        source_obj (bpy.types.Object): Source object to generate bmesh from
        start_cap (bpy.types.Object, optional): Object to use as start cap.Defaults to None.
        end_cap (bpy.types.Object, optional): Object to use as end cap. Defaults to None.
        count (int, optional): Number of times to array item if using Fixed Count. Defaults to 0.
        use_relative_offset (bool, optional): Offset relative to the object's bounding box. Defaults to True.
        relative_offset_displace (tuple, optional): Offset amount. Defaults to (0, 0, 0).
        use_constant_offset (bool, optional): Offset by a fixed amount. Defaults to False.
        constant_offset_displace (tuple, optional): Offset amount. Defaults to (0, 0, 0).
        use_merge_vertices (bool, optional): Merge vertices. Defaults to True.
        merge_threshold (int, optional): [description]. Defaults to 0.0001.
        fit_type (Enum in ['FIT_LENGTH', 'FIXED'], optional): Array length calculation method. Defaults to 'FIT_LENGTH'.
        fit_length (int, optional): Length to fit array within if using 'FIT_LENGTH'. Defaults to 0.

    Returns:
        bpy.types.bmesh: Bmesh
    """

    offset = Vector((0, 0, 0))
    
    if use_relative_offset:
        dims = source_obj.dimensions.copy()
        offset = Vector(relative_offset_displace) * Vector(dims)

    if use_constant_offset:
        offset = offset + Vector((constant_offset_displace))

    if fit_type == 'FIT_LENGTH':
        dupes=[]
        if offset[0]:
            dupes.append(modf(fit_length / offset[0])[1])
        if offset[1]:
            dupes.append(modf(fit_length / offset[1])[1])
        if offset[2]:
            dupes.append(modf(fit_length / offset[2])[1])
        if dupes:
            count = min(dupes)

    if count:
        mesh = source_obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        source_geom = bm.verts[:] + bm.edges[:] + bm.faces[:]

        i = 0
        while i < count:
            ret = bmesh.ops.duplicate(
                bm,
                geom=source_geom)
            geom=ret["geom"]
            dupe_verts = [ele for ele in geom if isinstance(ele, bmesh.types.BMVert)]
            del ret
            bmesh.ops.translate(
                bm,
                verts=dupe_verts,
                vec=offset * (i + 1),
                space=source_obj.matrix_world)
            i += 1
        
        if start_cap:
            me_2 = start_cap.data
            bm.from_mesh(me_2)

        if end_cap:
            me_3 = end_cap.data
            bm_2 = bmesh.new()
            bm_2.from_mesh(me_3)
            bmesh.ops.translate(
                bm_2,
                verts=bm_2.verts,
                vec=offset * count,
                space=source_obj.matrix_world)
        
        # create temp mesh because copying from one bmesh to another is fubared
        temp = bpy.data.meshes.new("temp")
        bm_2.to_mesh(temp)
        bm_2.free()
        bm.from_mesh(temp)
        bpy.data.meshes.remove(temp)

        if use_merge_vertices:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_threshold)
        
    return bm

def bm_select_all(bm):
    """Select all verts.

    Args:
        bm (bmesh): bmesh
    """
    for v in bm.verts:
        v.select_set(True)
    bm.select_flush(True)


def bm_deselect_all(bm):
    """Deselect all verts.

    Args:
        bm (bmesh): bmesh
    """
    for v in bm.verts:
        v.select_set(False)
    bm.select_flush(False)


def select_verts_in_bounds(lbound, ubound, buffer, bm):
    """Select vertices within cubical boundary.

    Args:
        lbound (tuple[3]): Lower left corner of bounds
        ubound (tuble[3]): Upper left corner of bounds
        buffer (float): Buffer around bbox
        bm (bmesh): bmesh

    Returns:
        list[bmesh.verts]: List of verts
    """
    vert_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = [in_bbox(lbound, ubound, v, buffer) for v in vert_coords]

    for vert, select in zip(bm.verts, to_select):
        vert.select = select

    return [v for v in bm.verts if v.select]

def select_edges_in_bounds(lbound, ubound, buffer, bm):
    vert_coords = []
    [vert_coords.append([v.co.to_tuple()for v in e.verts]) for e in bm.edges]
    to_select = []
    [to_select.append(all(in_bbox(lbound, ubound, v, buffer)for v in e)) for e in vert_coords]
    for edge_obj, select in zip(bm.edges, to_select):
        edge_obj.select = select
    return [e for e in bm.edges if e.select]

def points_are_inside_bmesh(coords, bm):
    """Test whether points are inside an arbitrary manifold bmesh.

    Args:
        coords list[Vector / tuples /list]: a list of vectors (can also be tuples/lists)
        bm (bMesh): a manifold bmesh with verts and (edge/faces) for which the normals are calculated already. (add bm.normal_update() otherwise)
    Returns:
        list[bool]: a mask list with True if the point is inside the bmesh, False otherwise
    """
    coord_mask = []
    addp = coord_mask.append
    bvh = BVHTree.FromBMesh(bm, epsilon=0.001)

    # return points on polygons
    for co in coords:
        fco, normal, _, _ = bvh.find_nearest(co)
        p2 = fco - Vector(co)
        v = p2.dot(normal)
        # angle = acos(min(max(v, -1), 1)) * 180 / pi
        # addp(angle > 90 + tolerance)
        # addp(not v < 0.0)  # addp(v >= 0.0) ?
        # addp(v >= 0.0)
        addp(v >= 0.0)

    return coord_mask


def assign_verts_to_group(verts, obj, deform_groups, group_name):
    """Assigns verts to vertex group

    Args:
        verts (list[bmesh.verts]): List of verts
        obj (bpy.types.Object): object
        deform_groups (bmesh.types.BMLayerCollection): deform layer. Corresponds to vertex groups
        group_name (string): Vertex group name
    """
    group_index = obj.vertex_groups[group_name].index

    for v in verts:
        if v.is_valid:
            groups = v[deform_groups]
            groups[group_index] = 1

def extrude_translate(bm, local_trans, del_original=True):
    """Extrudes and translates selected verts, edges or faces

    Args:
        bm (bmesh): bmesh
        local_trans (Vector[3]): Local transform vector
        del_original (bool, optional): Whether to delete original faces. Defaults to True.
    """
    # use cursor as turtle
    turtle = bpy.context.scene.cursor

    # work out transform in turtle's local space and convert to global
    local_trans = Vector(local_trans)
    world_trans = turtle.matrix.to_3x3() @ local_trans
    turtle.location = turtle.matrix.translation + world_trans

    if bpy.context.view_layer.objects.active.mt_object_props.penstate is True:
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

            # select extruded faces
            for f in faces:
                f.select_set(True)

# https://blender.stackexchange.com/questions/186067/what-is-the-bmesh-equivalent-to-bpy-ops-mesh-shortest-path-select
class Node:
    """Return a node object that contains list of edges \
     that make up shortest path between two verts.

    Returns:
        dict{vert: BMVert, length: float, shortest_path: list[BMEdge]}: Dict giving shortest path \
        between two verts
    """
    @property
    def edges(self):
        return (e for e in self.vert.link_edges if not e.tag)

    def __init__(self, v):
        self.vert = v
        self.length = inf
        self.shortest_path = []


def bm_shortest_path(bm, v_start, v_target=None):
    """Return shortest path between two verts.

    Args:
        bm (bmesh): bmesh
        v_start (bmesh.vert): start vert
        v_target (bmesh.vert, optional): end vert. Defaults to None.

    Returns:
        dict{BMVert: Node}: Nodes
    """
    for e in bm.edges:
        e.tag = False

    d = {v : Node(v) for v in bm.verts}
    node = d[v_start]
    node.length = 0

    visiting = [node]

    while visiting:
        node = visiting.pop(0)

        if node.vert is v_target:
            return d

        for e in node.edges:
            e.tag = True
            length = node.length + e.calc_length()
            v = e.other_vert(node.vert)

            visit = d[v]
            visiting.append(visit)
            if visit.length > length:
                visit.length = length
                visit.shortest_path = node.shortest_path + [e]

        visiting.sort(key=lambda n: n.length)

    return d


def add_vertex_to_intersection(bm, edges):
    bm_deselect_all(bm)
    if len(edges) == 2:
        [[v1, v2], [v3, v4]] = [[v.co for v in e.verts] for e in edges]

        iv = geometry.intersect_line_line(v1, v2, v3, v4)
        if iv:
            iv = (iv[0] + iv[1]) / 2
            bm.verts.new(iv)

            bm.verts.ensure_lookup_table()

            bm.verts[-1].select = True


def calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness,
        angle):

    #  leg 2
    #   |
    #   |
    #   |_ _ _ leg 1

    #   |      *
    #   |   *  | <- tri_a
    #   |*_ _ _|

    #           _ _ _ _
    #          |      *
    # tri_c -> |   *
    #          |*_ _ _

    # X leg
    # right triangle
    tri_a_angle = angle / 2
    tri_a_adj = leg_1_len
    tri_a_opp = tri_a_adj * tan(radians(tri_a_angle))

    # right triangle
    tri_b_angle = 180 - tri_a_angle - 90
    tri_b_opp = tri_a_opp - thickness
    tri_b_adj = tri_b_opp * tan(radians(tri_b_angle))

    # Y leg
    # right triangle
    tri_c_angle = angle / 2
    tri_c_adj = leg_2_len
    tri_c_opp = tri_c_adj * tan(radians(tri_c_angle))

    tri_d_angle = 180 - tri_c_angle - 90
    tri_d_opp = tri_c_opp - thickness
    tri_d_adj = tri_d_opp * tan(radians(tri_d_angle))

    triangles = {
        'a_adj': tri_a_adj,  # leg 1 outer leg length
        'b_adj': tri_b_adj,  # leg 1 inner leg length
        'c_adj': tri_c_adj,  # leg 2 outer leg length
        'd_adj': tri_d_adj}  # leg 2 inner leg length

    return triangles