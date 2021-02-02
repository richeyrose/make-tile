import os
import bpy
from ..utils.registration import get_prefs


class MT_OT_Ungridify(bpy.types.Operator):
    """Removes a gridify grid if one has been added to the active material"""
    bl_idname = "material.ungridify"
    bl_label = "Ungridify"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is not None and obj.active_material is not None:
            nodes = obj.active_material.node_tree.nodes
            if 'mt_gridify' in nodes:
                return True
        return False

    def execute(self, context):
        # get material node tree
        tree = context.object.active_material.node_tree
        nodes = tree.nodes
        final_node = nodes['final_node']
        gridify_node = nodes['mt_gridify']
        previous_node_socket = gridify_node.inputs['mat_input'].links[0].from_socket

        # link previous_node_socket to final_node input
        tree.links.new(previous_node_socket, final_node.inputs[0])

        # sever link from gridify node to previous node socket
        tree.links.remove(gridify_node.inputs['mat_input'].links[0])

        # delete nodes connected to gridify node
        for node_input in gridify_node.inputs:
            for link in node_input.links:
                nodes.remove(link.from_node)

        # delete frames
        frame_names = ['w_grid_properties', 'x_grid_location', 'y_grid_scale', 'z_grid_rotation']
        for node in nodes:
            if node.name in frame_names:
                nodes.remove(node)

        nodes.remove(gridify_node)
        return {'FINISHED'}


class MT_OT_Gridify(bpy.types.Operator):
    """Takes any MakeTile material and adds a customisable grid to it."""
    bl_idname = "material.gridify"
    bl_label = "Gridify"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is not None and obj.active_material is not None:
            nodes = obj.active_material.node_tree.nodes
            if 'final_node' in nodes and 'mt_gridify' not in nodes:
                return True
        return False

    def execute(self, context):
        prefs = get_prefs()

        # get material node tree
        tree = context.object.active_material.node_tree
        nodes = tree.nodes
        final_node = nodes['final_node']

        # node that is currently linked to final_node
        previous_node_socket = final_node.inputs[0].links[0].from_socket

        # load gridify node group
        try:
            gridify_tree = bpy.data.node_groups['gridify']
        except KeyError:
            groups_path = os.path.join(
                prefs.assets_path,
                "node_groups",
                "gridify.blend")

            with bpy.data.libraries.load(groups_path) as (data_from, data_to):
                data_to.node_groups = ['gridify']

            gridify_tree = data_to.node_groups[0]

        # add an empty node group to material
        gridify_group = tree.nodes.new('ShaderNodeGroup')
        gridify_group.name = 'mt_gridify'

        # set node tree to gridify
        gridify_group.node_tree = bpy.data.node_groups[gridify_tree.name]
        # gridify node output
        gridify_output = gridify_group.outputs['gridified_mat']
        # gridify material input
        gridify_mat_input = gridify_group.inputs['mat_input']
        # link gridify output to final_node input
        tree.links.new(gridify_output, final_node.inputs[0])
        # link gridify input to previous node input
        tree.links.new(previous_node_socket, gridify_mat_input)

        inputs_frame = nodes['editable_inputs']

        # create node frames to make grid properties editable in UI
        frames = []
        i = 0
        while i < 4:
            frame = tree.nodes.new('NodeFrame')
            frame.parent = inputs_frame
            frames.append(frame)
            i += 1

        frame_names = ['w_grid_properties', 'x_grid_location', 'y_grid_scale', 'z_grid_rotation']
        frame_labels = ['Grid Properties', 'Grid Location', 'Grid Scale', 'Grid Rotation']

        i = 0
        while i < 4:
            frames[i].name = frame_names[i]
            frames[i].label = frame_labels[i]
            i += 1

        # create input nodes to control grid properties
        input_nodes = []
        i = 0
        while i < 10:
            input_nodes.append(tree.nodes.new('ShaderNodeValue'))
            i += 1

        # thickness
        input_nodes[0].name = input_nodes[0].label = 'Thickness'
        output = input_nodes[0].outputs[0]
        output.default_value = 0.015
        tree.links.new(output, gridify_group.inputs['grid_thickness'])
        input_nodes[0].parent = nodes['w_grid_properties']

        # transforms
        node_labels = ['X', 'Y', 'Z']
        node_names = ['loc_x', 'loc_y', 'loc_z']

        # location
        i = 1
        j = 0
        while i < 4:
            node = input_nodes[i]
            node.name = node_names[j]
            node.label = node_labels[j]
            output = node.outputs[0]
            output.default_value = 1
            tree.links.new(output, gridify_group.inputs[node.name])
            node.parent = nodes['x_grid_location']
            i += 1
            j += 1

        # rotation
        node_names = ['rot_x', 'rot_y', 'rot_z']

        i = 4
        j = 0
        while i < 7:
            node = input_nodes[i]
            node.name = node_names[j]
            node.label = node_labels[j]
            output = node.outputs[0]
            output.default_value = 0
            tree.links.new(output, gridify_group.inputs[node.name])
            node.parent = nodes['z_grid_rotation']
            i += 1
            j += 1

        # scale
        node_names = ['scale_x', 'scale_y', 'scale_z']

        i = 7
        j = 0
        while i < 10:
            node = input_nodes[i]
            node.name = node_names[j]
            node.label = node_labels[j]
            output = node.outputs[0]
            output.default_value = 1
            tree.links.new(output, gridify_group.inputs[node.name])
            node.parent = nodes['y_grid_scale']
            i += 1
            j += 1

        return {'FINISHED'}
