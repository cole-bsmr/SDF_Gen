bl_info = {
    "name" : "SDF_Gen",
    "author" : "Cole Biesemeyer", 
    "description" : "Creates SDF files.",
    "blender" : (4, 2, 0),
    "version" : (1, 1, 0),
    "location" : "Editors -> SDF_Gen",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "3D View" 
}


import bpy
import bpy.utils.previews
import mathutils
import math
import bmesh
import numpy as np
import blf
import os
from mathutils import Vector, Euler
import xml.etree.ElementTree as ET
import re
from mathutils import Vector
import mathutils  # Import mathutils to handle transformations


addon_keymaps = {}
_icons = None
box = {'sna_sourcelocation': [], }
collider = {'sna_ray_origin_global': None, 'sna_cylindercapobj': None, 'sna_activeobject': None, 'sna_selection': None, 'sna_collidername': None, 'sna_activeobjectcollider': None, 'sna_userscollection': None, 'sna_moveoutcollection': None, 'sna_collidercollectionexists': False, 'sna_minbb': None, 'sna_joinedobj': None, 'sna_minboxname': '', 'sna_isincolliders': False, 'sna_users_collection': None, 'sna_collision_collections': None, }
cylinder = {'sna_actobjcylgen': '', 'sna_cylsource': None, 'sna_cylusercollection': None, 'sna_colliderscollectionexists': False, 'sna_objcollection': None, }
export_sdf = {'sna_stored_matrix': None, 'sna_storedlocation': None, 'sna_storedrotation': None, }
genface = {'sna_genfaceactobj': None, 'sna_rayfail': False, }
genmesh = {'sna_collidercollection': None, 'sna_incolliderscollection': False, 'sna_colliderscollectionexist': False, }
joint = {'sna_jointmatrix': None, }
sdf_gen = {'sna_errors': [], }
ui = {'sna_decimateexists': False, }


def sna_update_sna_cylrad_0B327(self, context):
    sna_updated_prop = self.sna_cylrad
    self.dimensions = (self.sna_cylrad, self.sna_cylrad, self.dimensions[2])


def sna_update_sna_collidermargin_4105F(self, context):
    sna_updated_prop = self.sna_collidermargin
    for i_81921 in range(len(bpy.data.objects)):
        for i_ADD02 in range(len(bpy.data.objects[i_81921].modifiers)):
            if 'ColliderMargin' in str(bpy.data.objects[i_81921].modifiers[i_ADD02]):
                bpy.data.objects[i_81921].modifiers['ColliderMargin'].thickness = bpy.context.scene.sna_collidermargin


def sna_popup_message_45189_521B9(Title, Body, Named_Icon):
    txt = Title
    bdy = Body
    ico = Named_Icon
    # Create a new dialogue box

    def popup_callback(self, context):
        self.layout.label(text=bdy)
    bpy.context.window_manager.popup_menu(
        title=txt,
        icon=ico,
        draw_func=popup_callback,
    )
    return


def property_exists(prop_path, glob, loc):
    try:
        eval(prop_path, glob, loc)
        return True
    except:
        return False


class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def sna_update_sna_collidervisibiity_8151C(self, context):
    sna_updated_prop = self.sna_collidervisibiity
    for i_EEBEC in range(len(bpy.data.collections)):
        if '_colliders' in bpy.data.collections[i_EEBEC].name:
            bpy.data.collections[i_EEBEC].hide_viewport = (not bpy.context.scene.sna_collidervisibiity)


def sna_update_sna_jointvisibility_80CDE(self, context):
    sna_updated_prop = self.sna_jointvisibility
    for i_ADE93 in range(len(bpy.context.scene.objects)):
        if '_joint' in bpy.context.scene.objects[i_ADE93].name:
            bpy.context.scene.objects[i_ADE93].hide_viewport = (not bpy.context.scene.sna_jointvisibility)
            for i_7C635 in range(len(bpy.context.scene.objects[i_ADE93].children_recursive)):
                bpy.context.scene.objects[i_ADE93].children_recursive[i_7C635].hide_viewport = (not bpy.context.scene.sna_jointvisibility)


def sna_update_sna_limits_lower_AAA88(self, context):
    sna_updated_prop = self.sna_limits_lower
    for i_F3CB3 in range(len(self.children)):
        if 'lower_limit' in str(self.children[i_F3CB3].name):
            bpy.context.scene.sna_lower_limit = self.children[i_F3CB3]
            bpy.context.scene.sna_lower_limit.rotation_euler = (bpy.context.scene.sna_lower_limit.rotation_euler[0], sna_updated_prop, bpy.context.scene.sna_lower_limit.rotation_euler[2])


def sna_update_sna_limits_upper_9ECDF(self, context):
    sna_updated_prop = self.sna_limits_upper
    for i_CF955 in range(len(self.children)):
        if 'upper_limit' in str(self.children[i_CF955].name):
            bpy.context.scene.sna_upper_limit = self.children[i_CF955]
            bpy.context.scene.sna_upper_limit.rotation_euler = (bpy.context.scene.sna_upper_limit.rotation_euler[0], sna_updated_prop, bpy.context.scene.sna_upper_limit.rotation_euler[2])


def sna_update_sna_limits_upper_distance_183F5(self, context):
    sna_updated_prop = self.sna_limits_upper_distance
    for i_EE797 in range(len(self.children)):
        if 'upper_limit_distance' in str(self.children[i_EE797].name):
            bpy.context.scene.sna_upper_limit = self.children[i_EE797]
            bpy.context.scene.sna_upper_limit.location = (bpy.context.scene.sna_upper_limit.location[0], float((0.0, 0.0, 0.0)[1] + sna_updated_prop), bpy.context.scene.sna_upper_limit.location[2])


def sna_update_sna_limits_lower_distance_80B68(self, context):
    sna_updated_prop = self.sna_limits_lower_distance
    for i_14052 in range(len(self.children)):
        if 'lower_limit_distance' in str(self.children[i_14052].name):
            bpy.context.scene.sna_lower_limit = self.children[i_14052]
            bpy.context.scene.sna_lower_limit.location = (bpy.context.scene.sna_lower_limit.location[0], float((0.0, 0.0, 0.0)[1] + sna_updated_prop), bpy.context.scene.sna_lower_limit.location[2])
            print(str((0.0, 0.0, 0.0)[1]), str(sna_updated_prop), str(float((0.0, 0.0, 0.0)[1] + sna_updated_prop)))


def sna_update_sna_iscontinuous_810A8(self, context):
    sna_updated_prop = self.sna_iscontinuous
    for i_9DF2E in range(len(self.children_recursive)):
        if sna_updated_prop:
            self.children_recursive[i_9DF2E].hide_viewport = True
        else:
            self.children_recursive[i_9DF2E].hide_viewport = False


def ShowMessageBoxer(title, icon, message):
    scene = bpy.context.scene
    # Access the 2D cursor location
    cursor_location = scene.cursor.location 

    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


class SNA_UL_display_collection_list001_E2509(bpy.types.UIList):

    def draw_item(self, context, layout, data, item_E2509, icon, active_data, active_propname, index_E2509):
        row = layout
        layout.label(text=item_E2509.name, icon_value=0)

    def filter_items(self, context, data, propname):
        flt_flags = []
        for item in getattr(data, propname):
            if not self.filter_name or self.filter_name.lower() in item.name.lower():
                if sna_notactivescene_4FCAA(item):
                    flt_flags.append(self.bitflag_filter_item)
                else:
                    flt_flags.append(0)
            else:
                flt_flags.append(0)
        return flt_flags, []


def display_collection_id(uid, vars):
    id = f"coll_{uid}"
    for var in vars.keys():
        if var.startswith("i_"):
            id += f"_{var}_{vars[var]}"
    return id


class SNA_UL_display_collection_list_1546D(bpy.types.UIList):

    def draw_item(self, context, layout, data, item_1546D, icon, active_data, active_propname, index_1546D):
        row = layout
        layout.prop(item_1546D, 'name', text='', icon_value=0, emboss=False)

    def filter_items(self, context, data, propname):
        flt_flags = []
        for item in getattr(data, propname):
            if not self.filter_name or self.filter_name.lower() in item.name.lower():
                if True:
                    flt_flags.append(self.bitflag_filter_item)
                else:
                    flt_flags.append(0)
            else:
                flt_flags.append(0)
        return flt_flags, []


def sna_update_sna_sceneindex_6B93D(self, context):
    sna_updated_prop = self.sna_sceneindex
    print(bpy.data.scenes[bpy.context.window_manager.sna_sceneindex].name)
    scene_name = bpy.data.scenes[bpy.context.window_manager.sna_sceneindex].name
    #scene_name = "SceneName"  # Replace with your desired scene name
    for window in bpy.context.window_manager.windows:
        window.scene = bpy.data.scenes[scene_name]


def sna_update_sna_visualmaterial_6C149(self, context):
    sna_updated_prop = self.sna_visualmaterial


def sna_update_sna_visualmaterial_E3F9C(self, context):
    sna_updated_prop = self.sna_visualmaterial
    if (self == bpy.context.view_layer.objects.active):
        print('')
        material_name = sna_updated_prop
        # Store the currently selected objects
        selected_objects = bpy.context.selected_objects.copy()
        # Point to materials.blend file
        blend_file_path = bpy.utils.user_resource('EXTENSIONS') + "/user_default/sdf_gen/materials.blend"
        # Function to check if a material already exists in the current blend file

        def material_exists(material_name):
            return material_name in bpy.data.materials
        # Ensure the path is correct and the file exists

        def append_material(material_name):
            try:
                # Check if the material already exists in the current blend file
                if material_exists(material_name):
                    print(f"Material '{material_name}' already exists in the current blend file.")
                else:
                    # Append the material from the specified blend file
                    with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):
                        # Check if the material exists in the source file
                        if material_name in data_from.materials:
                            # Append the material
                            data_to.materials.append(material_name)
                            print(f"Successfully appended material: {material_name}")
                        else:
                            print(f"Material '{material_name}' not found in '{blend_file_path}'")
            except Exception as e:
                print(f"An error occurred: {e}")
        # Remove all materials from each selected object and assign the material

        def assign_material_to_objects(material_name):
            for obj in selected_objects:
                # Clear all materials from the object
                if obj.type == 'MESH':
                    obj.data.materials.clear()
                    # Get the material
                    material = bpy.data.materials.get(material_name)
                    # Update visual_material property
                    if obj.sna_visualmaterial != material_name:
                        obj.sna_visualmaterial = material_name
                    if material:
                        # Ensure the object has a material slot
                        if len(obj.data.materials) == 0:
                            # Create a new material slot if none exist
                            obj.data.materials.append(material)
                        else:
                            # Assign the material to the first material slot
                            obj.data.materials[0] = material
                        print(f"Material '{material_name}' assigned to object: {obj.name}")
                    else:
                        print(f"Material '{material_name}' not found.")
                else:
                    print(f"Object '{obj.name}' is not a mesh.")
        # Example of how to use the functions
        # Replace 'YourMaterialName' with the actual material name when calling the functions
        #material_name = 'YourMaterialName'  # Get this name from user input or other sources
        append_material(material_name)
        assign_material_to_objects(material_name)


class SNA_OT_Box_9D9E4(bpy.types.Operator):
    bl_idname = "sna.box_9d9e4"
    bl_label = "Box"
    bl_description = "Creates a box collider that fits the selected object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.collider_creation_setiup_8e177('INVOKE_DEFAULT', )
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        if bpy.context.scene.sna_perobj:
            collider['sna_selection'] = bpy.context.selected_objects
            for i_5C24E in range(len(collider['sna_selection'])-1,-1,-1):
                bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
                bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
                bpy.ops.mesh.primitive_cube_add('INVOKE_DEFAULT', location=collider['sna_selection'][i_5C24E].location, rotation=collider['sna_selection'][i_5C24E].rotation_euler, scale=tuple(mathutils.Vector(collider['sna_selection'][i_5C24E].dimensions) / 2.0))
                bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
                bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
                bpy.context.active_object.name = 'collider_box'
                bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        else:
            exec('bpy.ops.object.duplicate()')
            exec('bpy.ops.object.join()')
            collider['sna_joinedobj'] = bpy.context.view_layer.objects.active
            for i_0C6CA in range(len(bpy.context.view_layer.objects.selected)):
                bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
                bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
                bpy.ops.mesh.primitive_cube_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.selected[i_0C6CA].location, rotation=bpy.context.view_layer.objects.selected[i_0C6CA].rotation_euler, scale=tuple(mathutils.Vector(bpy.context.view_layer.objects.selected[i_0C6CA].dimensions) / 2.0))
                bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
                box['sna_sourcelocation'] = bpy.context.view_layer.objects.active.matrix_world
                bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
                bpy.context.active_object.name = 'collider_box'
                bpy.data.objects.remove(object=collider['sna_joinedobj'], )
                bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Minbox_0936B(bpy.types.Operator):
    bl_idname = "sna.minbox_0936b"
    bl_label = "MinBox"
    bl_description = "Creates a box collider that fits the selected object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        collider['sna_minboxname'] = bpy.context.view_layer.objects.active.name
        collider['sna_selection'] = bpy.context.selected_objects
        if bpy.context.scene.sna_perobj:
            for i_88F10 in range(len(collider['sna_selection'])):
                MinBB = collider['sna_selection'][i_88F10]
                from timeit import default_timer as timer
                #import bpy
                from mathutils import Matrix
                DEBUG = False
                CUBE_FACE_INDICES = (
                    (0, 1, 3, 2),
                    (2, 3, 7, 6),
                    (6, 7, 5, 4),
                    (4, 5, 1, 0),
                    (2, 6, 4, 0),
                    (7, 3, 1, 5),
                )

                def gen_cube_verts():
                    for x in range(-1, 2, 2):
                        for y in range(-1, 2, 2):
                            for z in range(-1, 2, 2):
                                yield x, y, z

                def rotating_calipers(hull_points: np.ndarray, bases):
                    min_bb_basis = None
                    min_bb_min = None
                    min_bb_max = None
                    min_vol = math.inf
                    for basis in bases:
                        rot_points = hull_points.dot(np.linalg.inv(basis))
                        # Equivalent to: rot_points = hull_points.dot(np.linalg.inv(np.transpose(basis)).T)
                        bb_min = rot_points.min(axis=0)
                        bb_max = rot_points.max(axis=0)
                        volume = (bb_max - bb_min).prod()
                        if volume < min_vol:
                            min_bb_basis = basis
                            min_vol = volume
                            min_bb_min = bb_min
                            min_bb_max = bb_max
                    return np.array(min_bb_basis), min_bb_max, min_bb_min

                def obj_rotating_calipers(obj):
                    bm = bmesh.new()
                    dg = bpy.context.evaluated_depsgraph_get()
                    bm.from_object(obj, dg)
                    t0 = timer()
                    chull_out = bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
                    t1 = timer()
                    print(f"Convex-Hull calculated in {t1-t0} sec")
                    chull_geom = chull_out["geom"]
                    chull_points = np.array([bmelem.co for bmelem in chull_geom if isinstance(bmelem, bmesh.types.BMVert)])
                    # Create object from Convex-Hull (for debugging)
                    if DEBUG:
                        t0 = timer()
                        for face in set(bm.faces) - set(chull_geom):
                            bm.faces.remove(face)
                        for edge in set(bm.edges) - set(chull_geom):
                            bm.edges.remove(edge)
                        t1 = timer()
                        print(f"Deleted non Convex-Hull edges and faces in {t1 - t0} sec")
                        chull_mesh = bpy.data.meshes.new(obj.name + "_convex_hull")
                        chull_mesh.validate()
                        bm.to_mesh(chull_mesh)
                        chull_obj = bpy.data.objects.new(chull_mesh.name, chull_mesh)
                        chull_obj.matrix_world = obj.matrix_world
                        bpy.context.scene.collection.objects.link(chull_obj)
                    bases = []
                    t0 = timer()
                    for elem in chull_geom:
                        if not isinstance(elem, bmesh.types.BMFace):
                            continue
                        if len(elem.verts) != 3:
                            continue
                        face_normal = elem.normal
                        if np.allclose(face_normal, 0, atol=0.00001):
                            continue
                        for e in elem.edges:
                            v0, v1 = e.verts
                            edge_vec = (v0.co - v1.co).normalized()
                            co_tangent = face_normal.cross(edge_vec)
                            basis = (edge_vec, co_tangent, face_normal)
                            bases.append(basis)
                    t1 = timer()
                    print(f"List of bases built in {t1-t0} sec")
                    t0 = timer()
                    bb_basis, bb_max, bb_min = rotating_calipers(chull_points, bases)
                    t1 = timer()
                    print(f"Rotating Calipers finished in {t1-t0} sec")
                    bm.free()
                    bb_basis_mat = bb_basis.T
                    bb_dim = bb_max - bb_min
                    bb_center = (bb_max + bb_min) / 2
                    mat = Matrix.Translation(bb_center.dot(bb_basis)) @ Matrix(bb_basis_mat).to_4x4() @ Matrix(np.identity(3) * bb_dim / 2).to_4x4()
                    bb_mesh = bpy.data.meshes.new(obj.name + "_minimum_bounding_box")
                    bb_mesh.from_pydata(vertices=list(gen_cube_verts()), edges=[], faces=CUBE_FACE_INDICES)
                    bb_mesh.validate()
                    #bb_mesh.transform(mat)
                    bb_mesh.update()
                    bb_obj = bpy.data.objects.new(bb_mesh.name, bb_mesh)
                    bb_obj.matrix_world = obj.matrix_world @ mat
                    bpy.context.scene.collection.objects.link(bb_obj)
                    bpy.context.view_layer.objects.active = bb_obj
                    #bb_obj.select_set(True)
                    #MinBB.select_set(False)
                #MinBB = bpy.context.object
                obj_rotating_calipers(MinBB)
                #print(str(bb_obj))
                bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
                bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
                collider['sna_moveoutcollection'] = bpy.context.collection
                collider['sna_activeobjectcollider'] = bpy.context.view_layer.objects.active
                bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
                bpy.ops.object.select_all('INVOKE_DEFAULT', action='DESELECT')
                bpy.context.active_object.select_set(state=True, )
                bpy.context.active_object.name = 'collider_box'
        else:
            bpy.ops.object.duplicate('INVOKE_DEFAULT', )
            bpy.ops.object.join('INVOKE_DEFAULT', )
            collider['sna_joinedobj'] = bpy.context.view_layer.objects.active
            MinBB = bpy.context.view_layer.objects.active
            from timeit import default_timer as timer
            #import bpy
            from mathutils import Matrix
            DEBUG = False
            CUBE_FACE_INDICES = (
                (0, 1, 3, 2),
                (2, 3, 7, 6),
                (6, 7, 5, 4),
                (4, 5, 1, 0),
                (2, 6, 4, 0),
                (7, 3, 1, 5),
            )

            def gen_cube_verts():
                for x in range(-1, 2, 2):
                    for y in range(-1, 2, 2):
                        for z in range(-1, 2, 2):
                            yield x, y, z

            def rotating_calipers(hull_points: np.ndarray, bases):
                min_bb_basis = None
                min_bb_min = None
                min_bb_max = None
                min_vol = math.inf
                for basis in bases:
                    rot_points = hull_points.dot(np.linalg.inv(basis))
                    # Equivalent to: rot_points = hull_points.dot(np.linalg.inv(np.transpose(basis)).T)
                    bb_min = rot_points.min(axis=0)
                    bb_max = rot_points.max(axis=0)
                    volume = (bb_max - bb_min).prod()
                    if volume < min_vol:
                        min_bb_basis = basis
                        min_vol = volume
                        min_bb_min = bb_min
                        min_bb_max = bb_max
                return np.array(min_bb_basis), min_bb_max, min_bb_min

            def obj_rotating_calipers(obj):
                bm = bmesh.new()
                dg = bpy.context.evaluated_depsgraph_get()
                bm.from_object(obj, dg)
                t0 = timer()
                chull_out = bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
                t1 = timer()
                print(f"Convex-Hull calculated in {t1-t0} sec")
                chull_geom = chull_out["geom"]
                chull_points = np.array([bmelem.co for bmelem in chull_geom if isinstance(bmelem, bmesh.types.BMVert)])
                # Create object from Convex-Hull (for debugging)
                if DEBUG:
                    t0 = timer()
                    for face in set(bm.faces) - set(chull_geom):
                        bm.faces.remove(face)
                    for edge in set(bm.edges) - set(chull_geom):
                        bm.edges.remove(edge)
                    t1 = timer()
                    print(f"Deleted non Convex-Hull edges and faces in {t1 - t0} sec")
                    chull_mesh = bpy.data.meshes.new(obj.name + "_convex_hull")
                    chull_mesh.validate()
                    bm.to_mesh(chull_mesh)
                    chull_obj = bpy.data.objects.new(chull_mesh.name, chull_mesh)
                    chull_obj.matrix_world = obj.matrix_world
                    bpy.context.scene.collection.objects.link(chull_obj)
                bases = []
                t0 = timer()
                for elem in chull_geom:
                    if not isinstance(elem, bmesh.types.BMFace):
                        continue
                    if len(elem.verts) != 3:
                        continue
                    face_normal = elem.normal
                    if np.allclose(face_normal, 0, atol=0.00001):
                        continue
                    for e in elem.edges:
                        v0, v1 = e.verts
                        edge_vec = (v0.co - v1.co).normalized()
                        co_tangent = face_normal.cross(edge_vec)
                        basis = (edge_vec, co_tangent, face_normal)
                        bases.append(basis)
                t1 = timer()
                print(f"List of bases built in {t1-t0} sec")
                t0 = timer()
                bb_basis, bb_max, bb_min = rotating_calipers(chull_points, bases)
                t1 = timer()
                print(f"Rotating Calipers finished in {t1-t0} sec")
                bm.free()
                bb_basis_mat = bb_basis.T
                bb_dim = bb_max - bb_min
                bb_center = (bb_max + bb_min) / 2
                mat = Matrix.Translation(bb_center.dot(bb_basis)) @ Matrix(bb_basis_mat).to_4x4() @ Matrix(np.identity(3) * bb_dim / 2).to_4x4()
                bb_mesh = bpy.data.meshes.new(obj.name + "_minimum_bounding_box")
                bb_mesh.from_pydata(vertices=list(gen_cube_verts()), edges=[], faces=CUBE_FACE_INDICES)
                bb_mesh.validate()
                #bb_mesh.transform(mat)
                bb_mesh.update()
                bb_obj = bpy.data.objects.new(bb_mesh.name, bb_mesh)
                bb_obj.matrix_world = obj.matrix_world @ mat
                bpy.context.scene.collection.objects.link(bb_obj)
                bpy.context.view_layer.objects.active = bb_obj
                #bb_obj.select_set(True)
                #MinBB.select_set(False)
            #MinBB = bpy.context.object
            obj_rotating_calipers(MinBB)
            #print(str(bb_obj))
            bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
            bpy.data.objects.remove(object=collider['sna_joinedobj'], )
            bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
            collider['sna_moveoutcollection'] = bpy.context.collection
            collider['sna_activeobjectcollider'] = bpy.context.view_layer.objects.active
            bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
            bpy.context.active_object.select_set(state=True, )
            bpy.context.active_object.name = 'collider_box'
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Scale_Cage_4E08E(bpy.types.Operator):
    bl_idname = "sna.scale_cage_4e08e"
    bl_label = "Scale Cage"
    bl_description = "Sets the current tool to Select Cage"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        exec("bpy.context.scene.tool_settings.snap_elements_base = {'FACE'}")
        bpy.context.scene.tool_settings.use_snap_scale = True
        bpy.context.scene.tool_settings.use_snap_translate = True
        bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
        bpy.ops.wm.tool_set_by_id('INVOKE_DEFAULT', name='builtin.scale_cage')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Select_Cylinder_Face_8A190(bpy.types.Operator):
    bl_idname = "sna.select_cylinder_face_8a190"
    bl_label = "Select cylinder face"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        bpy.ops.mesh.select_mode('INVOKE_DEFAULT', type='FACE')
        bpy.ops.mesh.select_all('INVOKE_DEFAULT', action='DESELECT')
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        bpy.context.view_layer.objects.active.data.polygons[33].select = True
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        bpy.ops.wm.tool_set_by_id('INVOKE_DEFAULT', name='builtin.move')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Move_To_Collision_Collection_B7E42(bpy.types.Operator):
    bl_idname = "sna.move_to_collision_collection_b7e42"
    bl_label = "Move to collision collection"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if "['" + bpy.context.window.scene.name + "']" in str(bpy.context.view_layer.objects.active.users_collection):
            pass
        else:
            bpy.context.scene.collection.objects.link(object=bpy.context.view_layer.objects.active, )
        collider['sna_collision_collections'] = bpy.context.view_layer.objects.active.users_collection
        for i_E8C31 in range(len(collider['sna_collision_collections'])):
            if 'Scene Collection' in collider['sna_collision_collections'][i_E8C31].name:
                pass
            else:
                collider['sna_collision_collections'][i_E8C31].objects.unlink(object=bpy.context.view_layer.objects.active, )
        for i_2D324 in range(len(bpy.context.scene.sna_active_visual_object.users_collection)):
            if '_visual' in bpy.context.scene.sna_active_visual_object.users_collection[i_2D324].name:
                bpy.data.collections[bpy.context.scene.sna_active_visual_object.users_collection[i_2D324].name.replace('_visual', '_colliders')].objects.link(object=bpy.context.view_layer.objects.active, )
                bpy.context.scene.collection.objects.unlink(object=bpy.context.view_layer.objects.active, )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Move_To_Colllder_Collection_1Fa60(bpy.types.Operator):
    bl_idname = "sna.move_to_colllder_collection_1fa60"
    bl_label = "Move to Colllder collection"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not True

    def execute(self, context):
        if (property_exists("bpy.context.scene.collection.children", globals(), locals()) and 'Colliders' in bpy.context.scene.collection.children):
            pass
        else:
            bpy.ops.collection.create('INVOKE_DEFAULT', name='Colliders')
            bpy.data.scenes['Scene'].collection.children.link(child=bpy.data.collections['Colliders'], )
        collider['sna_isincolliders'] = False
        if False:
            pass
        collider['sna_userscollection'] = bpy.context.view_layer.objects.active.users_collection
        for i_CC8AD in range(len(collider['sna_userscollection'])):
            if 'Colliders' in collider['sna_userscollection'][i_CC8AD].name:
                collider['sna_isincolliders'] = True
        if collider['sna_isincolliders']:
            pass
        else:
            bpy.data.collections['Colliders'].objects.link(object=bpy.context.view_layer.objects.active, )
        for i_0A612 in range(len(collider['sna_userscollection'])):
            if (collider['sna_userscollection'][i_0A612].name == 'Colliders'):
                pass
            else:
                collider['sna_userscollection'][i_0A612].objects.unlink(object=bpy.context.view_layer.objects.active, )
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        # Access the 3D Viewport's shading settings
                        space_3d = area.spaces.active
                        if space_3d:
                            # Set the viewport shading color type to 'OBJECT'
                            space_3d.shading.color_type = 'OBJECT'
                            print("Viewport shading color type set to 'OBJECT'")
                print("Script could not find an active 3D Viewport.")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Set_Active_Collection_50942(bpy.types.Operator):
    bl_idname = "sna.set_active_collection_50942"
    bl_label = "Set Active Collection"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (property_exists("bpy.context.scene.collection.children", globals(), locals()) and 'Colliders' in bpy.context.scene.collection.children):
            pass
        else:
            bpy.ops.collection.create('INVOKE_DEFAULT', name='Colliders')
            bpy.data.scenes['Scene'].collection.children.link(child=bpy.data.collections['Colliders'], )
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                # Access the 3D Viewport's shading settings
                space_3d = area.spaces.active
                if space_3d:
                    # Set the viewport shading color type to 'OBJECT'
                    space_3d.shading.color_type = 'OBJECT'
                    print("Viewport shading color type set to 'OBJECT'")
        print("Script could not find an active 3D Viewport.")
        bpy.data.collections['Colliders'].objects.link(object=bpy.context.view_layer.objects.active, )
        for i_BC317 in range(len(bpy.data.collections)):
            if False:
                None.objects.unlink(object=bpy.context.view_layer.objects.active, )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Set_Collider_Material_33Bff(bpy.types.Operator):
    bl_idname = "sna.set_collider_material_33bff"
    bl_label = "Set Collider Material"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.view_layer.objects.active.show_wire = True
        bpy.context.view_layer.objects.active.color = (1.0, 0.0, 1.0, 0.5)
        # Ensure we're in the 3D viewport context
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        # Set viewport shading to 'OBJECT'
                        space.shading.color_type = 'OBJECT'
        # Check if the material already exists
        material_name = "ColliderMaterial"
        material = bpy.data.materials.get(material_name)
        if not material:
            # Create the material if it doesn't exist
            material = bpy.data.materials.new(name=material_name)
            material.use_nodes = True
            # Get the node tree
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            # Clear existing nodes
            nodes.clear()
            # Create nodes
            output_node = nodes.new(type='ShaderNodeOutputMaterial')
            principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
            emission_node = nodes.new(type='ShaderNodeEmission')
            mix_shader_node = nodes.new(type='ShaderNodeMixShader')
            # Set positions for clarity
            output_node.location = (400, 0)
            principled_node.location = (0, 0)
            emission_node.location = (0, 200)
            mix_shader_node.location = (200, 0)
            # Set pink color and alpha
            base_color = (1.0, 0.2, 0.6, 0.25)  # (R, G, B, A)
            principled_node.inputs["Base Color"].default_value = base_color
            principled_node.inputs["Alpha"].default_value = 0.25
            # Set roughness to 1.0
            principled_node.inputs["Roughness"].default_value = 1.0
            # Set emission color and strength
            emission_node.inputs["Color"].default_value = base_color[:3] + (1.0,)  # (R, G, B, 1.0)
            emission_node.inputs["Strength"].default_value = 1
            # Connect the nodes
            links.new(principled_node.outputs["BSDF"], mix_shader_node.inputs[1])
            links.new(emission_node.outputs["Emission"], mix_shader_node.inputs[2])
            links.new(mix_shader_node.outputs["Shader"], output_node.inputs["Surface"])
            # Set the render method and shadow options for transparency
            material.surface_render_method = 'BLENDED'  # Options: 'OPAQUE', 'BLENDED', 'DITHERED'
            material.shadow_method = 'NONE'  # Avoid grainy shadows from transparency
            #material.show_backface_culling = True  # Prevent overlapping artifacts
        # Assign the material to the active object
        if bpy.context.active_object:
            obj = bpy.context.active_object
            if obj.data.materials:
                obj.data.materials[0] = material
            else:
                obj.data.materials.append(material)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Set_Active_Object_40Bc9(bpy.types.Operator):
    bl_idname = "sna.set_active_object_40bc9"
    bl_label = "Set Active Object"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.sna_active_visual_object = bpy.context.view_layer.objects.active
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Scalecylradius_E1610(bpy.types.Operator):
    bl_idname = "sna.scalecylradius_e1610"
    bl_label = "ScaleCylRadius"
    bl_description = "Increases the radius of the cylinder"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.transform.resize('INVOKE_DEFAULT', orient_type='LOCAL', orient_matrix_type='LOCAL', constraint_axis=(True, True, False))
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Scalesphereradius_Bd79D(bpy.types.Operator):
    bl_idname = "sna.scalesphereradius_bd79d"
    bl_label = "ScaleSphereRadius"
    bl_description = "Increases the radius of the sphere"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.transform.resize('INVOKE_DEFAULT', orient_type='LOCAL', orient_matrix_type='LOCAL', constraint_axis=(True, True, True))
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Add_Margin_Modifier_43181(bpy.types.Operator):
    bl_idname = "sna.add_margin_modifier_43181"
    bl_label = "Add Margin Modifier"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.modifier_add('INVOKE_DEFAULT', type='SOLIDIFY')
        bpy.context.view_layer.objects.active.modifiers['Solidify'].name = 'ColliderMargin'
        bpy.context.view_layer.objects.active.modifiers['ColliderMargin'].offset = 1.0
        bpy.context.view_layer.objects.active.modifiers['ColliderMargin'].use_even_offset = True
        bpy.context.view_layer.objects.active.modifiers['ColliderMargin'].thickness = bpy.context.scene.sna_collidermargin
        bpy.context.view_layer.objects.active.modifiers['ColliderMargin'].use_rim_only = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Collider_Creation_Setiup_8E177(bpy.types.Operator):
    bl_idname = "sna.collider_creation_setiup_8e177"
    bl_label = "Collider Creation Setiup"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (len(list(bpy.context.view_layer.objects.selected)) != 0):
            bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
            bpy.context.scene.sna_collidervisibiity = True
        else:
            sna_popup_message_45189_521B9('Warning', 'No object selected', 'ERROR')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_colliderstab_0B1AA(layout_function, ):
    box_7DF5A = layout_function.box()
    box_7DF5A.alert = False
    box_7DF5A.enabled = True
    box_7DF5A.active = True
    box_7DF5A.use_property_split = False
    box_7DF5A.use_property_decorate = False
    box_7DF5A.alignment = 'Expand'.upper()
    box_7DF5A.scale_x = 1.0
    box_7DF5A.scale_y = 1.0
    if not True: box_7DF5A.operator_context = "EXEC_DEFAULT"
    box_7DF5A.label(text='Options', icon_value=0)
    box_7DF5A.prop(bpy.context.scene, 'sna_collidervisibiity', text='Show/Hide Colliders', icon_value=0, emboss=True)
    row_9D0D6 = box_7DF5A.row(heading='', align=False)
    row_9D0D6.alert = False
    row_9D0D6.enabled = True
    row_9D0D6.active = True
    row_9D0D6.use_property_split = False
    row_9D0D6.use_property_decorate = False
    row_9D0D6.scale_x = 1.0
    row_9D0D6.scale_y = 1.0
    row_9D0D6.alignment = 'Expand'.upper()
    row_9D0D6.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
    row_9D0D6.prop(bpy.context.scene, 'sna_perobj', text='Per Object', icon_value=0, emboss=True, toggle=bpy.context.scene.sna_perobj)
    row_9D0D6.prop(bpy.context.scene, 'sna_minbox', text='Minimal Box', icon_value=0, emboss=True, toggle=bpy.context.scene.sna_minbox)
    box_7DF5A.prop(bpy.context.scene, 'sna_collidermargin', text='Collider Margin', icon_value=0, emboss=True)
    box_46623 = layout_function.box()
    box_46623.alert = False
    box_46623.enabled = True
    box_46623.active = True
    box_46623.use_property_split = False
    box_46623.use_property_decorate = False
    box_46623.alignment = 'Expand'.upper()
    box_46623.scale_x = 1.0
    box_46623.scale_y = 1.0
    if not True: box_46623.operator_context = "EXEC_DEFAULT"
    box_46623.label(text='Create', icon_value=0)
    col_700F2 = box_46623.column(heading='', align=False)
    col_700F2.alert = False
    col_700F2.enabled = True
    col_700F2.active = True
    col_700F2.use_property_split = False
    col_700F2.use_property_decorate = False
    col_700F2.scale_x = 1.0
    col_700F2.scale_y = 1.0
    col_700F2.alignment = 'Expand'.upper()
    col_700F2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
    if bpy.context.scene.sna_minbox:
        op = col_700F2.operator('sna.minbox_0936b', text='Box', icon_value=287, emboss=True, depress=False)
    else:
        op = col_700F2.operator('sna.box_9d9e4', text='Box', icon_value=287, emboss=True, depress=False)
    op = col_700F2.operator('sna.cylinder_050b8', text='Cylinder', icon_value=293, emboss=True, depress=False)
    op = col_700F2.operator('sna.sphere_f5cd9', text='Sphere', icon_value=289, emboss=True, depress=False)
    op = col_700F2.operator('sna.create_cone_3ded7', text='Cone', icon_value=305, emboss=True, depress=False)
    op = col_700F2.operator('sna.plane_182f2', text='Plane', icon_value=286, emboss=True, depress=False)
    row_90E90 = box_46623.row(heading='', align=False)
    row_90E90.alert = False
    row_90E90.enabled = True
    row_90E90.active = True
    row_90E90.use_property_split = False
    row_90E90.use_property_decorate = False
    row_90E90.scale_x = 1.0
    row_90E90.scale_y = 1.0
    row_90E90.alignment = 'Expand'.upper()
    row_90E90.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
    op = box_46623.operator('sna.selectflatfaces_0bf7c', text='Generate by Face', icon_value=204, emboss=True, depress=False)
    row_F586A = box_46623.row(heading='', align=False)
    row_F586A.alert = False
    row_F586A.enabled = True
    row_F586A.active = True
    row_F586A.use_property_split = False
    row_F586A.use_property_decorate = False
    row_F586A.scale_x = 1.0
    row_F586A.scale_y = 1.0
    row_F586A.alignment = 'Expand'.upper()
    row_F586A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
    box_3DAB7 = layout_function.box()
    box_3DAB7.alert = False
    box_3DAB7.enabled = True
    box_3DAB7.active = True
    box_3DAB7.use_property_split = False
    box_3DAB7.use_property_decorate = False
    box_3DAB7.alignment = 'Expand'.upper()
    box_3DAB7.scale_x = 1.0
    box_3DAB7.scale_y = 1.0
    if not True: box_3DAB7.operator_context = "EXEC_DEFAULT"
    box_55536 = box_3DAB7.box()
    box_55536.alert = False
    box_55536.enabled = True
    box_55536.active = True
    box_55536.use_property_split = False
    box_55536.use_property_decorate = False
    box_55536.alignment = 'Expand'.upper()
    box_55536.scale_x = 1.0
    box_55536.scale_y = 1.0
    if not True: box_55536.operator_context = "EXEC_DEFAULT"
    op = box_55536.operator('sna.mesh_85d40', text='Mesh Collider', icon_value=290, emboss=True, depress=False)
    row_6C90F = box_55536.row(heading='', align=False)
    row_6C90F.alert = False
    row_6C90F.enabled = True
    row_6C90F.active = True
    row_6C90F.use_property_split = False
    row_6C90F.use_property_decorate = False
    row_6C90F.scale_x = 1.0
    row_6C90F.scale_y = 1.0
    row_6C90F.alignment = 'Expand'.upper()
    row_6C90F.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
    if (property_exists("bpy.context.view_layer.objects.active.modifiers", globals(), locals()) and 'Decimate' in bpy.context.view_layer.objects.active.modifiers):
        if 'meshcollider' in bpy.context.active_object.name:
            row_6C90F.prop(bpy.context.view_layer.objects.active.modifiers['Decimate'], 'ratio', text='Simplify', icon_value=0, emboss=True)
    row_40A46 = box_55536.row(heading='', align=False)
    row_40A46.alert = False
    row_40A46.enabled = True
    row_40A46.active = True
    row_40A46.use_property_split = False
    row_40A46.use_property_decorate = False
    row_40A46.scale_x = 1.0
    row_40A46.scale_y = 1.0
    row_40A46.alignment = 'Expand'.upper()
    row_40A46.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
    if (property_exists("bpy.context.view_layer.objects.active.modifiers", globals(), locals()) and 'Inflate' in bpy.context.view_layer.objects.active.modifiers):
        row_40A46.prop(bpy.context.view_layer.objects.active.modifiers['Inflate'], 'thickness', text='Inflate', icon_value=0, emboss=True)
    box_3DAB7.label(text='Transform', icon_value=0)
    split_61591 = box_3DAB7.split(factor=0.7988929748535156, align=False)
    split_61591.alert = False
    split_61591.enabled = True
    split_61591.active = True
    split_61591.use_property_split = False
    split_61591.use_property_decorate = False
    split_61591.scale_x = 1.0
    split_61591.scale_y = 1.0
    split_61591.alignment = 'Expand'.upper()
    if not True: split_61591.operator_context = "EXEC_DEFAULT"
    op = split_61591.operator('sna.scale_cage_4e08e', text='Scale Cage', icon_value=0, emboss=True, depress=False)
    split_61591.prop(bpy.context.scene.tool_settings, 'use_snap', text='', icon_value=577, emboss=True, toggle=bpy.context.scene.tool_settings.use_snap)
    if (bpy.context.view_layer.objects.active == None):
        pass
    else:
        if '_cylinder' in bpy.context.view_layer.objects.active.name:
            box_3DAB7.prop(bpy.context.view_layer.objects.active, 'sna_cylrad', text='Diameter', icon_value=0, emboss=True)
    if (bpy.context.view_layer.objects.active == None):
        pass
    else:
        if '_sphere' in bpy.context.view_layer.objects.active.name:
            op = box_3DAB7.operator('sna.scalesphereradius_bd79d', text='Scale Radius', icon_value=0, emboss=True, depress=False)


class SNA_OT_Create_Cone_3Ded7(bpy.types.Operator):
    bl_idname = "sna.create_cone_3ded7"
    bl_label = "Create Cone"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.collider_creation_setiup_8e177('INVOKE_DEFAULT', )
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        if bpy.context.scene.sna_perobj:
            collider['sna_selection'] = bpy.context.selected_objects
            for i_D1257 in range(len(collider['sna_selection'])-1,-1,-1):
                bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
                bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
                float1 = tuple(mathutils.Vector(collider['sna_selection'][i_D1257].dimensions) / 2.0)[0]
                float2 = tuple(mathutils.Vector(collider['sna_selection'][i_D1257].dimensions) / 2.0)[1]
                largest_float = None
                largest_float = max(float1, float2)
                print(largest_float)
                bpy.ops.mesh.primitive_cone_add('INVOKE_DEFAULT', radius1=largest_float, radius2=0.0, depth=float(tuple(mathutils.Vector(collider['sna_selection'][i_D1257].dimensions) / 2.0)[2] * 2.0), location=collider['sna_selection'][i_D1257].location, rotation=collider['sna_selection'][i_D1257].rotation_euler)
                bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
                bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
                bpy.context.active_object.name = 'collider_cone'
                bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        else:
            exec('bpy.ops.object.duplicate()')
            exec('bpy.ops.object.join()')
            collider['sna_joinedobj'] = bpy.context.view_layer.objects.active
            for i_8F9E4 in range(len(bpy.context.view_layer.objects.selected)):
                bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
                bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
                float1 = tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0]
                float2 = tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[1]
                largest_float = None
                largest_float = max(float1, float2)
                print(largest_float)
                bpy.ops.mesh.primitive_cone_add('INVOKE_DEFAULT', radius1=largest_float, radius2=0.0, depth=float(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[2] * 2.0), location=bpy.context.view_layer.objects.selected[i_8F9E4].location, rotation=bpy.context.view_layer.objects.selected[i_8F9E4].rotation_euler)
                bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
                box['sna_sourcelocation'] = bpy.context.view_layer.objects.active.matrix_world
                bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
                bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
                bpy.context.active_object.name = 'collider_cone'
                bpy.data.objects.remove(object=collider['sna_joinedobj'], )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


_050B8_running = False
class SNA_OT_Cylinder_050B8(bpy.types.Operator):
    bl_idname = "sna.cylinder_050b8"
    bl_label = "Cylinder"
    bl_description = "Creates a cylinder collider that fits selected cylindrical shaped objects. Choose your alignment axis in the subsequent menu"
    bl_options = {"REGISTER", "UNDO"}
    cursor = "CROSSHAIR"
    _handle = None
    _event = {}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        if not True or context.area.spaces[0].bl_rna.identifier == 'SpaceView3D':
            return not False
        return False

    def save_event(self, event):
        event_options = ["type", "value", "alt", "shift", "ctrl", "oskey", "mouse_region_x", "mouse_region_y", "mouse_x", "mouse_y", "pressure", "tilt"]
        if bpy.app.version >= (3, 2, 1):
            event_options += ["type_prev", "value_prev"]
        for option in event_options: self._event[option] = getattr(event, option)

    def draw_callback_px(self, context):
        event = self._event
        if event.keys():
            event = dotdict(event)
            try:
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_F73DC, y_F73DC = (100.0, 600.0)
                    blf.position(font_id, x_F73DC, y_F73DC, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[X] Cylinder along X axis')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_0ADD1, y_0ADD1 = tuple(mathutils.Vector((100.0, 600.0)) - mathutils.Vector((0.0, 80.0)))
                    blf.position(font_id, x_0ADD1, y_0ADD1, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Y] Cylinder along Y axis')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_0CD0E, y_0CD0E = tuple(mathutils.Vector(tuple(mathutils.Vector((100.0, 600.0)) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))
                    blf.position(font_id, x_0CD0E, y_0CD0E, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Z] Cylinder along Z axis')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_E459D, y_E459D = tuple(mathutils.Vector(tuple(mathutils.Vector(tuple(mathutils.Vector((100.0, 600.0)) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))
                    blf.position(font_id, x_E459D, y_E459D, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[ESC] Cancel')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_BD0B8, y_BD0B8 = tuple(mathutils.Vector(tuple(mathutils.Vector(tuple(mathutils.Vector(tuple(mathutils.Vector((100.0, 600.0)) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))
                    blf.position(font_id, x_BD0B8, y_BD0B8, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Space] Confirm')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
            except Exception as error:
                print(error)

    def execute(self, context):
        global _050B8_running
        _050B8_running = False
        context.window.cursor_set("DEFAULT")
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        if (collider['sna_joinedobj'] != None):
            bpy.data.objects.remove(object=collider['sna_joinedobj'], )
            collider['sna_joinedobj'] = None
        for area in context.screen.areas:
            area.tag_redraw()
        return {"FINISHED"}

    def modal(self, context, event):
        global _050B8_running
        if not context.area or not _050B8_running:
            self.execute(context)
            return {'CANCELLED'}
        self.save_event(event)
        context.area.tag_redraw()
        context.window.cursor_set('CROSSHAIR')
        try:
            if (event.type == 'X' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                if (bpy.context.view_layer.objects.active.name == cylinder['sna_actobjcylgen']):
                    bpy.ops.sna.cylinder_x_3a040('INVOKE_DEFAULT', )
                else:
                    bpy.ops.object.delete('INVOKE_DEFAULT', confirm=False)
                    bpy.data.objects[cylinder['sna_actobjcylgen']].select_set(state=True, )
                    bpy.context.view_layer.objects.active = bpy.context.view_layer.objects.selected[cylinder['sna_actobjcylgen']]
                    bpy.ops.sna.cylinder_x_3a040('INVOKE_DEFAULT', )
            else:
                if (event.type == 'Y' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                    if (bpy.context.view_layer.objects.active.name == cylinder['sna_actobjcylgen']):
                        bpy.ops.sna.cylinder_y_f23b4('INVOKE_DEFAULT', )
                    else:
                        bpy.ops.object.delete('INVOKE_DEFAULT', confirm=False)
                        bpy.data.objects[cylinder['sna_actobjcylgen']].select_set(state=True, )
                        bpy.context.view_layer.objects.active = bpy.context.view_layer.objects.selected[cylinder['sna_actobjcylgen']]
                        bpy.ops.sna.cylinder_y_f23b4('INVOKE_DEFAULT', )
                if (event.type == 'Z' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                    if (bpy.context.view_layer.objects.active.name == cylinder['sna_actobjcylgen']):
                        bpy.ops.sna.cylinder_z_83f4c('INVOKE_DEFAULT', )
                    else:
                        bpy.ops.object.delete('INVOKE_DEFAULT', confirm=False)
                        bpy.data.objects[cylinder['sna_actobjcylgen']].select_set(state=True, )
                        bpy.context.view_layer.objects.active = bpy.context.view_layer.objects.selected[cylinder['sna_actobjcylgen']]
                        bpy.ops.sna.cylinder_z_83f4c('INVOKE_DEFAULT', )
                if (event.type == 'ESC' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                    if (bpy.context.view_layer.objects.active.name != cylinder['sna_actobjcylgen']):
                        bpy.ops.object.delete('INVOKE_DEFAULT', confirm=False)
                    else:
                        if event.type in ['RIGHTMOUSE', 'ESC']:
                            self.execute(context)
                            return {'CANCELLED'}
                        self.execute(context)
                        return {"FINISHED"}
                if (event.type == 'SPACE' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                    if event.type in ['RIGHTMOUSE', 'ESC']:
                        self.execute(context)
                        return {'CANCELLED'}
                    self.execute(context)
                    return {"FINISHED"}
        except Exception as error:
            print(error)
        if event.type in ['RIGHTMOUSE', 'ESC']:
            self.execute(context)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        global _050B8_running
        if _050B8_running:
            _050B8_running = False
            return {'FINISHED'}
        else:
            self.save_event(event)
            self.start_pos = (event.mouse_x, event.mouse_y)
            bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
            collider['sna_joinedobj'] = None
            cylinder['sna_actobjcylgen'] = bpy.context.view_layer.objects.active.name
            if (len(bpy.context.selected_objects) > 1):
                exec('bpy.ops.object.duplicate()')
                exec('bpy.ops.object.join()')
                collider['sna_joinedobj'] = bpy.context.view_layer.objects.active
                cylinder['sna_actobjcylgen'] = bpy.context.view_layer.objects.active.name
            args = (context,)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            _050B8_running = True
            return {'RUNNING_MODAL'}


class SNA_OT_Cylinder_Z_83F4C(bpy.types.Operator):
    bl_idname = "sna.cylinder_z_83f4c"
    bl_label = "Cylinder Z"
    bl_description = "Cylinder"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.collider_creation_setiup_8e177('INVOKE_DEFAULT', )
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        cylinder['sna_cylusercollection'] = bpy.context.view_layer.objects.active.users_collection
        cylinder['sna_cylsource'] = bpy.context.view_layer.objects.active
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        float1 = tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0]
        float2 = tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[1]
        largest_float = None
        largest_float = max(float1, float2)
        print(largest_float)
        bpy.ops.mesh.primitive_cylinder_add('INVOKE_DEFAULT', radius=largest_float, depth=float(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[2] * 2.0), location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler)
        bpy.context.active_object.name = 'collider_cylinder'
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        bpy.context.view_layer.objects.active.sna_cylrad = bpy.context.view_layer.objects.active.dimensions[1]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Cylinder_X_3A040(bpy.types.Operator):
    bl_idname = "sna.cylinder_x_3a040"
    bl_label = "Cylinder X"
    bl_description = "Cylinder"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        cylinder['sna_cylusercollection'] = bpy.context.view_layer.objects.active.users_collection
        cylinder['sna_cylsource'] = bpy.context.view_layer.objects.active
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        float1 = tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0]
        float2 = tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[2]
        largest_float = None
        largest_float = max(float1, float2)
        print(largest_float)
        bpy.ops.mesh.primitive_cylinder_add('INVOKE_DEFAULT', radius=largest_float, depth=float(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[1] * 2.0), location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler)
        axis = 'X'
        from math import radians
        # Rotate 90 degrees around the local Y-axis
        bpy.context.active_object.rotation_euler.rotate_axis(axis, radians(90))
        bpy.context.active_object.name = 'collider_cylinder'
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        bpy.context.view_layer.objects.active.sna_cylrad = bpy.context.view_layer.objects.active.dimensions[1]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Cylinder_Y_F23B4(bpy.types.Operator):
    bl_idname = "sna.cylinder_y_f23b4"
    bl_label = "Cylinder Y"
    bl_description = "Cylinder"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        cylinder['sna_cylusercollection'] = bpy.context.view_layer.objects.active.users_collection
        cylinder['sna_cylsource'] = bpy.context.view_layer.objects.active
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        float1 = tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[1]
        float2 = tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[2]
        largest_float = None
        largest_float = max(float1, float2)
        print(largest_float)
        bpy.ops.mesh.primitive_cylinder_add('INVOKE_DEFAULT', radius=largest_float, depth=float(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0] * 2.0), location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler)
        axis = 'Y'
        from math import radians
        # Rotate 90 degrees around the local Y-axis
        bpy.context.active_object.rotation_euler.rotate_axis(axis, radians(90))
        bpy.context.active_object.name = 'collider_cylinder'
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        bpy.context.view_layer.objects.active.sna_cylrad = bpy.context.view_layer.objects.active.dimensions[1]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Export_All_B6B8D(bpy.types.Operator):
    bl_idname = "sna.export_all_b6b8d"
    bl_label = "Export All"
    bl_description = "Creates an SDF of all objects in the 'Collider' collection"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.window_manager.sna_initialscene = bpy.context.scene
        if (len(bpy.context.view_layer.objects.selected) != 0):
            bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        for i_6691E in range(len(bpy.data.scenes)):
            bpy.context.window_manager.sna_exportscene = bpy.data.scenes[i_6691E]
            bpy.context.window.scene = bpy.data.scenes[i_6691E]
            folder_name = bpy.data.scenes[i_6691E].name.replace('_model', '')
            path = bpy.context.scene.sna_filepath
            import shutil
            # Specify the path and folder name
            # path = 'G:/My Drive/Tools/WIP/Blender SDF Gen/V3/ExportTest'
            # folder_name = 'arm'
            # Full folder path
            folder_path = os.path.join(path, folder_name)
            # Check if the folder exists
            if os.path.exists(folder_path):
                # Clear the folder's contents without deleting the folder itself
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)  # Delete the file or symbolic link
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)  # Delete the directory and its contents
                    except Exception as e:
                        print(f'Failed to delete {file_path}. Reason: {e}')
            else:
                # If the folder doesn't exist, create it
                os.makedirs(folder_path)
            print(f"Folder '{folder_path}' is now empty and ready for use.")
            bpy.ops.object.select_all('INVOKE_DEFAULT', action='DESELECT')
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
            bpy.context.scene.sna_userpath = os.path.join(os.path.join(bpy.path.abspath(bpy.context.scene.sna_filepath),bpy.path.abspath(bpy.data.scenes[i_6691E].name.replace('_model', ''))),'',os.path.join(r'model.sdf',))
            with open(os.path.join(os.path.join(bpy.path.abspath(bpy.context.scene.sna_filepath),bpy.path.abspath(bpy.data.scenes[i_6691E].name.replace('_model', ''))),'',os.path.join(r'model.sdf',)), mode='a') as file_94DF1:
                file_94DF1.write('<?xml version="1.0" encoding="UTF-8"?>' + '\n<sdf version="1.6">' + "\n  <model name='" + bpy.data.scenes[i_6691E].name.replace('_model', '') + "'>")
            for i_C07BB in range(len(bpy.data.collections)):
                target_collection = bpy.data.collections[i_C07BB]
                target_scene = bpy.context.scene
                is_in_scene = None
                # Replace with your collection and scene names
                #target_collection = bpy.data.collections.get("X")
                #target_scene = bpy.data.scenes.get("Y")

                def collection_in_scene(scene, collection):

                    def traverse(col):
                        return col == collection or any(traverse(child) for child in col.children)
                    return traverse(scene.collection)
                # Set the boolean based on whether the collection is in the scene
                is_in_scene = collection_in_scene(target_scene, target_collection)
                if is_in_scene:
                    if '_link' in bpy.data.collections[i_C07BB].name:
                        with open(os.path.join(os.path.join(bpy.path.abspath(bpy.context.scene.sna_filepath),bpy.path.abspath(bpy.data.scenes[i_6691E].name.replace('_model', ''))),'',os.path.join(r'model.sdf',)), mode='a') as file_AED39:
                            file_AED39.write('\n    <link name ="' + bpy.data.collections[i_C07BB].name + '">')
                        if (not bpy.data.collections[i_C07BB].sna_isstatic):
                            for i_44F2C in range(len(bpy.data.collections[i_C07BB].children)):
                                if '_visual' in bpy.data.collections[i_C07BB].children[i_44F2C].name:
                                    for i_9CB7D in range(len(bpy.data.collections[i_C07BB].children[i_44F2C].all_objects)):
                                        if (bpy.data.collections[i_C07BB].children[i_44F2C].all_objects[i_9CB7D].sna_materialsmass == None):
                                            bpy.context.view_layer.objects.active.sna_materialsmass = 'Default'
                                        bpy.data.collections[i_C07BB].children[i_44F2C].all_objects[i_9CB7D].select_set(state=True, )
                                        bpy.context.view_layer.objects.active = bpy.data.collections[i_C07BB].children[i_44F2C].all_objects[i_9CB7D]
                                    bpy.ops.object.duplicate_move()
                                    bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_CENTER_OF_MASS')
                                    output_string = None
                                    import numpy as np

                                    def calculate_signed_volume(v0, v1, v2):
                                        """Calculate the signed volume of a tetrahedron formed by the origin and a triangle."""
                                        return np.dot(v0, np.cross(v1, v2)) / 6.0

                                    def calculate_volume(mesh):
                                        """Calculate the volume of the mesh using the signed volume method."""
                                        if mesh is None:
                                            return 0.0
                                        total_volume = 0.0
                                        for poly in mesh.polygons:
                                            vertices = [mesh.vertices[i].co for i in poly.vertices]
                                            if len(vertices) >= 3:  # Only process triangles and quads
                                                v0, v1, v2 = vertices[0], vertices[1], vertices[2]
                                                total_volume += calculate_signed_volume(v0, v1, v2)
                                                if len(vertices) == 4:  # Process quadrilaterals as two triangles
                                                    v3 = vertices[3]
                                                    total_volume += calculate_signed_volume(v0, v2, v3)
                                        return abs(total_volume)  # Return the absolute value of the volume

                                    def calculate_inertia_tensor(obj):
                                        """Calculate the inertia tensor for a given object based on its geometry."""
                                        # Apply object scale to ensure consistency
                                        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                                        # Get evaluated mesh data
                                        depsgraph = bpy.context.evaluated_depsgraph_get()
                                        mesh = obj.evaluated_get(depsgraph).to_mesh()
                                        # Initialize tensor components
                                        ixx = iyy = izz = ixy = ixz = iyz = 0.0
                                        total_volume = 0.0
                                        # Check if the sna_materialsmass property exists; if not, default to 1.0
                                        density = 1.0  # Default value
                                        if "sna_materialsmass" in obj:
                                            density = obj["sna_materialsmass"]  # Access the property safely
                                        # Iterate over the polygons (faces) of the mesh
                                        for poly in mesh.polygons:
                                            # Get the local vertices of the polygon
                                            vertices = [mesh.vertices[i].co for i in poly.vertices]
                                            # Only process triangles and quads
                                            if len(vertices) >= 3:
                                                # Calculate the signed volume contributions
                                                if len(vertices) == 3:  # Triangle
                                                    v0, v1, v2 = vertices
                                                    poly_volume = calculate_signed_volume(v0, v1, v2)
                                                elif len(vertices) == 4:  # Quadrilateral
                                                    v0, v1, v2, v3 = vertices
                                                    poly_volume = (calculate_signed_volume(v0, v1, v2) +
                                                                   calculate_signed_volume(v0, v2, v3))
                                                # Update total volume
                                                total_volume += abs(poly_volume)
                                                # Estimate the mass of the polygon
                                                triangle_mass = density * abs(poly_volume)
                                                # Sum contributions of each vertex to the inertia tensor
                                                for vertex in vertices:
                                                    x, y, z = vertex.x, vertex.y, vertex.z
                                                    ixx += triangle_mass * (y**2 + z**2)
                                                    iyy += triangle_mass * (x**2 + z**2)
                                                    izz += triangle_mass * (x**2 + y**2)
                                                    ixy -= triangle_mass * x * y
                                                    ixz -= triangle_mass * x * z
                                                    iyz -= triangle_mass * y * z
                                        # Final mass calculation based on total volume and density
                                        mass = density * total_volume if total_volume > 0 else 0
                                        # Free the mesh after use
                                        obj.evaluated_get(depsgraph).to_mesh_clear()
                                        return (ixx, ixy, ixz, iyy, iyz, izz), mass, np.array(obj.location)  # Convert location to NumPy array

                                    def apply_parallel_axis_theorem(inertia_tensor, mass, obj_com, group_com):
                                        """Apply the parallel axis theorem to adjust the object's inertia tensor to the group's center of mass."""
                                        # Distance vector from the object's center of mass to the group's center of mass
                                        d = obj_com - group_com
                                        d_squared = np.dot(d, d)
                                        # Identity matrix for the size of 3x3
                                        identity_matrix = np.identity(3)
                                        # Outer product of the distance vector with itself
                                        outer_dd = np.outer(d, d)
                                        # Construct the object's original inertia tensor in 3x3 matrix form
                                        I_obj = np.array([
                                            [inertia_tensor[0], inertia_tensor[1], inertia_tensor[2]],
                                            [inertia_tensor[1], inertia_tensor[3], inertia_tensor[4]],
                                            [inertia_tensor[2], inertia_tensor[4], inertia_tensor[5]]
                                        ])
                                        # Apply the parallel axis theorem: I_adjusted = I_object + m * (d^2 * I - outer(d, d))
                                        I_adjusted = I_obj + mass * (d_squared * identity_matrix - outer_dd)
                                        return I_adjusted

                                    def merge_inertia_tensors(tensors, masses, centers_of_mass, group_com):
                                        """Merge multiple inertia tensors and masses into one."""
                                        merged_tensor = np.zeros((3, 3))
                                        total_mass = sum(masses)
                                        for i, (tensor, mass, obj_com) in enumerate(zip(tensors, masses, centers_of_mass)):
                                            if mass > 0:
                                                # Adjust tensor to the group's center of mass
                                                adjusted_tensor = apply_parallel_axis_theorem(tensor, mass, obj_com, group_com)
                                                merged_tensor += adjusted_tensor
                                        return merged_tensor, total_mass

                                    def output_inertia_tensor(inertia, mass, com):
                                        """Store the inertia tensor in a string."""
                                        output = "\n    <inertial>\n"
                                        output += "      <inertia>\n"
                                        output += f"        <ixx>{inertia[0, 0]:.24f}</ixx>\n"
                                        output += f"        <ixy>{inertia[0, 1]:.24f}</ixy>\n"
                                        output += f"        <ixz>{inertia[0, 2]:.24f}</ixz>\n"
                                        output += f"        <iyy>{inertia[1, 1]:.24f}</iyy>\n"
                                        output += f"        <iyz>{inertia[1, 2]:.24f}</iyz>\n"
                                        output += f"        <izz>{inertia[2, 2]:.24f}</izz>\n"
                                        output += "      </inertia>\n"
                                        output += f"      <mass>{round(mass, 6)}</mass>\n"
                                        output += f"      <pose>{round(com[0], 6)} {round(com[1], 6)} {round(com[2], 6)} 0 0 0</pose>\n"
                                        output += "    </inertial>"
                                        return output  # Return the output string
                                    # Main execution
                                    selected_objects = bpy.context.selected_objects
                                    output_string = ""  # Initialize the output string
                                    if selected_objects:
                                        total_inertia_tensor = np.zeros((3, 3))
                                        total_mass = 0.0
                                        center_of_mass = np.zeros(3)
                                        centers_of_mass = []
                                        tensors = []
                                        masses = []
                                        # First pass: calculate individual object properties
                                        for obj in selected_objects:
                                            inertia_tensor, mass, obj_com = calculate_inertia_tensor(obj)
                                            tensors.append(inertia_tensor)
                                            masses.append(mass)
                                            centers_of_mass.append(obj_com)
                                            total_mass += mass
                                            # Calculate the weighted center of mass
                                            if mass > 0:
                                                center_of_mass += obj_com * mass
                                        # Compute the final center of mass for the group
                                        if total_mass > 0:
                                            center_of_mass /= total_mass
                                        # Second pass: adjust each tensor to the group's center of mass
                                        total_inertia_tensor, total_mass = merge_inertia_tensors(tensors, masses, centers_of_mass, center_of_mass)
                                        # Generate the output string
                                        output_string = output_inertia_tensor(total_inertia_tensor, total_mass, center_of_mass)
                                        # Optionally, print the output string
                                        print(output_string)
                                    else:
                                        print("No object selected.")
                                    with open(bpy.context.scene.sna_userpath, mode='a') as file_CD444:
                                        file_CD444.write(output_string)
                                    bpy.ops.object.delete(confirm=False)
                        for i_AD620 in range(len(bpy.data.collections[i_C07BB].children)):
                            if '_visual' in bpy.data.collections[i_C07BB].children[i_AD620].name:
                                for i_4CB84 in range(len(bpy.data.collections[i_C07BB].children[i_AD620].all_objects)):
                                    bpy.data.collections[i_C07BB].children[i_AD620].all_objects[i_4CB84].select_set(state=True, )
                                    bpy.context.view_layer.objects.active = bpy.data.collections[i_C07BB].children[i_AD620].all_objects[i_4CB84]
                                bpy.ops.object.duplicate_move()
                                bpy.ops.object.join('INVOKE_DEFAULT', )
                                bpy.ops.object.transform_apply('INVOKE_DEFAULT', )
                                bpy.context.view_layer.objects.active.name = bpy.context.view_layer.objects.active.users_collection[0].name.replace('_visual', '')
                                if (bpy.context.scene.sna_exportfiletype == 'glb'):
                                    bpy.ops.export_scene.gltf(filepath=os.path.join(bpy.path.abspath(bpy.context.scene.sna_filepath),bpy.path.abspath(bpy.data.scenes[i_6691E].name.replace('_model', ''))) + '/' + bpy.context.view_layer.objects.active.name, check_existing=False, export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT', use_selection=True, export_yup=False, export_apply=True, export_animations=False, export_morph=False)
                                    with open(bpy.context.scene.sna_userpath, mode='a') as file_982D0:
                                        file_982D0.write('\n      <visual name ="' + bpy.context.view_layer.objects.active.name + '">\n' + '        <geometry>\n' + '          <mesh>\n' + '            <uri>' + bpy.context.scene.sna_sdf_export_path + bpy.context.view_layer.objects.active.name + '.' + bpy.context.scene.sna_exportfiletype + '</uri>\n' + '          </mesh>\n' + '        </geometry>\n' + '      </visual>')
                                    bpy.ops.object.delete()
                                else:
                                    if (bpy.context.scene.sna_exportfiletype == 'gltf'):
                                        bpy.ops.export_scene.gltf(filepath=os.path.join(bpy.path.abspath(bpy.context.scene.sna_filepath),bpy.path.abspath(bpy.data.scenes[i_6691E].name.replace('_model', ''))) + '/' + bpy.context.view_layer.objects.active.name, check_existing=False, export_format='GLTF_SEPARATE', export_texcoords=True, export_normals=True, export_materials='EXPORT', use_selection=True, export_yup=False, export_apply=True, export_animations=False, export_morph=False)
                                    else:
                                        if (bpy.context.scene.sna_exportfiletype == 'dae'):
                                            bpy.ops.wm.collada_export(filepath=os.path.join(bpy.path.abspath(bpy.context.scene.sna_filepath),bpy.path.abspath(bpy.data.scenes[i_6691E].name.replace('_model', ''))) + '/' + bpy.context.view_layer.objects.active.name, check_existing=False, apply_modifiers=True, selected=True, triangulate=True)
                            else:
                                if '_colliders' in bpy.data.collections[i_C07BB].children[i_AD620].name:
                                    for i_2981E in range(len(bpy.data.collections[i_C07BB].children[i_AD620].all_objects)):
                                        obj = bpy.data.collections[i_C07BB].children[i_AD620].all_objects[i_2981E]
                                        file_path = bpy.context.scene.sna_userpath
                                        # Select object
                                        obj.select_set(True)
                                        # Set origin to zero
                                        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                                        # Deselect all objects
                                        bpy.ops.object.select_all(action='DESELECT')
                                        with open(file_path, 'a') as file:
                                            file.write(
                                            f"\n<collision name=\"{obj.name}\">"
                                            )
                                            if "_meshcollider" not in obj.name:
                                                file.write(
                                                    f"\n  <pose>{obj.location.x:.6f} {obj.location.y:.6f} {obj.location.z:.6f} {obj.matrix_world.to_euler().x:.6f} {obj.matrix_world.to_euler().y:.6f} {obj.matrix_world.to_euler().z:.6f}</pose>"
                                                )
                                            file.write(
                                            f"\n  <geometry>"
                                            )
                                            # Check if the object name contains "_meshcollider"
                                            if "_meshcollider" in obj.name:
                                                file.write(
                                                    "\n    <mesh>"
                                                    f"\n      <uri>{obj.name.replace('.', '')}.stl</uri>"
                                                    "\n    </mesh>"
                                                )
                                            # Box collider
                                            elif "_box" in obj.name:
                                                file.write(
                                                    "\n    <box>"
                                                    f"\n      <size>{obj.dimensions.x:.6f} {obj.dimensions.y:.6f} {obj.dimensions.z:.6f}</size>"
                                                    "\n    </box>"
                                                )
                                            # Cylinder collider
                                            elif "_cylinder" in obj.name:
                                                file.write(
                                                    "\n    <cylinder>"
                                                    f"\n      <radius>{obj.dimensions.x:.6f}</radius>"
                                                    f"\n      <length>{obj.dimensions.z:.6f}</length>"
                                                    "\n    </cylinder>"
                                                )
                                            # Sphere collider
                                            elif "_sphere" in obj.name:
                                                file.write(
                                                    "\n    <ellipsoid>"
                                                    f"\n      <size>{obj.dimensions.x:.6f} {obj.dimensions.y:.6f} {obj.dimensions.z:.6f}</size>"
                                                    "\n    </ellipsoid>"
                                                )
                                            # Cone collider
                                            elif "_cone" in obj.name:
                                                file.write(
                                                    "\n    <cone>"
                                                    f"\n      <radius>{obj.dimensions.x:.6f}</radius>"
                                                    f"\n      <length>{obj.dimensions.z:.6f}</length>"
                                                    "\n    </cone>"
                                                )
                                            # Plane collider
                                            elif "_plane" in obj.name:
                                                file.write(
                                                    "\n    <plane>"
                                                    f"\n      <size>{obj.dimensions.x:.6f} {obj.dimensions.y:.6f}</size>"
                                                    "\n    </plane>"
                                                )
                                            # Close the geometry and collision tags
                                            file.write(
                                                "\n  </geometry>"
                                                "\n</collision>"
                                            )
                                        bpy.ops.object.select_all('INVOKE_DEFAULT', action='DESELECT')
                        with open(bpy.context.scene.sna_userpath, mode='a') as file_081DE:
                            file_081DE.write('\n    </link>')
            bpy.ops.sna.sdf_link_clone_2564f('INVOKE_DEFAULT', )
            bpy.ops.sna.sdf_include_0a203('INVOKE_DEFAULT', )
            for i_B7DF0 in range(len(bpy.context.view_layer.objects)):
                obj = bpy.context.view_layer.objects[i_B7DF0]
                output = None
                import math
                output = ""
                type = "prismatic"
                name = "joint_test"
                pose = "0 0 0 0 0 0"
                parent = "parent"
                child = "child"
                axis = "0 0 0"
                limitlower = "-45"
                limitupper = "45"
                # Check if the object is visible and of type 'EMPTY'
                if obj.visible_get() and obj.type == 'EMPTY' and "_joint" in obj.name:
                    # Set joint properties
                    name = obj.name
                    pose_values = [round(value, 6) for value in obj.location]
                    pose_orientation = "0 0 0"
                    pose = " ".join(str(value if abs(value) >= 1e-5 else 0) for value in pose_values) + " " + pose_orientation
                    parent = obj.sna_parent.name if obj.sna_parent else "NONE"
                    child = obj.sna_child.name if obj.sna_child else "NONE"
                    # Define joint type based on object name
                    if "_fixed" in obj.name:
                        type = "fixed"
                    elif "_revolute" in obj.name:
                        type = "revolute"
                    elif "_prismatic" in obj.name:
                        type = "prismatic"
                    # Start building the joint XML block
                    output = f'\n<joint name="{name}" type="{type}">'
                    output += f'\n  <pose>{pose}</pose>'
                    output += f'\n  <parent>{parent}</parent>'
                    output += f'\n  <child>{child}</child>'
                    # Add axis and limits if applicable
                    if type in ["prismatic", "revolute"]:
                        rotation_matrix = Euler(obj.rotation_euler, 'XYZ').to_matrix()
                        y_axis_vector = rotation_matrix @ Vector((0, 1, 0))
                        axis_values = [round(value, 6) for value in y_axis_vector]
                        axis = " ".join(str(value if abs(value) >= 1e-5 else 0) for value in axis_values)
                        if type == "revolute" and obj.sna_iscontinuous == True:
                            limitupper = "-1.0e+9"
                            limitlower = "-1.0e+9"
                        elif type == "revolute" and obj.sna_iscontinuous == False:
                            limitupper = round(obj.sna_limits_upper, 6)
                            limitlower = round(obj.sna_limits_lower, 6)
                        elif type == "prismatic":
                            limitupper = round(obj.sna_limits_upper_distance, 6)
                            limitlower = round(obj.sna_limits_lower_distance, 6)
                        elif obj.sna_iscontinuous == True:
                            limitupper = "-1.0e+9"
                            limitlower = "-1.0e+9"
                            print (obj + "is true")
                        output += "\n  <axis>"
                        output += f"\n    <xyz>{axis}</xyz>"
                        output += "\n    <limit>"
                        output += f"\n      <lower>{limitlower}</lower>"
                        output += f"\n      <upper>{limitupper}</upper>"
                        output += "\n    </limit>"
                        output += "\n  </axis>"
                    # End joint XML block
                    output += "\n</joint>"
                output = str(output)
                with open(bpy.context.scene.sna_userpath, mode='a') as file_4B279:
                    file_4B279.write(output)
            with open(bpy.context.scene.sna_userpath, mode='a') as file_647FC:
                file_647FC.write('\n  </model>' + '\n</sdf>')
            sdf_file = bpy.context.scene.sna_userpath
            # Path to the original SDF file
            #sdf_file = "path/to/your/model.sdf"
            # Load and parse the SDF file
            tree = ET.parse(sdf_file)
            root = tree.getroot()
            # Function to find the original link by removing '_clone' from the clone link's name

            def find_original_link(root, clone_name):
                original_name = clone_name.replace("_clone", "")
                return root.find(f".//link[@name='{original_name}']")
            # Loop through all links and update clones
            for link in root.findall(".//link"):
                if "_clone" in link.attrib["name"]:  # Identify clone links
                    original_link = find_original_link(root, link.attrib["name"])
                    if original_link is not None:
                        # Copy all child elements from the original link to the clone link
                        for child in original_link:
                            link.append(child)
            # Overwrite the original SDF file with the modified content
            tree.write(sdf_file, encoding="utf-8", xml_declaration=True)
            print(f"SDF file '{sdf_file}' updated successfully!")
            input_file_path = bpy.context.scene.sna_userpath
            #input_file_path = r"G:\My Drive\Tools\WIP\Blender SDF Gen\V3\ExportTest\arm\model.sdf"
            import xml.dom.minidom
            # Function to format an XML file with indentation

            def format_xml_file(input_file_path):
                # Read the XML content from the file
                with open(input_file_path, 'r') as file:
                    xml_string = file.read()
                # Parse the XML string
                dom = xml.dom.minidom.parseString(xml_string)
                # Convert it back to a pretty-printed XML string
                pretty_xml = dom.toprettyxml(indent="  ")  # 4 spaces for indentation
                # Remove extra blank lines
                cleaned_xml = re.sub(r'\n\s*\n', '\n', pretty_xml).strip()  # Remove extra newlines
                # Write the pretty XML back to the same file (overwrite)
                with open(input_file_path, 'w') as file:
                    file.write(cleaned_xml)
            # Call the function
            format_xml_file(input_file_path)
            bpy.context.window.scene = bpy.context.window_manager.sna_initialscene
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Set_File_Path_Fb37A(bpy.types.Operator):
    bl_idname = "sna.set_file_path_fb37a"
    bl_label = "Set File Path"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (bpy.context.scene.sna_sdf_file_paths == 'Blank'):
            bpy.context.scene.sna_sdf_export_path = ''
        else:
            if (bpy.context.scene.sna_sdf_file_paths == 'Same as export path'):
                bpy.context.scene.sna_sdf_export_path = bpy.context.scene.sna_filepath + bpy.context.scene.sna_sdf_export_modelname + '/'
            else:
                if (bpy.context.scene.sna_sdf_file_paths == 'Custom'):
                    bpy.context.scene.sna_sdf_export_path = bpy.context.scene.sna_sdf_custom_path + bpy.context.scene.sna_sdf_export_modelname + '/'
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Sdf_Link_Clone_2564F(bpy.types.Operator):
    bl_idname = "sna.sdf_link_clone_2564f"
    bl_label = "SDF Link Clone"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        for i_06EBF in range(len(bpy.context.scene.objects)):
            if '_clone' in bpy.context.scene.objects[i_06EBF].name:
                with open(bpy.context.scene.sna_userpath, mode='a') as file_9A7A1:
                    file_9A7A1.write('\n    <link name ="' + bpy.context.scene.objects[i_06EBF].name + '">' + '\n      <pose>' + str(round(bpy.context.scene.objects[i_06EBF].location[0], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_06EBF].location[1], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_06EBF].location[2], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_06EBF].rotation_euler[0], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_06EBF].rotation_euler[1], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_06EBF].rotation_euler[2], abs(4))) + '</pose>' + '\n    </link>')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Sdf_Include_0A203(bpy.types.Operator):
    bl_idname = "sna.sdf_include_0a203"
    bl_label = "SDF Include"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        for i_8FAF4 in range(len(bpy.context.scene.objects)):
            if '_include' in bpy.context.scene.objects[i_8FAF4].name:
                with open(bpy.context.scene.sna_userpath, mode='a') as file_820FF:
                    file_820FF.write('\n    <include' + '' + '' + '>' + '\n      <name>' + bpy.context.scene.name + '</name>' + '\n      <pose>' + str(round(bpy.context.scene.objects[i_8FAF4].location[0], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_8FAF4].location[1], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_8FAF4].location[2], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_8FAF4].rotation_euler[0], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_8FAF4].rotation_euler[1], abs(4))) + ' ' + str(round(bpy.context.scene.objects[i_8FAF4].rotation_euler[2], abs(4))) + '</pose>' + '\n      <uri>' + bpy.context.scene.sna_sdf_export_path + bpy.context.scene.name + '</uri>' + '\n    </include>')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


_0BF7C_running = False
class SNA_OT_Selectflatfaces_0Bf7C(bpy.types.Operator):
    bl_idname = "sna.selectflatfaces_0bf7c"
    bl_label = "SelectFlatFaces"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    cursor = "CROSSHAIR"
    _handle = None
    _event = {}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        if not True or context.area.spaces[0].bl_rna.identifier == 'SpaceView3D':
            return not False
        return False

    def save_event(self, event):
        event_options = ["type", "value", "alt", "shift", "ctrl", "oskey", "mouse_region_x", "mouse_region_y", "mouse_x", "mouse_y", "pressure", "tilt"]
        if bpy.app.version >= (3, 2, 1):
            event_options += ["type_prev", "value_prev"]
        for option in event_options: self._event[option] = getattr(event, option)

    def draw_callback_px(self, context):
        event = self._event
        if event.keys():
            event = dotdict(event)
            try:
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_4590E, y_4590E = (410.0, 1000.0)
                    blf.position(font_id, x_4590E, y_4590E, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 0.06046402454376221, 0.032939016819000244, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 0:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 0)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, 'Choose a flat surface')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_3F7BB, y_3F7BB = (400.0, 930.0)
                    blf.position(font_id, x_3F7BB, y_3F7BB, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 1493:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 1493)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Ctrl + Shift + C] Generate Cylinder')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_C45A9, y_C45A9 = (400.0, 860.0)
                    blf.position(font_id, x_C45A9, y_C45A9, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 1493:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 1493)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Ctrl + Shift + B] Generate Box')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_AF615, y_AF615 = (400.0, 790.0)
                    blf.position(font_id, x_AF615, y_AF615, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 1493:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 1493)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Ctrl + Shift + V] Generate Cone')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_ED7B9, y_ED7B9 = (400.0, 720.0)
                    blf.position(font_id, x_ED7B9, y_ED7B9, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 1493:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 1493)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Ctrl + Shift + P] Generate Plane')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_5FB65, y_5FB65 = (400.0, 650.0)
                    blf.position(font_id, x_5FB65, y_5FB65, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 1493:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 1493)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[ESC] Cancel')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
            except Exception as error:
                print(error)

    def execute(self, context):
        global _0BF7C_running
        _0BF7C_running = False
        context.window.cursor_set("DEFAULT")
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        for area in context.screen.areas:
            area.tag_redraw()
        return {"FINISHED"}

    def modal(self, context, event):
        global _0BF7C_running
        if not context.area or not _0BF7C_running:
            self.execute(context)
            return {'CANCELLED'}
        self.save_event(event)
        context.area.tag_redraw()
        context.window.cursor_set('CROSSHAIR')
        try:
            if 'RELEASE' in event.value_prev:
                bpy.ops.mesh.faces_select_linked_flat('INVOKE_DEFAULT', sharpness=0.10000000149011612)
            else:
                if (event.type == 'C' and event.value == 'PRESS' and event.alt == False and event.shift == True and event.ctrl == True):
                    bpy.ops.sna.cylindercap_0f9d8('INVOKE_DEFAULT', )
                    bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
                    if event.type in ['RIGHTMOUSE', 'ESC']:
                        self.execute(context)
                        return {'CANCELLED'}
                    self.execute(context)
                    return {"FINISHED"}
                else:
                    if (event.type == 'B' and event.value == 'PRESS' and event.alt == False and event.shift == True and event.ctrl == True):
                        bpy.ops.sna.boxcap_7899e('INVOKE_DEFAULT', )
                        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
                        if event.type in ['RIGHTMOUSE', 'ESC']:
                            self.execute(context)
                            return {'CANCELLED'}
                        self.execute(context)
                        return {"FINISHED"}
                    else:
                        if (event.type == 'V' and event.value == 'PRESS' and event.alt == False and event.shift == True and event.ctrl == True):
                            bpy.ops.sna.conecap_53679('INVOKE_DEFAULT', )
                            bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
                            if event.type in ['RIGHTMOUSE', 'ESC']:
                                self.execute(context)
                                return {'CANCELLED'}
                            self.execute(context)
                            return {"FINISHED"}
                        else:
                            if (event.type == 'P' and event.value == 'PRESS' and event.alt == False and event.shift == True and event.ctrl == True):
                                bpy.ops.sna.planecap_e5c55('INVOKE_DEFAULT', )
                                bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
                                if event.type in ['RIGHTMOUSE', 'ESC']:
                                    self.execute(context)
                                    return {'CANCELLED'}
                                self.execute(context)
                                return {"FINISHED"}
        except Exception as error:
            print(error)
        if event.type in ['RIGHTMOUSE', 'ESC']:
            self.execute(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global _0BF7C_running
        if _0BF7C_running:
            _0BF7C_running = False
            return {'FINISHED'}
        else:
            self.save_event(event)
            self.start_pos = (event.mouse_x, event.mouse_y)
            bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
            bpy.ops.object.mode_set_with_submode('INVOKE_DEFAULT', mode='EDIT', mesh_select_mode={'FACE'})
            bpy.ops.mesh.select_all('INVOKE_DEFAULT', action='DESELECT')
            args = (context,)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            _0BF7C_running = True
            return {'RUNNING_MODAL'}


class SNA_OT_Cylindercap_0F9D8(bpy.types.Operator):
    bl_idname = "sna.cylindercap_0f9d8"
    bl_label = "CylinderCap"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        collider['sna_activeobject'] = bpy.context.view_layer.objects.active.name
        bpy.ops.object.duplicate('INVOKE_DEFAULT', )
        bpy.context.scene.sna_duplicate_to_delete = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        exec("bpy.ops.mesh.select_all(action='INVERT')")
        bpy.ops.mesh.delete('INVOKE_DEFAULT', type='FACE')
        exec("bpy.ops.mesh.select_all(action='SELECT')")
        area_type = 'VIEW_3D'
        areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
        bpy.context.scene.tool_settings.use_transform_data_origin = True
        with bpy.context.temp_override(area=areas[0]):
            bpy.ops.transform.create_orientation(use=True)
            bpy.ops.object.editmode_toggle()
            transform_type = bpy.context.scene.transform_orientation_slots[0].type
            bpy.ops.transform.transform(mode='ALIGN', orient_type='Face', orient_matrix_type=transform_type, mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='ACTIVE', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
            bpy.ops.transform.delete_orientation()
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        exec('')
        exec('from mathutils import Vector')
        exec('bpy.context.active_object.location += 1.0 * bpy.context.active_object.matrix_world.to_quaternion() @ Vector((0, 0, -100))')
        euler_angles = bpy.context.view_layer.objects.active.rotation_euler
        normal_direction = None
        from mathutils import Euler
        # Convert Euler angles to a rotation matrix
        rotation_matrix = euler_angles.to_matrix()
        # Extract the normal direction from the rotation matrix
        normal_direction = rotation_matrix.to_3x3() @ mathutils.Vector((0, 0, 1))
        ray_direction_global_vec = normal_direction
        ray_origin_global_vec = bpy.context.view_layer.objects.active.location
        specified_object_name = collider['sna_activeobject']
        hit_location_global = None
        #import bpy
        from mathutils import Euler
        #ray_origin_global_vec = (1, 1, 1)
        #ray_direction_global_vec = (1, 1, 1)
        # Set the starting point for the ray (origin) in global coordinates
        ray_origin_global = mathutils.Vector(ray_origin_global_vec)
        # Set the direction of the ray (upwards along the positive Z-axis) in global coordinates
        ray_direction_global = mathutils.Vector(ray_direction_global_vec)
        # Set the maximum distance for the ray
        max_distance = 1000.0  # Adjust as needed
        # Specify the object name you want to cast rys against
        #specified_object_name = "Link4"
        # Ensure the scene is in OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Get the current dependency graph
        depsgraph = bpy.context.evaluated_depsgraph_get()
        hit_object_name = None
        hit_location_global = None
        # Iterate through all visible objects in the scene
        for obj in bpy.context.visible_objects:
            # Check if the current object is the specified object
            if obj.name == specified_object_name:
                # Convert the ray origin and direction to object local coordinates
                ray_origin_local = obj.matrix_world.inverted() @ ray_origin_global
                ray_direction_local = obj.matrix_world.inverted().to_3x3() @ ray_direction_global
                # Cast the ray for the specified object
                success, location, normal, index = obj.ray_cast(ray_origin_local, ray_direction_local)
                if success:
                    # Convert the hit location back to global coordinates
                    hit_location_global = obj.matrix_world @ location
                    print("Ray Hit Location (Global):", hit_location_global)
                    print("Hit Normal:", normal)
                    print("Face Index:", index)
                    hit_object_name = obj.name
                    break  # Exit the loop after the first hit
        # Check if any hits occurred
        if hit_object_name:
            print("Object Hit:", hit_object_name)
        #    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=hit_location_global)
        else:
            print("Ray did not hit anything within the specified distance on the specified object.")
        if (hit_location_global == None):
            genface['sna_rayfail'] = True
        exec('')
        exec('from mathutils import Vector')
        exec('bpy.context.active_object.location += 1.0 * bpy.context.active_object.matrix_world.to_quaternion() @ Vector((0, 0, 100))')
        if (tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0] >= tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[1]):
            bpy.ops.mesh.primitive_cylinder_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler, scale=(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0], tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0], 0.0))
            bpy.context.active_object.name = 'collider_cylinder'
            bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
            bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
            bpy.context.scene.tool_settings.use_transform_data_origin = False
            bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
            bpy.data.objects.remove(object=bpy.context.scene.sna_duplicate_to_delete, )
            bpy.ops.sna.select_cylinder_face_8a190('INVOKE_DEFAULT', )
            if genface['sna_rayfail']:
                prev_context = bpy.context.area.type
                bpy.context.area.type = 'VIEW_3D'
                bpy.ops.transform.translate(value=(0.0, 0.0, float(float(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0] * 3.0) * -1.0)), orient_type='LOCAL', orient_matrix_type='LOCAL', constraint_axis=(False, False, True))
                bpy.context.area.type = prev_context
            else:
                target_global_position = hit_location_global
                object_name = bpy.context.view_layer.objects.active.name
                import bmesh
                # Replace 'Cube' with the name of your object
                #object_name = 'Cylinder.013'
                # Replace these coordinates with your desired global position
                #target_global_position = Vector((7.05492, -15.1448, -2.33593))
                # Get the active object
                obj = bpy.data.objects.get(object_name)
                # Check if the object exists and is in Edit Mode
                if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
                    # Get the mesh data
                    mesh = bmesh.from_edit_mesh(obj.data)
                    # Check if there is at least one selected face
                    selected_faces = [f for f in mesh.faces if f.select]
                    if selected_faces:
                        # Calculate the translation vector to the target position
                        target_local_position = obj.matrix_world.inverted() @ target_global_position
                        translation_vector = target_local_position - selected_faces[0].calc_center_median()
                        # Move the selected face(s) to the target global position
                        for face in selected_faces:
                            for vert in face.verts:
                                vert.co += translation_vector
                        # Update the mesh
                        bmesh.update_edit_mesh(obj.data)
                        # Print the new location of the face after the update
                        updated_center = selected_faces[0].calc_center_median()
                        print("Updated Location of Selected Face(s):", obj.matrix_world @ updated_center)
                    else:
                        print("No faces selected.")
                else:
                    print("Object not found or not in Edit Mode.")
            bpy.context.view_layer.objects.active.sna_cylrad = bpy.context.view_layer.objects.active.dimensions[1]
        else:
            bpy.ops.mesh.primitive_cylinder_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler, scale=(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[1], tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[1], 0.0))
            bpy.context.active_object.name = 'collider_cylinder'
            bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
            bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
            bpy.context.scene.tool_settings.use_transform_data_origin = False
            bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
            bpy.data.objects.remove(object=bpy.context.scene.sna_duplicate_to_delete, )
            bpy.ops.sna.select_cylinder_face_8a190('INVOKE_DEFAULT', )
            if genface['sna_rayfail']:
                prev_context = bpy.context.area.type
                bpy.context.area.type = 'VIEW_3D'
                bpy.ops.transform.translate(value=(0.0, 0.0, float(float(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[1] * 3.0) * -1.0)), orient_type='LOCAL', orient_matrix_type='LOCAL', constraint_axis=(False, False, True))
                bpy.context.area.type = prev_context
            else:
                target_global_position = hit_location_global
                object_name = bpy.context.view_layer.objects.active.name
                import bmesh
                # Replace 'Cube' with the name of your object
                #object_name = 'Cylinder.013'
                # Replace these coordinates with your desired global position
                #target_global_position = Vector((7.05492, -15.1448, -2.33593))
                # Get the active object
                obj = bpy.data.objects.get(object_name)
                # Check if the object exists and is in Edit Mode
                if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
                    # Get the mesh data
                    mesh = bmesh.from_edit_mesh(obj.data)
                    # Check if there is at least one selected face
                    selected_faces = [f for f in mesh.faces if f.select]
                    if selected_faces:
                        # Calculate the translation vector to the target position
                        target_local_position = obj.matrix_world.inverted() @ target_global_position
                        translation_vector = target_local_position - selected_faces[0].calc_center_median()
                        # Move the selected face(s) to the target global position
                        for face in selected_faces:
                            for vert in face.verts:
                                vert.co += translation_vector
                        # Update the mesh
                        bmesh.update_edit_mesh(obj.data)
                        # Print the new location of the face after the update
                        updated_center = selected_faces[0].calc_center_median()
                        print("Updated Location of Selected Face(s):", obj.matrix_world @ updated_center)
                    else:
                        print("No faces selected.")
                else:
                    print("Object not found or not in Edit Mode.")
            bpy.context.view_layer.objects.active.sna_cylrad = bpy.context.view_layer.objects.active.dimensions[1]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Boxcap_7899E(bpy.types.Operator):
    bl_idname = "sna.boxcap_7899e"
    bl_label = "BoxCap"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        collider['sna_activeobject'] = bpy.context.view_layer.objects.active.name
        bpy.ops.mesh.faces_select_linked_flat('INVOKE_DEFAULT', )
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        bpy.ops.object.duplicate('INVOKE_DEFAULT', )
        bpy.context.scene.sna_duplicate_to_delete = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        exec("bpy.ops.mesh.select_all(action='INVERT')")
        bpy.ops.mesh.delete('INVOKE_DEFAULT', type='FACE')
        exec("bpy.ops.mesh.select_all(action='SELECT')")
        Variable = None
        area_type = 'VIEW_3D'
        areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
        bpy.context.scene.tool_settings.use_transform_data_origin = True
        with bpy.context.temp_override(area=areas[0]):
            bpy.ops.transform.create_orientation(use=True)
            bpy.ops.object.editmode_toggle()
            transform_type = bpy.context.scene.transform_orientation_slots[0].type
            bpy.ops.transform.transform(mode='ALIGN', orient_type='Face', orient_matrix_type=transform_type, mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='ACTIVE', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
            bpy.ops.transform.delete_orientation()
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        exec('')
        exec('from mathutils import Vector')
        exec('bpy.context.active_object.location += 1.0 * bpy.context.active_object.matrix_world.to_quaternion() @ Vector((0, 0, -100))')
        euler_angles = bpy.context.view_layer.objects.active.rotation_euler
        normal_direction = None
        from mathutils import Euler
        # Convert Euler angles to a rotation matrix
        rotation_matrix = euler_angles.to_matrix()
        # Extract the normal direction from the rotation matrix
        normal_direction = rotation_matrix.to_3x3() @ mathutils.Vector((0, 0, 1))
        ray_direction_global_vec = normal_direction
        ray_origin_global_vec = bpy.context.view_layer.objects.active.location
        specified_object_name = collider['sna_activeobject']
        hit_location_global = None
        #import bpy
        from mathutils import Euler
        #ray_origin_global_vec = (1, 1, 1)
        #ray_direction_global_vec = (1, 1, 1)
        # Set the starting point for the ray (origin) in global coordinates
        ray_origin_global = mathutils.Vector(ray_origin_global_vec)
        # Set the direction of the ray (upwards along the positive Z-axis) in global coordinates
        ray_direction_global = mathutils.Vector(ray_direction_global_vec)
        # Set the maximum distance for the ray
        max_distance = 1000.0  # Adjust as needed
        # Specify the object name you want to cast rys against
        #specified_object_name = "Link4"
        # Ensure the scene is in OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Get the current dependency graph
        depsgraph = bpy.context.evaluated_depsgraph_get()
        hit_object_name = None
        hit_location_global = None
        # Iterate through all visible objects in the scene
        for obj in bpy.context.visible_objects:
            # Check if the current object is the specified object
            if obj.name == specified_object_name:
                # Convert the ray origin and direction to object local coordinates
                ray_origin_local = obj.matrix_world.inverted() @ ray_origin_global
                ray_direction_local = obj.matrix_world.inverted().to_3x3() @ ray_direction_global
                # Cast the ray for the specified object
                success, location, normal, index = obj.ray_cast(ray_origin_local, ray_direction_local)
                if success:
                    # Convert the hit location back to global coordinates
                    hit_location_global = obj.matrix_world @ location
                    print("Ray Hit Location (Global):", hit_location_global)
                    print("Hit Normal:", normal)
                    print("Face Index:", index)
                    hit_object_name = obj.name
                    break  # Exit the loop after the first hit
        # Check if any hits occurred
        if hit_object_name:
            print("Object Hit:", hit_object_name)
        #    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=hit_location_global)
        else:
            print("Ray did not hit anything within the specified distance on the specified object.")
        exec('')
        exec('from mathutils import Vector')
        exec('bpy.context.active_object.location += 1.0 * bpy.context.active_object.matrix_world.to_quaternion() @ Vector((0, 0, 100))')
        bpy.ops.mesh.primitive_cube_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, rotation=(bpy.context.view_layer.objects.active.rotation_euler[0], bpy.context.view_layer.objects.active.rotation_euler[1], bpy.context.view_layer.objects.active.rotation_euler[2]), scale=tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0))
        bpy.context.active_object.name = 'collider_box'
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.data.scenes['Scene'].tool_settings.use_transform_data_origin = False
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.data.objects.remove(object=bpy.context.scene.sna_duplicate_to_delete, )
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        bpy.ops.mesh.select_mode('INVOKE_DEFAULT', type='FACE')
        bpy.ops.mesh.select_all('INVOKE_DEFAULT', action='DESELECT')
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        bpy.context.view_layer.objects.active.data.polygons[4].select = True
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        bpy.ops.wm.tool_set_by_id('INVOKE_DEFAULT', name='builtin.move')
        target_global_position = hit_location_global
        object_name = bpy.context.view_layer.objects.active.name
        import bmesh
        # Replace 'Cube' with the name of your object
        #object_name = 'Cylinder.013'
        # Replace these coordinates with your desired global position
        #target_global_position = Vector((7.05492, -15.1448, -2.33593))
        # Get the active object
        obj = bpy.data.objects.get(object_name)
        # Check if the object exists and is in Edit Mode
        if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
            # Get the mesh data
            mesh = bmesh.from_edit_mesh(obj.data)
            # Check if there is at least one selected face
            selected_faces = [f for f in mesh.faces if f.select]
            if selected_faces:
                # Calculate the translation vector to the target position
                target_local_position = obj.matrix_world.inverted() @ target_global_position
                translation_vector = target_local_position - selected_faces[0].calc_center_median()
                # Move the selected face(s) to the target global position
                for face in selected_faces:
                    for vert in face.verts:
                        vert.co += translation_vector
                # Update the mesh
                bmesh.update_edit_mesh(obj.data)
                # Print the new location of the face after the update
                updated_center = selected_faces[0].calc_center_median()
                print("Updated Location of Selected Face(s):", obj.matrix_world @ updated_center)
            else:
                print("No faces selected.")
        else:
            print("Object not found or not in Edit Mode.")
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Conecap_53679(bpy.types.Operator):
    bl_idname = "sna.conecap_53679"
    bl_label = "ConeCap"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        collider['sna_activeobject'] = bpy.context.view_layer.objects.active.name
        bpy.ops.object.duplicate('INVOKE_DEFAULT', )
        bpy.context.scene.sna_duplicate_to_delete = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        exec("bpy.ops.mesh.select_all(action='INVERT')")
        bpy.ops.mesh.delete('INVOKE_DEFAULT', type='FACE')
        exec("bpy.ops.mesh.select_all(action='SELECT')")
        area_type = 'VIEW_3D'
        areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
        bpy.context.scene.tool_settings.use_transform_data_origin = True
        with bpy.context.temp_override(area=areas[0]):
            bpy.ops.transform.create_orientation(use=True)
            bpy.ops.object.editmode_toggle()
            transform_type = bpy.context.scene.transform_orientation_slots[0].type
            bpy.ops.transform.transform(mode='ALIGN', orient_type='Face', orient_matrix_type=transform_type, mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='ACTIVE', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
            bpy.ops.transform.delete_orientation()
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        exec('')
        exec('from mathutils import Vector')
        exec('bpy.context.active_object.location += 1.0 * bpy.context.active_object.matrix_world.to_quaternion() @ Vector((0, 0, -100))')
        euler_angles = bpy.context.view_layer.objects.active.rotation_euler
        normal_direction = None
        from mathutils import Euler
        # Convert Euler angles to a rotation matrix
        rotation_matrix = euler_angles.to_matrix()
        # Extract the normal direction from the rotation matrix
        normal_direction = rotation_matrix.to_3x3() @ mathutils.Vector((0, 0, 1))
        ray_direction_global_vec = normal_direction
        ray_origin_global_vec = bpy.context.view_layer.objects.active.location
        specified_object_name = collider['sna_activeobject']
        hit_location_global = None
        #import bpy
        from mathutils import Euler
        #ray_origin_global_vec = (1, 1, 1)
        #ray_direction_global_vec = (1, 1, 1)
        # Set the starting point for the ray (origin) in global coordinates
        ray_origin_global = mathutils.Vector(ray_origin_global_vec)
        # Set the direction of the ray (upwards along the positive Z-axis) in global coordinates
        ray_direction_global = mathutils.Vector(ray_direction_global_vec)
        # Set the maximum distance for the ray
        max_distance = 1000.0  # Adjust as needed
        # Specify the object name you want to cast rys against
        #specified_object_name = "Link4"
        # Ensure the scene is in OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Get the current dependency graph
        depsgraph = bpy.context.evaluated_depsgraph_get()
        hit_object_name = None
        hit_location_global = None
        # Iterate through all visible objects in the scene
        for obj in bpy.context.visible_objects:
            # Check if the current object is the specified object
            if obj.name == specified_object_name:
                # Convert the ray origin and direction to object local coordinates
                ray_origin_local = obj.matrix_world.inverted() @ ray_origin_global
                ray_direction_local = obj.matrix_world.inverted().to_3x3() @ ray_direction_global
                # Cast the ray for the specified object
                success, location, normal, index = obj.ray_cast(ray_origin_local, ray_direction_local)
                if success:
                    # Convert the hit location back to global coordinates
                    hit_location_global = obj.matrix_world @ location
                    print("Ray Hit Location (Global):", hit_location_global)
                    print("Hit Normal:", normal)
                    print("Face Index:", index)
                    hit_object_name = obj.name
                    break  # Exit the loop after the first hit
        # Check if any hits occurred
        if hit_object_name:
            print("Object Hit:", hit_object_name)
        #    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=hit_location_global)
        else:
            print("Ray did not hit anything within the specified distance on the specified object.")
        if (hit_location_global == None):
            pass
        exec('')
        exec('from mathutils import Vector')
        exec('bpy.context.active_object.location += 1.0 * bpy.context.active_object.matrix_world.to_quaternion() @ Vector((0, 0, 100))')
        bpy.ops.mesh.primitive_cone_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler, scale=(tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0], tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0)[0], 0.0))
        bpy.context.active_object.name = 'collider_cone'
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        bpy.context.scene.tool_settings.use_transform_data_origin = False
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.data.objects.remove(object=bpy.context.scene.sna_duplicate_to_delete, )
        bpy.ops.sna.select_cone_tip_6a0b7('INVOKE_DEFAULT', )
        if genface['sna_rayfail']:
            prev_context = bpy.context.area.type
            bpy.context.area.type = 'VIEW_3D'
            bpy.ops.transform.translate(value=(0.0, 0.0, 0.10000000149011612), orient_type='LOCAL', orient_matrix_type='LOCAL', constraint_axis=(False, False, True))
            bpy.context.area.type = prev_context
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Select_Cone_Tip_6A0B7(bpy.types.Operator):
    bl_idname = "sna.select_cone_tip_6a0b7"
    bl_label = "Select cone tip"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        bpy.ops.mesh.select_mode('INVOKE_DEFAULT', type='VERT')
        bpy.ops.mesh.select_all('INVOKE_DEFAULT', action='DESELECT')
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        bpy.context.view_layer.objects.active.data.vertices[32].select = True
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        bpy.ops.wm.tool_set_by_id('INVOKE_DEFAULT', name='builtin.move')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Planecap_E5C55(bpy.types.Operator):
    bl_idname = "sna.planecap_e5c55"
    bl_label = "PlaneCap"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        collider['sna_activeobject'] = bpy.context.view_layer.objects.active.name
        bpy.ops.mesh.faces_select_linked_flat('INVOKE_DEFAULT', )
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        bpy.ops.object.duplicate('INVOKE_DEFAULT', )
        bpy.context.scene.sna_duplicate_to_delete = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        exec("bpy.ops.mesh.select_all(action='INVERT')")
        bpy.ops.mesh.delete('INVOKE_DEFAULT', type='FACE')
        exec("bpy.ops.mesh.select_all(action='SELECT')")
        Variable = None
        area_type = 'VIEW_3D'
        areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
        bpy.context.scene.tool_settings.use_transform_data_origin = True
        with bpy.context.temp_override(area=areas[0]):
            bpy.ops.transform.create_orientation(use=True)
            bpy.ops.object.editmode_toggle()
            transform_type = bpy.context.scene.transform_orientation_slots[0].type
            bpy.ops.transform.transform(mode='ALIGN', orient_type='Face', orient_matrix_type=transform_type, mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='ACTIVE', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
            bpy.ops.transform.delete_orientation()
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        bpy.ops.mesh.primitive_plane_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, rotation=(bpy.context.view_layer.objects.active.rotation_euler[0], bpy.context.view_layer.objects.active.rotation_euler[1], bpy.context.view_layer.objects.active.rotation_euler[2]))
        bpy.context.view_layer.objects.active.dimensions = bpy.context.scene.sna_duplicate_to_delete.dimensions
        bpy.context.active_object.name = 'collider_plane'
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        bpy.data.scenes['Scene'].tool_settings.use_transform_data_origin = False
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.data.objects.remove(object=bpy.context.scene.sna_duplicate_to_delete, )
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        bpy.ops.mesh.select_mode('INVOKE_DEFAULT', type='FACE')
        bpy.ops.mesh.select_all('INVOKE_DEFAULT', action='DESELECT')
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Mesh_85D40(bpy.types.Operator):
    bl_idname = "sna.mesh_85d40"
    bl_label = "Mesh"
    bl_description = "Generates a convex hull mesh collider"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        if 'OBJECT'==bpy.context.mode:
            exec('bpy.ops.object.duplicate()')
            exec('bpy.ops.object.join()')
            collider['sna_joinedobj'] = bpy.context.view_layer.objects.active
            bpy.context.view_layer.objects.active.name = bpy.context.view_layer.objects.active.name + '_meshcollider'
            bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
            exec('bpy.ops.mesh.select_mode(type="VERT")')
            exec("bpy.ops.mesh.select_all(action='SELECT')")
            exec('bpy.ops.mesh.convex_hull()')
            bpy.ops.object.modifier_add('INVOKE_DEFAULT', type='DECIMATE')
            exec('bpy.ops.object.editmode_toggle()')
            bpy.ops.object.modifier_add('INVOKE_DEFAULT', type='SOLIDIFY')
            bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
            bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
            bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
            bpy.context.view_layer.objects.active.modifiers['Solidify.001'].name = 'Inflate'
            exec('bpy.context.object.modifiers["Inflate"].use_rim_only = True')
            exec('bpy.context.object.modifiers["Inflate"].offset = 1')
            exec('bpy.context.object.modifiers["Inflate"].use_even_offset = True')
        else:
            if 'EDIT_MESH'==bpy.context.mode:
                bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
                exec('bpy.ops.object.duplicate()')
                bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
                exec("bpy.ops.mesh.select_all(action='INVERT')")
                bpy.ops.mesh.delete('INVOKE_DEFAULT', type='FACE')
                exec('bpy.ops.mesh.convex_hull()')
                bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
                bpy.ops.object.modifier_add('INVOKE_DEFAULT', type='DECIMATE')
                bpy.ops.object.modifier_add('INVOKE_DEFAULT', type='SOLIDIFY')
                bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
                bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
                bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
                bpy.context.view_layer.objects.active.modifiers['Solidify.001'].name = 'Inflate'
                exec('bpy.context.object.modifiers["Inflate"].use_rim_only = True')
                exec('bpy.context.object.modifiers["Inflate"].offset = 1')
                exec('bpy.context.object.modifiers["Inflate"].use_even_offset = True')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_UTILITIES_9531D(bpy.types.Panel):
    bl_label = 'Utilities'
    bl_idname = 'SNA_PT_UTILITIES_9531D'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'SDF Gen'
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_CF752 = layout.box()
        box_CF752.alert = False
        box_CF752.enabled = True
        box_CF752.active = True
        box_CF752.use_property_split = False
        box_CF752.use_property_decorate = False
        box_CF752.alignment = 'Expand'.upper()
        box_CF752.scale_x = 1.0
        box_CF752.scale_y = 1.0
        if not True: box_CF752.operator_context = "EXEC_DEFAULT"
        box_CF752.label(text='Utilities', icon_value=0)
        row_5533A = box_CF752.row(heading='', align=False)
        row_5533A.alert = False
        row_5533A.enabled = True
        row_5533A.active = True
        row_5533A.use_property_split = False
        row_5533A.use_property_decorate = False
        row_5533A.scale_x = 1.0
        row_5533A.scale_y = 1.0
        row_5533A.alignment = 'Expand'.upper()
        row_5533A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_5533A.operator('sna.import_stl_90582', text='STL', icon_value=0, emboss=True, depress=False)
        op = row_5533A.operator('sna.import_fbx_644d9', text='FBX', icon_value=0, emboss=True, depress=False)
        op = row_5533A.operator('sna.import_obj_befeb', text='OBJ', icon_value=0, emboss=True, depress=False)
        op = row_5533A.operator('sna.import_dae_a17ee', text='DAE', icon_value=0, emboss=True, depress=False)
        op = box_CF752.operator('sna.clear_hierarchy_9ff17', text='Clear Hierarchy/Reset Scale', icon_value=0, emboss=True, depress=False)
        op = box_CF752.operator('sna.separate_parts_17bd5', text='Separate Parts', icon_value=0, emboss=True, depress=False)
        op = box_CF752.operator('sna.separate_by_material_8dbf4', text='Separate by Material', icon_value=0, emboss=True, depress=False)
        box_8C07A = layout.box()
        box_8C07A.alert = False
        box_8C07A.enabled = True
        box_8C07A.active = True
        box_8C07A.use_property_split = False
        box_8C07A.use_property_decorate = False
        box_8C07A.alignment = 'Expand'.upper()
        box_8C07A.scale_x = 1.0
        box_8C07A.scale_y = 1.0
        if not True: box_8C07A.operator_context = "EXEC_DEFAULT"
        op = box_8C07A.operator('sna.select_small_geometry_8dbe4', text='Select small parts', icon_value=0, emboss=True, depress=False)
        row_81640 = box_8C07A.row(heading='', align=False)
        row_81640.alert = False
        row_81640.enabled = True
        row_81640.active = True
        row_81640.use_property_split = False
        row_81640.use_property_decorate = False
        row_81640.scale_x = 1.0
        row_81640.scale_y = 1.0
        row_81640.alignment = 'Left'.upper()
        row_81640.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_81640.label(text='Objects under', icon_value=0)
        row_81640.prop(bpy.context.scene, 'sna_objectvolume', text='', icon_value=0, emboss=True)
        row_81640.label(text='cm3', icon_value=0)


class SNA_OT_Import_Stl_90582(bpy.types.Operator):
    bl_idname = "sna.import_stl_90582"
    bl_label = "Import STL"
    bl_description = "Import STL file"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.wm.stl_import('INVOKE_DEFAULT', up_axis='Z')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Import_Fbx_644D9(bpy.types.Operator):
    bl_idname = "sna.import_fbx_644d9"
    bl_label = "Import FBX"
    bl_description = "Import FBX file"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        prev_context = bpy.context.area.type
        bpy.context.area.type = 'VIEW_3D'
        bpy.ops.import_scene.fbx('INVOKE_DEFAULT', axis_up='Z')
        bpy.context.area.type = prev_context
        for i_C745B in range(len(bpy.context.selected_objects)):
            pass
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Import_Obj_Befeb(bpy.types.Operator):
    bl_idname = "sna.import_obj_befeb"
    bl_label = "Import OBJ"
    bl_description = "Import OBJ file"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.wm.obj_import('INVOKE_DEFAULT', up_axis='Z')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Import_Dae_A17Ee(bpy.types.Operator):
    bl_idname = "sna.import_dae_a17ee"
    bl_label = "Import DAE"
    bl_description = "Import DAE file"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.wm.collada_import('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Clear_Hierarchy_9Ff17(bpy.types.Operator):
    bl_idname = "sna.clear_hierarchy_9ff17"
    bl_label = "Clear Hierarchy"
    bl_description = "Removes all hierarchys and empty objects as well as resetting scale values. This ensures collision objects fit correctly to the scene objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        prev_context = bpy.context.area.type
        bpy.context.area.type = 'VIEW_3D'
        bpy.ops.object.parent_clear('INVOKE_DEFAULT', type='CLEAR_KEEP_TRANSFORM')
        bpy.context.area.type = prev_context
        prev_context = bpy.context.area.type
        bpy.context.area.type = 'VIEW_3D'
        bpy.ops.object.parent_clear('INVOKE_DEFAULT', type='CLEAR_KEEP_TRANSFORM')
        bpy.context.area.type = prev_context
        prev_context = bpy.context.area.type
        bpy.context.area.type = 'VIEW_3D'
        bpy.ops.object.parent_clear('INVOKE_DEFAULT', type='CLEAR_KEEP_TRANSFORM')
        bpy.context.area.type = prev_context
        prev_context = bpy.context.area.type
        bpy.context.area.type = 'VIEW_3D'
        bpy.ops.object.parent_clear('INVOKE_DEFAULT', type='CLEAR_KEEP_TRANSFORM')
        bpy.context.area.type = prev_context
        bpy.ops.object.transform_apply('INVOKE_DEFAULT', scale=True)
        for i_85522 in range(len(bpy.context.view_layer.objects.selected)):
            if (bpy.context.view_layer.objects.selected[i_85522].type == 'EMPTY'):
                bpy.context.view_layer.objects.active = bpy.context.view_layer.objects.selected[i_85522]
                bpy.data.objects.remove(object=bpy.context.view_layer.objects.active, )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Separate_Parts_17Bd5(bpy.types.Operator):
    bl_idname = "sna.separate_parts_17bd5"
    bl_label = "Separate Parts"
    bl_description = "Separates objects into individual parts when able. This allows the user to apply colliders to individual parts. Note that continuous geometry will not be separated however this can be done manually"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        exec("bpy.ops.mesh.select_all(action='SELECT')")
        bpy.ops.mesh.customdata_custom_splitnormals_clear('INVOKE_DEFAULT', )
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        bpy.ops.mesh.separate('INVOKE_DEFAULT', type='LOOSE')
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Separate_By_Material_8Dbf4(bpy.types.Operator):
    bl_idname = "sna.separate_by_material_8dbf4"
    bl_label = "Separate by material"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='EDIT')
        exec("bpy.ops.mesh.select_all(action='SELECT')")
        bpy.ops.mesh.separate('INVOKE_DEFAULT', type='MATERIAL')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Select_Small_Geometry_8Dbe4(bpy.types.Operator):
    bl_idname = "sna.select_small_geometry_8dbe4"
    bl_label = "Select small geometry"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.select_all('INVOKE_DEFAULT', action='DESELECT')
        for i_20E8A in range(len(bpy.data.objects)):
            if bpy.data.objects[i_20E8A].type == 'MESH':
                obj = bpy.data.objects[i_20E8A]
                volume = None
                import bmesh

                def get_mesh_volume(obj):
                    if obj.type != 'MESH':
                        print(f"{obj.name} is not a mesh object.")
                        return 0.0
                    # Create a BMesh from the object's evaluated mesh data
                    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    bm.transform(obj.matrix_world)  # Transform mesh to world space
                    volume_m3 = bm.calc_volume(signed=True)  # Calculate volume in cubic meters
                    bm.free()
                    # Convert volume from cubic meters to cubic centimeters
                    volume_cm3 = volume_m3 * 1_000_000  # 1 m³ = 1,000,000 cm³
                    return volume_cm3
                # Get the active object (make sure it's selected)
                #obj = bpy.context.active_object
                if obj:
                    volume = get_mesh_volume(obj)
                    print(f"Volume of '{obj.name}': {volume:.2f} cubic centimeters")
                else:
                    print("No active object selected.")
                if ((round(volume, abs(6)) < bpy.context.scene.sna_objectvolume) and (round(volume, abs(6)) > 0.0)):
                    bpy.data.objects[i_20E8A].select_set(state=True, )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_add_to_view3d_mt_add_CED9A(self, context):
    if not (False):
        layout = self.layout
        layout.popover('SNA_PT_NEW_PANEL_EFE02', text='Options', icon_value=0)


class SNA_OT_Set_Joint_Shape_Ded74(bpy.types.Operator):
    bl_idname = "sna.set_joint_shape_ded74"
    bl_label = "Set Joint Shape"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (bpy.context.scene.sna_jointtypes == 'Fixed'):
            bpy.context.scene.sna_joint_shape = 'CUBE'
        else:
            if ((bpy.context.scene.sna_jointtypes == 'Continuous') or (bpy.context.scene.sna_jointtypes == 'Revolute')):
                bpy.context.scene.sna_joint_shape = 'CIRCLE'
                print(bpy.context.scene.sna_joint_shape)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Link_Properties_28B11(bpy.types.Operator):
    bl_idname = "sna.link_properties_28b11"
    bl_label = "Link Properties"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        joint_name = bpy.context.scene.sna_jointtypes
        joint_name_lowered = None
        joint_name_lowered = joint_name.lower()
        bpy.context.view_layer.objects.active.name = bpy.context.scene.sna_jointname + '_joint_' + joint_name_lowered
        bpy.context.view_layer.objects.active.show_name = True
        bpy.context.view_layer.objects.active.show_in_front = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Create_Joint_D6784(bpy.types.Operator):
    bl_idname = "sna.create_joint_d6784"
    bl_label = "Create Joint"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    sna_joint_name: bpy.props.StringProperty(name='Joint Name', description='', default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (bpy.context.scene.sna_jointtypes == 'Fixed'):
            bpy.ops.sna.create_fixed_joint_61041('INVOKE_DEFAULT', )
        else:
            if (bpy.context.scene.sna_jointtypes == 'Revolute'):
                bpy.ops.sna.create_revolute_joint_941aa('INVOKE_DEFAULT', )
            else:
                if (bpy.context.scene.sna_jointtypes == 'Prismatic'):
                    bpy.ops.sna.create_prismatic_joint_a9ec2('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        row_8B366 = layout.row(heading='', align=False)
        row_8B366.alert = False
        row_8B366.enabled = True
        row_8B366.active = True
        row_8B366.use_property_split = False
        row_8B366.use_property_decorate = False
        row_8B366.scale_x = 1.0
        row_8B366.scale_y = 1.0
        row_8B366.alignment = 'Expand'.upper()
        row_8B366.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_8B366.prop(bpy.context.scene, 'sna_jointname', text='', icon_value=0, emboss=True)
        row_8B366.label(text='_joint', icon_value=0)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


class SNA_OT_Create_Fixed_Joint_61041(bpy.types.Operator):
    bl_idname = "sna.create_fixed_joint_61041"
    bl_label = "Create Fixed Joint"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='CUBE', radius=float(float(float(bpy.context.active_object.dimensions[0] + bpy.context.active_object.dimensions[1] + bpy.context.active_object.dimensions[2]) / 3.0) / 2.0), location=bpy.context.active_object.location, rotation=bpy.context.active_object.rotation_euler)
        bpy.ops.sna.link_properties_28b11('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_add_to_object_pt_context_object_449E2(self, context):
    if not (True):
        layout = self.layout
        row_DFDDB = layout.row(heading='', align=False)
        row_DFDDB.alert = False
        row_DFDDB.enabled = True
        row_DFDDB.active = True
        row_DFDDB.use_property_split = False
        row_DFDDB.use_property_decorate = False
        row_DFDDB.scale_x = 1.0
        row_DFDDB.scale_y = 1.0
        row_DFDDB.alignment = 'Expand'.upper()
        row_DFDDB.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_DFDDB.prop(bpy.context.view_layer.objects.active, 'location', text='Pose', icon_value=0, emboss=True)
        row_DFDDB.prop(bpy.context.view_layer.objects.active, 'rotation_euler', text='', icon_value=0, emboss=True)
        row_DD3A9 = layout.row(heading='', align=False)
        row_DD3A9.alert = (bpy.context.view_layer.objects.active.sna_parent == None)
        row_DD3A9.enabled = True
        row_DD3A9.active = True
        row_DD3A9.use_property_split = False
        row_DD3A9.use_property_decorate = False
        row_DD3A9.scale_x = 1.0
        row_DD3A9.scale_y = 1.0
        row_DD3A9.alignment = 'Expand'.upper()
        row_DD3A9.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_DD3A9.prop(bpy.context.view_layer.objects.active, 'sna_parent', text='Parent', icon_value=0, emboss=True)
        row_8C2A7 = layout.row(heading='', align=False)
        row_8C2A7.alert = (bpy.context.view_layer.objects.active.sna_child == None)
        row_8C2A7.enabled = True
        row_8C2A7.active = True
        row_8C2A7.use_property_split = False
        row_8C2A7.use_property_decorate = False
        row_8C2A7.scale_x = 1.0
        row_8C2A7.scale_y = 1.0
        row_8C2A7.alignment = 'Expand'.upper()
        row_8C2A7.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_8C2A7.prop(bpy.context.view_layer.objects.active, 'sna_child', text='Child', icon_value=0, emboss=True)
        row_42A80 = layout.row(heading='Limits', align=False)
        row_42A80.alert = False
        row_42A80.enabled = True
        row_42A80.active = True
        row_42A80.use_property_split = False
        row_42A80.use_property_decorate = False
        row_42A80.scale_x = 1.0
        row_42A80.scale_y = 1.0
        row_42A80.alignment = 'Expand'.upper()
        row_42A80.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_42A80.prop(bpy.context.view_layer.objects.active, 'sna_limits_lower', text='Lower', icon_value=0, emboss=True)
        row_42A80.prop(bpy.context.view_layer.objects.active, 'sna_limits_upper', text='Upper', icon_value=0, emboss=True)


class SNA_OT_Create_Prismatic_Joint_A9Ec2(bpy.types.Operator):
    bl_idname = "sna.create_prismatic_joint_a9ec2"
    bl_label = "Create Prismatic Joint"
    bl_description = "Create Prismatic Joint"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.sna_jointobj = bpy.context.active_object
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='CUBE', radius=float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 50.0), location=bpy.context.scene.sna_jointobj.location, rotation=bpy.context.scene.sna_jointobj.rotation_euler)
        bpy.context.scene.sna_mainjoint = bpy.context.view_layer.objects.active
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='PLAIN_AXES', radius=float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 5.0), location=bpy.context.scene.sna_jointobj.location, rotation=bpy.context.scene.sna_jointobj.rotation_euler)
        bpy.context.view_layer.objects.active.show_in_front = True
        bpy.context.view_layer.objects.active.hide_select = True
        joint['sna_jointmatrix'] = bpy.context.view_layer.objects.active.matrix_world
        bpy.context.view_layer.objects.active.parent = bpy.context.scene.sna_mainjoint
        bpy.context.view_layer.objects.active.matrix_world = joint['sna_jointmatrix']
        bpy.context.active_object.name = '0 reference'
        bpy.context.view_layer.objects.active.scale = (0.10000000149011612, 1.0, 0.10000000149011612)
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='CONE', radius=float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 50.0), location=bpy.context.scene.sna_jointobj.location, rotation=bpy.context.scene.sna_jointobj.rotation_euler)
        bpy.context.view_layer.objects.active.show_in_front = True
        bpy.context.view_layer.objects.active.hide_select = True
        joint['sna_jointmatrix'] = bpy.context.view_layer.objects.active.matrix_world
        bpy.context.view_layer.objects.active.parent = bpy.context.scene.sna_mainjoint
        bpy.context.view_layer.objects.active.matrix_world = joint['sna_jointmatrix']
        bpy.context.active_object.name = 'upper_limit_distance'
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='CONE', radius=float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 50.0), location=bpy.context.scene.sna_jointobj.location, rotation=bpy.context.scene.sna_jointobj.rotation_euler)
        bpy.context.view_layer.objects.active.show_in_front = True
        joint['sna_jointmatrix'] = bpy.context.view_layer.objects.active.matrix_world
        bpy.context.view_layer.objects.active.parent = bpy.context.scene.sna_mainjoint
        bpy.context.view_layer.objects.active.matrix_world = joint['sna_jointmatrix']
        bpy.context.active_object.name = 'lower_limit_distance'
        bpy.context.view_layer.objects.active.rotation_euler = (3.141590118408203, 0.0, 0.0)
        bpy.context.view_layer.objects.active.hide_select = True
        bpy.context.view_layer.objects.active.hide_select = True
        bpy.context.view_layer.objects.active = bpy.context.scene.sna_mainjoint
        bpy.context.scene.sna_mainjoint.select_set(state=True, )
        bpy.ops.sna.link_properties_28b11('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Scale_Joint_0971A(bpy.types.Operator):
    bl_idname = "sna.scale_joint_0971a"
    bl_label = "Scale Joint"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not True

    def execute(self, context):
        bpy.ops.transform.resize('INVOKE_DEFAULT', orient_type='LOCAL', orient_matrix_type='LOCAL', constraint_axis=(True, True, False))
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Create_Revolute_Joint_941Aa(bpy.types.Operator):
    bl_idname = "sna.create_revolute_joint_941aa"
    bl_label = "Create Revolute Joint"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.sna_jointobj = bpy.context.active_object
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='CIRCLE', radius=float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 3.0), location=bpy.context.scene.sna_jointobj.location, rotation=bpy.context.scene.sna_jointobj.rotation_euler)
        bpy.context.scene.sna_mainjoint = bpy.context.view_layer.objects.active
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='SINGLE_ARROW', radius=float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 3.0), location=bpy.context.scene.sna_jointobj.location, rotation=bpy.context.scene.sna_jointobj.rotation_euler)
        bpy.context.view_layer.objects.active.show_in_front = True
        bpy.context.view_layer.objects.active.hide_select = True
        joint['sna_jointmatrix'] = bpy.context.view_layer.objects.active.matrix_world
        bpy.context.view_layer.objects.active.parent = bpy.context.scene.sna_mainjoint
        bpy.context.view_layer.objects.active.matrix_world = joint['sna_jointmatrix']
        bpy.context.active_object.name = 'upper_limit'
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='SINGLE_ARROW', radius=float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 3.0), location=bpy.context.scene.sna_jointobj.location, rotation=bpy.context.scene.sna_jointobj.rotation_euler)
        bpy.context.view_layer.objects.active.show_in_front = True
        bpy.context.view_layer.objects.active.hide_select = True
        joint['sna_jointmatrix'] = bpy.context.view_layer.objects.active.matrix_world
        bpy.context.view_layer.objects.active.parent = bpy.context.scene.sna_mainjoint
        bpy.context.view_layer.objects.active.matrix_world = joint['sna_jointmatrix']
        bpy.context.active_object.name = 'lower_limit'
        bpy.ops.object.empty_add('INVOKE_DEFAULT', type='CIRCLE', radius=float(float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 3.0) / 15.0), location=bpy.context.scene.sna_jointobj.location, rotation=bpy.context.scene.sna_jointobj.rotation_euler, scale=(1.0, 1.0, 0.30000001192092896))
        bpy.context.view_layer.objects.active.show_in_front = True
        joint['sna_jointmatrix'] = bpy.context.view_layer.objects.active.matrix_world
        bpy.context.view_layer.objects.active.parent = bpy.context.scene.sna_mainjoint
        bpy.context.view_layer.objects.active.matrix_world = joint['sna_jointmatrix']
        bpy.context.active_object.name = '0 reference'
        bpy.ops.transform.transform(mode='TRANSLATION', value=(0.0, 0.0, float(float(float(bpy.context.scene.sna_jointobj.dimensions[0] + bpy.context.scene.sna_jointobj.dimensions[1] + bpy.context.scene.sna_jointobj.dimensions[2]) / 3.0) * 0.8999999761581421), 0.0), orient_type='LOCAL', constraint_axis=(False, False, True))
        bpy.context.view_layer.objects.active.hide_select = True
        bpy.context.view_layer.objects.active = bpy.context.scene.sna_mainjoint
        bpy.context.scene.sna_mainjoint.select_set(state=True, )
        bpy.ops.sna.link_properties_28b11('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_jointstab_F6DFE(layout_function, ):
    box_F5BDB = layout_function.box()
    box_F5BDB.alert = False
    box_F5BDB.enabled = True
    box_F5BDB.active = True
    box_F5BDB.use_property_split = False
    box_F5BDB.use_property_decorate = False
    box_F5BDB.alignment = 'Expand'.upper()
    box_F5BDB.scale_x = 1.0
    box_F5BDB.scale_y = 1.0
    if not True: box_F5BDB.operator_context = "EXEC_DEFAULT"
    box_F5BDB.prop(bpy.context.scene, 'sna_jointvisibility', text='Show/Hide Joints', icon_value=0, emboss=True)
    row_C224C = box_F5BDB.row(heading='', align=False)
    row_C224C.alert = False
    row_C224C.enabled = True
    row_C224C.active = True
    row_C224C.use_property_split = False
    row_C224C.use_property_decorate = False
    row_C224C.scale_x = 0.8799999952316284
    row_C224C.scale_y = 1.0
    row_C224C.alignment = 'Left'.upper()
    row_C224C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
    split_1F3BD = row_C224C.split(factor=0.5666666626930237, align=True)
    split_1F3BD.alert = False
    split_1F3BD.enabled = True
    split_1F3BD.active = True
    split_1F3BD.use_property_split = False
    split_1F3BD.use_property_decorate = False
    split_1F3BD.scale_x = 1.0
    split_1F3BD.scale_y = 1.0
    split_1F3BD.alignment = 'Left'.upper()
    if not True: split_1F3BD.operator_context = "EXEC_DEFAULT"
    split_1F3BD.label(text='Joint Color:', icon_value=0)
    split_1F3BD.prop(bpy.context.preferences.themes['Default'].view_3d, 'empty', text='', icon_value=0, emboss=True)
    split_BF075 = box_F5BDB.split(factor=0.30444443225860596, align=False)
    split_BF075.alert = False
    split_BF075.enabled = True
    split_BF075.active = True
    split_BF075.use_property_split = False
    split_BF075.use_property_decorate = False
    split_BF075.scale_x = 1.0
    split_BF075.scale_y = 1.0
    split_BF075.alignment = 'Expand'.upper()
    if not True: split_BF075.operator_context = "EXEC_DEFAULT"
    split_BF075.label(text='Joint Type:', icon_value=0)
    split_BF075.prop(bpy.context.scene, 'sna_jointtypes', text='', icon_value=0, emboss=True)
    op = box_F5BDB.operator('sna.create_joint_d6784', text='Create Joint', icon_value=0, emboss=True, depress=False)
    op.sna_joint_name = ''


class SNA_OT_Createlink_Af238(bpy.types.Operator):
    bl_idname = "sna.createlink_af238"
    bl_label = "CreateLink"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        collection_E2A59 = bpy.data.collections.new(name=bpy.context.scene.sna_linkname + '_link', )
        bpy.context.scene.collection.children.link(child=collection_E2A59, )
        collection_FC8D6 = bpy.data.collections.new(name=bpy.context.scene.sna_linkname + '_visual', )
        bpy.data.collections[bpy.context.scene.sna_linkname + '_link'].children.link(child=collection_FC8D6, )
        collection_D2615 = bpy.data.collections.new(name=bpy.context.scene.sna_linkname + '_colliders', )
        bpy.data.collections[bpy.context.scene.sna_linkname + '_link'].children.link(child=collection_D2615, )
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        row_FB32A = layout.row(heading='', align=False)
        row_FB32A.alert = False
        row_FB32A.enabled = True
        row_FB32A.active = True
        row_FB32A.use_property_split = False
        row_FB32A.use_property_decorate = False
        row_FB32A.scale_x = 1.0
        row_FB32A.scale_y = 1.0
        row_FB32A.alignment = 'Expand'.upper()
        row_FB32A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_FB32A.prop(bpy.context.scene, 'sna_linkname', text='', icon_value=0, emboss=True)
        row_FB32A.label(text='_link', icon_value=0)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


class SNA_OT_Clone_Link_11408(bpy.types.Operator):
    bl_idname = "sna.clone_link_11408"
    bl_label = "Clone Link"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.view3d.snap_cursor_to_center('INVOKE_DEFAULT', )
        if '_link' in bpy.context.collection.name:
            bpy.ops.object.collection_instance_add('INVOKE_DEFAULT', name=bpy.context.collection.name, collection=bpy.context.collection.name, location=(0.0, 0.0, 0.0))
            original_string = bpy.context.active_object.name
            new_string = None

            def insert_clone(original):
                index = original.rfind("_")  # Find the last underscore
                return f"{original[:index]}_clone{original[index:]}"  # Insert 'clone' before the last part
            # Example usage
            #original_string = "link6_link"
            new_string = insert_clone(original_string)
            #print (new_string)
            bpy.context.active_object.name = new_string
        else:
            ShowMessageBoxer('Warning',
                                                              'ERROR',
                                                              'Select a link collection')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Add_Include_D77Ba(bpy.types.Operator):
    bl_idname = "sna.add_include_d77ba"
    bl_label = "Add include"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        scene_index = bpy.context.scene.sna_includesceneindex
        include_scene = None
        include_scene = bpy.data.scenes[scene_index]
        source_scene_name = include_scene.name
        # Names of the target scene and the current scene
        target_scene_name = "Other"
        current_scene = bpy.context.scene
        current_scene_name = current_scene.name
        # Get the target scene
        target_scene = bpy.data.scenes.get(target_scene_name)
        if target_scene:
            # Define the new collection name dynamically based on the target scene name
            new_collection_name = f"{target_scene_name}_Instance"
            instance_collection_name = f"{new_collection_name}_include"
            # Create or get the dynamically named 'Instance' collection in the target scene
            instance_collection = bpy.data.collections.get(new_collection_name)
            if not instance_collection:
                instance_collection = bpy.data.collections.new(new_collection_name)
                target_scene.collection.children.link(instance_collection)
            # Move all top-level collections in the target scene to 'Instance'
            for collection in target_scene.collection.children:
                # Ensure we are using collection names for comparison
                if collection.name != new_collection_name and collection.name not in instance_collection.children.keys():
                    # Link the collection to 'Instance'
                    instance_collection.children.link(collection)
                    # Unlink it from the root collection of the target scene
                    target_scene.collection.children.unlink(collection)
            print(f"All collections in '{target_scene_name}' are now organized under the '{new_collection_name}' collection.")
            # Create a collection instance in the current scene if it is different from the target scene
            if current_scene_name != target_scene_name:
                # Check if an instance of 'Other_Instance_include' already exists in the current scene
                existing_instance = False
                for obj in current_scene.objects:
                    if obj.instance_collection and obj.instance_collection.name == new_collection_name:
                        existing_instance = True
                        break
                if not existing_instance:
                    # Add a collection instance of 'Other_Instance' (without '_include') to the current scene
                    bpy.ops.object.collection_instance_add(collection=new_collection_name, location=(0, 0, 0))
                    # Get the newly added instance object
                    instance_object = bpy.context.view_layer.objects.active
                    # Rename the instance object to include "_include"
                    instance_object.name = instance_collection_name
                    # Unlink the instance from any collections it may have been added to
                    for col in instance_object.users_collection:
                        col.objects.unlink(instance_object)
                    # Link the instance directly to the root collection of the current scene
                    current_scene.collection.objects.link(instance_object)
                    print(f"Created a collection instance of '{instance_collection_name}' in the '{current_scene_name}' scene's root collection.")
                else:
                    print(f"An instance of '{new_collection_name}' already exists in the '{current_scene_name}' scene.")
            else:
                print("Warning: Models cannot contain an instance of themselves.")
        else:
            print(f"The scene '{target_scene_name}' does not exist.")
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        coll_id = display_collection_id('E2509', locals())
        layout.template_list('SNA_UL_display_collection_list001_E2509', coll_id, bpy.data, 'scenes', bpy.context.scene, 'sna_includesceneindex', rows=len(bpy.data.scenes))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


class SNA_OT_Create_Model_63761(bpy.types.Operator):
    bl_idname = "sna.create_model_63761"
    bl_label = "Create Model"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        scene_07827 = bpy.data.scenes.new(name=bpy.context.scene.sna_modelname, )
        bpy.context.window.scene = scene_07827
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.context.scene, 'sna_modelname', text='Model Name', icon_value=0, emboss=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


def sna_notactivescene_4FCAA(Input):
    return (Input != bpy.context.scene)


class SNA_OT_Remove_Model_08467(bpy.types.Operator):
    bl_idname = "sna.remove_model_08467"
    bl_label = "Remove Model"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.scenes.remove(scene=bpy.context.scene, do_unlink=True, )
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


class SNA_OT_Plane_Z_01890(bpy.types.Operator):
    bl_idname = "sna.plane_z_01890"
    bl_label = "Plane Z"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        cylinder['sna_cylusercollection'] = bpy.context.view_layer.objects.active.users_collection
        cylinder['sna_cylsource'] = bpy.context.view_layer.objects.active
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        bpy.ops.mesh.primitive_plane_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler)
        bpy.context.view_layer.objects.active.dimensions = (bpy.context.scene.sna_active_visual_object.dimensions[0], bpy.context.scene.sna_active_visual_object.dimensions[1], 0.0)
        bpy.context.active_object.name = 'collider_plane'
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


_182F2_running = False
class SNA_OT_Plane_182F2(bpy.types.Operator):
    bl_idname = "sna.plane_182f2"
    bl_label = "Plane"
    bl_description = "Creates a cylinder collider that fits selected cylindrical shaped objects. Choose your alignment axis in the subsequent menu"
    bl_options = {"REGISTER", "UNDO"}
    cursor = "CROSSHAIR"
    _handle = None
    _event = {}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        if not True or context.area.spaces[0].bl_rna.identifier == 'SpaceView3D':
            return not False
        return False

    def save_event(self, event):
        event_options = ["type", "value", "alt", "shift", "ctrl", "oskey", "mouse_region_x", "mouse_region_y", "mouse_x", "mouse_y", "pressure", "tilt"]
        if bpy.app.version >= (3, 2, 1):
            event_options += ["type_prev", "value_prev"]
        for option in event_options: self._event[option] = getattr(event, option)

    def draw_callback_px(self, context):
        event = self._event
        if event.keys():
            event = dotdict(event)
            try:
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_1A834, y_1A834 = (100.0, 600.0)
                    blf.position(font_id, x_1A834, y_1A834, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[X] Plane along X axis')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_4B1BD, y_4B1BD = tuple(mathutils.Vector((100.0, 600.0)) - mathutils.Vector((0.0, 80.0)))
                    blf.position(font_id, x_4B1BD, y_4B1BD, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Y] Plane along Y axis')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_8CCFE, y_8CCFE = tuple(mathutils.Vector(tuple(mathutils.Vector((100.0, 600.0)) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))
                    blf.position(font_id, x_8CCFE, y_8CCFE, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Z] Plane along Z axis')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_9621E, y_9621E = tuple(mathutils.Vector(tuple(mathutils.Vector(tuple(mathutils.Vector((100.0, 600.0)) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))
                    blf.position(font_id, x_9621E, y_9621E, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[ESC] Cancel')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
                font_id = 0
                if r'' and os.path.exists(r''):
                    font_id = blf.load(r'')
                if font_id == -1:
                    print("Couldn't load font!")
                else:
                    x_A7FE9, y_A7FE9 = tuple(mathutils.Vector(tuple(mathutils.Vector(tuple(mathutils.Vector(tuple(mathutils.Vector((100.0, 600.0)) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))) - mathutils.Vector((0.0, 80.0)))
                    blf.position(font_id, x_A7FE9, y_A7FE9, 0)
                    if bpy.app.version >= (3, 4, 0):
                        blf.size(font_id, 50.0)
                    else:
                        blf.size(font_id, 50.0, 72)
                    clr = (1.0, 1.0, 1.0, 1.0)
                    blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
                    if 5000:
                        blf.enable(font_id, blf.WORD_WRAP)
                        blf.word_wrap(font_id, 5000)
                    if 0.0:
                        blf.enable(font_id, blf.ROTATION)
                        blf.rotation(font_id, 0.0)
                    blf.enable(font_id, blf.WORD_WRAP)
                    blf.draw(font_id, '[Space] Confirm')
                    blf.disable(font_id, blf.ROTATION)
                    blf.disable(font_id, blf.WORD_WRAP)
            except Exception as error:
                print(error)

    def execute(self, context):
        global _182F2_running
        _182F2_running = False
        context.window.cursor_set("DEFAULT")
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        if (collider['sna_joinedobj'] != None):
            bpy.data.objects.remove(object=collider['sna_joinedobj'], )
            collider['sna_joinedobj'] = None
        for area in context.screen.areas:
            area.tag_redraw()
        return {"FINISHED"}

    def modal(self, context, event):
        global _182F2_running
        if not context.area or not _182F2_running:
            self.execute(context)
            return {'CANCELLED'}
        self.save_event(event)
        context.area.tag_redraw()
        context.window.cursor_set('CROSSHAIR')
        try:
            if (event.type == 'X' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                if (bpy.context.view_layer.objects.active.name == cylinder['sna_actobjcylgen']):
                    bpy.ops.sna.plane_x_3923a('INVOKE_DEFAULT', )
                else:
                    bpy.ops.object.delete('INVOKE_DEFAULT', confirm=False)
                    bpy.data.objects[cylinder['sna_actobjcylgen']].select_set(state=True, )
                    bpy.context.view_layer.objects.active = bpy.context.view_layer.objects.selected[cylinder['sna_actobjcylgen']]
                    bpy.ops.sna.plane_x_3923a('INVOKE_DEFAULT', )
            else:
                if (event.type == 'Y' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                    if (bpy.context.view_layer.objects.active.name == cylinder['sna_actobjcylgen']):
                        bpy.ops.sna.plane_y_e935a('INVOKE_DEFAULT', )
                    else:
                        bpy.ops.object.delete('INVOKE_DEFAULT', confirm=False)
                        bpy.data.objects[cylinder['sna_actobjcylgen']].select_set(state=True, )
                        bpy.context.view_layer.objects.active = bpy.context.view_layer.objects.selected[cylinder['sna_actobjcylgen']]
                        bpy.ops.sna.plane_y_e935a('INVOKE_DEFAULT', )
                if (event.type == 'Z' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                    if (bpy.context.view_layer.objects.active.name == cylinder['sna_actobjcylgen']):
                        bpy.ops.sna.plane_z_01890('INVOKE_DEFAULT', )
                    else:
                        bpy.ops.object.delete('INVOKE_DEFAULT', confirm=False)
                        bpy.data.objects[cylinder['sna_actobjcylgen']].select_set(state=True, )
                        bpy.context.view_layer.objects.active = bpy.context.view_layer.objects.selected[cylinder['sna_actobjcylgen']]
                        bpy.ops.sna.plane_z_01890('INVOKE_DEFAULT', )
                if (event.type == 'ESC' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                    if (bpy.context.view_layer.objects.active.name != cylinder['sna_actobjcylgen']):
                        bpy.ops.object.delete('INVOKE_DEFAULT', confirm=False)
                    else:
                        if event.type in ['RIGHTMOUSE', 'ESC']:
                            self.execute(context)
                            return {'CANCELLED'}
                        self.execute(context)
                        return {"FINISHED"}
                if (event.type == 'SPACE' and event.value == 'PRESS' and event.alt == False and event.shift == False and event.ctrl == False):
                    if event.type in ['RIGHTMOUSE', 'ESC']:
                        self.execute(context)
                        return {'CANCELLED'}
                    self.execute(context)
                    return {"FINISHED"}
        except Exception as error:
            print(error)
        if event.type in ['RIGHTMOUSE', 'ESC']:
            self.execute(context)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        global _182F2_running
        if _182F2_running:
            _182F2_running = False
            return {'FINISHED'}
        else:
            self.save_event(event)
            self.start_pos = (event.mouse_x, event.mouse_y)
            bpy.ops.sna.collider_creation_setiup_8e177('INVOKE_DEFAULT', )
            collider['sna_joinedobj'] = None
            cylinder['sna_actobjcylgen'] = bpy.context.view_layer.objects.active.name
            if (len(bpy.context.selected_objects) > 1):
                exec('bpy.ops.object.duplicate()')
                exec('bpy.ops.object.join()')
                collider['sna_joinedobj'] = bpy.context.view_layer.objects.active
                cylinder['sna_actobjcylgen'] = bpy.context.view_layer.objects.active.name
            args = (context,)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            _182F2_running = True
            return {'RUNNING_MODAL'}


class SNA_OT_Plane_X_3923A(bpy.types.Operator):
    bl_idname = "sna.plane_x_3923a"
    bl_label = "Plane X"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        cylinder['sna_cylusercollection'] = bpy.context.view_layer.objects.active.users_collection
        cylinder['sna_cylsource'] = bpy.context.view_layer.objects.active
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        bpy.ops.mesh.primitive_plane_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler)
        axis = 'X'
        from math import radians
        # Rotate 90 degrees around the local Y-axis
        bpy.context.active_object.rotation_euler.rotate_axis(axis, radians(90))
        bpy.context.view_layer.objects.active.dimensions = (bpy.context.scene.sna_active_visual_object.dimensions[0], bpy.context.scene.sna_active_visual_object.dimensions[2], 0.0)
        bpy.context.active_object.name = 'collider_plane'
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Plane_Y_E935A(bpy.types.Operator):
    bl_idname = "sna.plane_y_e935a"
    bl_label = "Plane Y"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        cylinder['sna_cylusercollection'] = bpy.context.view_layer.objects.active.users_collection
        cylinder['sna_cylsource'] = bpy.context.view_layer.objects.active
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
        bpy.ops.mesh.primitive_plane_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, rotation=bpy.context.view_layer.objects.active.rotation_euler)
        axis = 'Y'
        from math import radians
        # Rotate 90 degrees around the local Y-axis
        bpy.context.active_object.rotation_euler.rotate_axis(axis, radians(90))
        bpy.context.view_layer.objects.active.dimensions = (bpy.context.scene.sna_active_visual_object.dimensions[2], bpy.context.scene.sna_active_visual_object.dimensions[1], 0.0)
        bpy.context.active_object.name = 'collider_plane'
        bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
        bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
        bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_VISUAL_PROPERTIES_71786(bpy.types.Panel):
    bl_label = 'Visual properties'
    bl_idname = 'SNA_PT_VISUAL_PROPERTIES_71786'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'SDF_Gen'
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (True)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        if '_visual' in bpy.context.view_layer.objects.active.name:
            layout.prop(bpy.data.objects['collider_cylinder.001'], 'name', text='', icon_value=0, emboss=True)


class SNA_PT_VISIBILITY_0147F(bpy.types.Panel):
    bl_label = 'Visibility'
    bl_idname = 'SNA_PT_VISIBILITY_0147F'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'SDF Gen'
    bl_order = 1
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (True)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_67B77 = layout.box()
        box_67B77.alert = False
        box_67B77.enabled = True
        box_67B77.active = True
        box_67B77.use_property_split = False
        box_67B77.use_property_decorate = False
        box_67B77.alignment = 'Expand'.upper()
        box_67B77.scale_x = 1.0
        box_67B77.scale_y = 1.0
        if not True: box_67B77.operator_context = "EXEC_DEFAULT"
        box_67B77.prop(bpy.context.scene, 'sna_collidervisibiity', text='Show/Hide Colliders', icon_value=0, emboss=True)
        box_67B77.prop(bpy.context.scene, 'sna_jointvisibility', text='Show/Hide Joints', icon_value=0, emboss=True)
        row_F84A5 = box_67B77.row(heading='', align=False)
        row_F84A5.alert = False
        row_F84A5.enabled = True
        row_F84A5.active = True
        row_F84A5.use_property_split = False
        row_F84A5.use_property_decorate = False
        row_F84A5.scale_x = 0.8799999952316284
        row_F84A5.scale_y = 1.0
        row_F84A5.alignment = 'Left'.upper()
        row_F84A5.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        split_697A8 = row_F84A5.split(factor=0.5666666626930237, align=True)
        split_697A8.alert = False
        split_697A8.enabled = True
        split_697A8.active = True
        split_697A8.use_property_split = False
        split_697A8.use_property_decorate = False
        split_697A8.scale_x = 1.0
        split_697A8.scale_y = 1.0
        split_697A8.alignment = 'Left'.upper()
        if not True: split_697A8.operator_context = "EXEC_DEFAULT"
        split_697A8.label(text='Joint Color:', icon_value=0)
        split_697A8.prop(bpy.context.preferences.themes['Default'].view_3d, 'empty', text='', icon_value=0, emboss=True)


class SNA_PT_EXPORT_0BD82(bpy.types.Panel):
    bl_label = 'Export'
    bl_idname = 'SNA_PT_EXPORT_0BD82'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'SDF Gen'
    bl_order = 4
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_2FC44 = layout.row(heading='Mesh File Type:', align=False)
        row_2FC44.alert = False
        row_2FC44.enabled = True
        row_2FC44.active = True
        row_2FC44.use_property_split = False
        row_2FC44.use_property_decorate = False
        row_2FC44.scale_x = 1.0
        row_2FC44.scale_y = 1.0
        row_2FC44.alignment = 'Left'.upper()
        row_2FC44.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_2FC44.prop(bpy.context.scene, 'sna_exportfiletype', text='', icon_value=0, emboss=True, expand=False)
        split_DC99C = layout.split(factor=0.3933333158493042, align=False)
        split_DC99C.alert = False
        split_DC99C.enabled = True
        split_DC99C.active = True
        split_DC99C.use_property_split = False
        split_DC99C.use_property_decorate = False
        split_DC99C.scale_x = 1.0
        split_DC99C.scale_y = 1.0
        split_DC99C.alignment = 'Expand'.upper()
        if not True: split_DC99C.operator_context = "EXEC_DEFAULT"
        split_DC99C.label(text='Mesh File Path:', icon_value=0)
        split_DC99C.prop(bpy.context.scene, 'sna_sdf_export_path', text='', icon_value=0, emboss=True)
        split_56429 = layout.split(factor=0.30888888239860535, align=False)
        split_56429.alert = False
        split_56429.enabled = True
        split_56429.active = True
        split_56429.use_property_split = False
        split_56429.use_property_decorate = False
        split_56429.scale_x = 1.0
        split_56429.scale_y = 1.0
        split_56429.alignment = 'Expand'.upper()
        if not True: split_56429.operator_context = "EXEC_DEFAULT"
        split_56429.label(text='Export Path:', icon_value=0)
        split_56429.prop(bpy.context.scene, 'sna_filepath', text='', icon_value=0, emboss=True)
        op = layout.operator('sna.export_all_b6b8d', text='Export', icon_value=0, emboss=True, depress=False)
        if (bpy.context.scene.sna_sdf_file_paths == 'Custom'):
            pass


class SNA_PT_CREATE_88892(bpy.types.Panel):
    bl_label = 'Create'
    bl_idname = 'SNA_PT_CREATE_88892'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'SDF Gen'
    bl_order = 1
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.context.scene, 'sna_tabscreate', text=bpy.context.scene.sna_tabscreate, icon_value=0, emboss=True, expand=True)
        if bpy.context.scene.sna_tabscreate == "Hierarchy":
            layout_function = layout
            sna_hierarchytab_C3C26(layout_function, )
        elif bpy.context.scene.sna_tabscreate == "Colliders":
            layout_function = layout
            sna_colliderstab_0B1AA(layout_function, )
        elif bpy.context.scene.sna_tabscreate == "Joints":
            layout_function = layout
            sna_jointstab_F6DFE(layout_function, )
        else:
            pass


class SNA_OT_Sphere_F5Cd9(bpy.types.Operator):
    bl_idname = "sna.sphere_f5cd9"
    bl_label = "Sphere"
    bl_description = "Creates a sphere collider that fits the selected object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.object.mode_set('INVOKE_DEFAULT', mode='OBJECT')
        bpy.ops.sna.set_active_object_40bc9('INVOKE_DEFAULT', )
        if bpy.context.scene.sna_perobj:
            bpy.ops.sna.sphereop_6d8a0('INVOKE_DEFAULT', )
        else:
            exec('bpy.ops.object.duplicate()')
            exec('bpy.ops.object.join()')
            collider['sna_joinedobj'] = bpy.context.view_layer.objects.active
            bpy.ops.sna.sphereop_6d8a0('INVOKE_DEFAULT', )
            bpy.context.active_object.name = 'collider_sphere'
            bpy.data.objects.remove(object=collider['sna_joinedobj'], )
            bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
            bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Sphereop_6D8A0(bpy.types.Operator):
    bl_idname = "sna.sphereop_6d8a0"
    bl_label = "SphereOp"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.collider_creation_setiup_8e177('INVOKE_DEFAULT', )
        collider['sna_selection'] = bpy.context.selected_objects
        for i_6F8AA in range(len(collider['sna_selection'])-1,-1,-1):
            bpy.context.view_layer.objects.active = collider['sna_selection'][i_6F8AA]
            bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
            bpy.ops.object.origin_set('INVOKE_DEFAULT', type='ORIGIN_GEOMETRY', center='BOUNDS')
            bpy.ops.mesh.primitive_uv_sphere_add('INVOKE_DEFAULT', location=bpy.context.view_layer.objects.active.location, scale=tuple(mathutils.Vector(bpy.context.view_layer.objects.active.dimensions) / 2.0))
            bpy.ops.sna.move_to_collision_collection_b7e42('INVOKE_DEFAULT', )
            bpy.context.active_object.name = 'collider_sphere'
            bpy.ops.sna.set_collider_material_33bff('INVOKE_DEFAULT', )
            bpy.ops.sna.add_margin_modifier_43181('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_PROPERTIES_7CC42(bpy.types.Panel):
    bl_label = 'Properties'
    bl_idname = 'SNA_PT_PROPERTIES_7CC42'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'SDF Gen'
    bl_order = 1
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        if (len(bpy.context.selected_objects) != 0):
            if '_joint' in bpy.context.selected_objects[0].name:
                box_89823 = layout.box()
                box_89823.alert = False
                box_89823.enabled = True
                box_89823.active = True
                box_89823.use_property_split = False
                box_89823.use_property_decorate = False
                box_89823.alignment = 'Expand'.upper()
                box_89823.scale_x = 1.0
                box_89823.scale_y = 1.0
                if not True: box_89823.operator_context = "EXEC_DEFAULT"
                box_80153 = box_89823.box()
                box_80153.alert = False
                box_80153.enabled = True
                box_80153.active = True
                box_80153.use_property_split = False
                box_80153.use_property_decorate = False
                box_80153.alignment = 'Expand'.upper()
                box_80153.scale_x = 1.0
                box_80153.scale_y = 1.0
                if not True: box_80153.operator_context = "EXEC_DEFAULT"
                box_80153.prop(bpy.context.view_layer.objects.active, 'sna_parent', text='Parent', icon_value=0, emboss=True)
                box_80153.prop(bpy.context.view_layer.objects.active, 'sna_child', text='Child', icon_value=0, emboss=True)
                if (len(bpy.context.selected_objects) == 1):
                    if '_joint_revolute' in bpy.context.selected_objects[0].name:
                        box_7897E = box_89823.box()
                        box_7897E.alert = False
                        box_7897E.enabled = True
                        box_7897E.active = True
                        box_7897E.use_property_split = False
                        box_7897E.use_property_decorate = False
                        box_7897E.alignment = 'Expand'.upper()
                        box_7897E.scale_x = 1.0
                        box_7897E.scale_y = 1.0
                        if not True: box_7897E.operator_context = "EXEC_DEFAULT"
                        box_7897E.label(text='Revolute Properties', icon_value=0)
                        box_7897E.prop(bpy.context.view_layer.objects.active, 'sna_iscontinuous', text='Continuous', icon_value=0, emboss=True)
                        if (not bpy.context.view_layer.objects.active.sna_iscontinuous):
                            box_7897E.prop(bpy.context.view_layer.objects.active, 'sna_limits_lower', text='Lower Limit', icon_value=0, emboss=True)
                        if (not bpy.context.view_layer.objects.active.sna_iscontinuous):
                            box_7897E.prop(bpy.context.view_layer.objects.active, 'sna_limits_upper', text='Upper Limit', icon_value=0, emboss=True)
                if (len(bpy.context.selected_objects) == 1):
                    if '_joint_prismatic' in bpy.context.selected_objects[0].name:
                        box_BD7C7 = box_89823.box()
                        box_BD7C7.alert = False
                        box_BD7C7.enabled = True
                        box_BD7C7.active = True
                        box_BD7C7.use_property_split = False
                        box_BD7C7.use_property_decorate = False
                        box_BD7C7.alignment = 'Expand'.upper()
                        box_BD7C7.scale_x = 1.0
                        box_BD7C7.scale_y = 1.0
                        if not True: box_BD7C7.operator_context = "EXEC_DEFAULT"
                        box_BD7C7.label(text='Prismatic Properties', icon_value=0)
                        box_BD7C7.prop(bpy.context.view_layer.objects.active, 'sna_limits_lower_distance', text='Lower Limit', icon_value=0, emboss=True)
                        box_BD7C7.prop(bpy.context.view_layer.objects.active, 'sna_limits_upper_distance', text='Upper Limit', icon_value=0, emboss=True)
        if ((len(bpy.context.selected_objects) != 0) and bpy.context.selected_objects[0].type == 'MESH' and (bpy.context.view_layer.objects.active.users_collection != None) and '_visual' in str(bpy.context.view_layer.objects.active.users_collection)):
            box_066B3 = layout.box()
            box_066B3.alert = False
            box_066B3.enabled = True
            box_066B3.active = True
            box_066B3.use_property_split = False
            box_066B3.use_property_decorate = False
            box_066B3.alignment = 'Expand'.upper()
            box_066B3.scale_x = 1.0
            box_066B3.scale_y = 1.0
            if not True: box_066B3.operator_context = "EXEC_DEFAULT"
            col_34C9A = box_066B3.column(heading='', align=False)
            col_34C9A.alert = False
            col_34C9A.enabled = True
            col_34C9A.active = True
            col_34C9A.use_property_split = False
            col_34C9A.use_property_decorate = False
            col_34C9A.scale_x = 1.0
            col_34C9A.scale_y = 1.0
            col_34C9A.alignment = 'Expand'.upper()
            col_34C9A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
            col_34C9A.label(text='Physics Material', icon_value=0)
            if bpy.context.view_layer.objects.active.sna_custommassbool:
                box_62908 = col_34C9A.box()
                box_62908.alert = False
                box_62908.enabled = True
                box_62908.active = True
                box_62908.use_property_split = False
                box_62908.use_property_decorate = False
                box_62908.alignment = 'Expand'.upper()
                box_62908.scale_x = 1.0
                box_62908.scale_y = 1.0
                if not True: box_62908.operator_context = "EXEC_DEFAULT"
                box_62908.prop(bpy.context.view_layer.objects.active, 'sna_custommass', text='Custom Mass', icon_value=0, emboss=True)
            else:
                box_68866 = col_34C9A.box()
                box_68866.alert = False
                box_68866.enabled = True
                box_68866.active = True
                box_68866.use_property_split = False
                box_68866.use_property_decorate = False
                box_68866.alignment = 'Expand'.upper()
                box_68866.scale_x = 1.0
                box_68866.scale_y = 1.0
                if not True: box_68866.operator_context = "EXEC_DEFAULT"
                box_68866.prop(bpy.context.view_layer.objects.active, 'sna_materialsmass', text='', icon_value=0, emboss=True)
                row_9A0A9 = box_68866.row(heading='', align=False)
                row_9A0A9.alert = False
                row_9A0A9.enabled = False
                row_9A0A9.active = True
                row_9A0A9.use_property_split = False
                row_9A0A9.use_property_decorate = False
                row_9A0A9.scale_x = 0.8999996185302734
                row_9A0A9.scale_y = 1.0
                row_9A0A9.alignment = 'Left'.upper()
                row_9A0A9.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
            col_34C9A.prop(bpy.context.view_layer.objects.active, 'sna_custommassbool', text='Custom Density', icon_value=0, emboss=True)
            box_706A0 = col_34C9A.box()
            box_706A0.alert = False
            box_706A0.enabled = True
            box_706A0.active = True
            box_706A0.use_property_split = False
            box_706A0.use_property_decorate = False
            box_706A0.alignment = 'Expand'.upper()
            box_706A0.scale_x = 1.0
            box_706A0.scale_y = 1.0
            if not True: box_706A0.operator_context = "EXEC_DEFAULT"
            box_706A0.label(text='Optimization', icon_value=0)
            op = box_706A0.operator('sna.decimate_5ed31', text='Decimate', icon_value=0, emboss=True, depress=False)
            if (len(list(bpy.context.view_layer.objects.active.modifiers)) > 0):
                for i_6D766 in range(len(bpy.context.view_layer.objects.active.modifiers)):
                    if 'Decimate' in str(bpy.context.view_layer.objects.active.modifiers[i_6D766]):
                        box_706A0.prop(bpy.context.view_layer.objects.active.modifiers['Decimate'], 'ratio', text='', icon_value=0, emboss=True)
        if ((len(list(bpy.context.view_layer.objects.selected)) == 0) and '_link' in str(bpy.context.collection)):
            box_F3C61 = layout.box()
            box_F3C61.alert = False
            box_F3C61.enabled = True
            box_F3C61.active = True
            box_F3C61.use_property_split = False
            box_F3C61.use_property_decorate = False
            box_F3C61.alignment = 'Expand'.upper()
            box_F3C61.scale_x = 1.0
            box_F3C61.scale_y = 1.0
            if not True: box_F3C61.operator_context = "EXEC_DEFAULT"
            row_E28D3 = box_F3C61.row(heading='', align=False)
            row_E28D3.alert = False
            row_E28D3.enabled = True
            row_E28D3.active = True
            row_E28D3.use_property_split = False
            row_E28D3.use_property_decorate = False
            row_E28D3.scale_x = 1.0
            row_E28D3.scale_y = 1.0
            row_E28D3.alignment = 'Left'.upper()
            row_E28D3.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
            row_E28D3.label(text='Link Properties:', icon_value=0)
            row_E28D3.label(text=str(bpy.context.collection.name), icon_value=0)
            row_73088 = box_F3C61.row(heading='', align=False)
            row_73088.alert = False
            row_73088.enabled = True
            row_73088.active = True
            row_73088.use_property_split = False
            row_73088.use_property_decorate = False
            row_73088.scale_x = 1.0
            row_73088.scale_y = 1.0
            row_73088.alignment = 'Left'.upper()
            row_73088.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
            row_73088.label(text='Static', icon_value=0)
            row_73088.prop(bpy.context.collection, 'sna_isstatic', text='', icon_value=0, emboss=True)
        if (len(bpy.context.selected_objects) == 1):
            if '_include' in bpy.context.selected_objects[0].name:
                box_D0C95 = layout.box()
                box_D0C95.alert = False
                box_D0C95.enabled = True
                box_D0C95.active = True
                box_D0C95.use_property_split = False
                box_D0C95.use_property_decorate = False
                box_D0C95.alignment = 'Expand'.upper()
                box_D0C95.scale_x = 1.0
                box_D0C95.scale_y = 1.0
                if not True: box_D0C95.operator_context = "EXEC_DEFAULT"
                box_D0C95.label(text='Include Properties', icon_value=0)
                row_0CD45 = box_D0C95.row(heading='Model to Include', align=False)
                row_0CD45.alert = False
                row_0CD45.enabled = True
                row_0CD45.active = True
                row_0CD45.use_property_split = False
                row_0CD45.use_property_decorate = False
                row_0CD45.scale_x = 1.0
                row_0CD45.scale_y = 1.0
                row_0CD45.alignment = 'Expand'.upper()
                row_0CD45.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
                row_0CD45.prop(bpy.context.view_layer.objects.active, 'sna_includescene', text='', icon_value=0, emboss=True)


class SNA_OT_Decimate_5Ed31(bpy.types.Operator):
    bl_idname = "sna.decimate_5ed31"
    bl_label = "Decimate"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        ui['sna_decimateexists'] = False
        for i_9F548 in range(len(bpy.context.view_layer.objects.active.modifiers)):
            ui['sna_decimateexists'] = 'Decimate' in str(bpy.context.view_layer.objects.active.modifiers[i_9F548])
        if ui['sna_decimateexists']:
            pass
        else:
            bpy.ops.object.modifier_add('INVOKE_DEFAULT', type='DECIMATE')
            bpy.context.view_layer.objects.active.modifiers['Decimate'].ratio = 0.20000000298023224
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_hierarchytab_C3C26(layout_function, ):
    box_866A3 = layout_function.box()
    box_866A3.alert = False
    box_866A3.enabled = True
    box_866A3.active = True
    box_866A3.use_property_split = False
    box_866A3.use_property_decorate = False
    box_866A3.alignment = 'Expand'.upper()
    box_866A3.scale_x = 1.0
    box_866A3.scale_y = 1.0
    if not True: box_866A3.operator_context = "EXEC_DEFAULT"
    box_866A3.label(text='Models', icon_value=0)
    box_5FD7F = box_866A3.box()
    box_5FD7F.alert = False
    box_5FD7F.enabled = True
    box_5FD7F.active = True
    box_5FD7F.use_property_split = False
    box_5FD7F.use_property_decorate = False
    box_5FD7F.alignment = 'Expand'.upper()
    box_5FD7F.scale_x = 1.0
    box_5FD7F.scale_y = 1.0
    if not True: box_5FD7F.operator_context = "EXEC_DEFAULT"
    split_7845D = box_5FD7F.split(factor=0.8999999761581421, align=False)
    split_7845D.alert = False
    split_7845D.enabled = True
    split_7845D.active = True
    split_7845D.use_property_split = False
    split_7845D.use_property_decorate = False
    split_7845D.scale_x = 1.0
    split_7845D.scale_y = 1.0
    split_7845D.alignment = 'Expand'.upper()
    if not True: split_7845D.operator_context = "EXEC_DEFAULT"
    coll_id = display_collection_id('1546D', locals())
    split_7845D.template_list('SNA_UL_display_collection_list_1546D', coll_id, bpy.data, 'scenes', bpy.context.window_manager, 'sna_sceneindex', rows=len(bpy.data.scenes))
    col_7D2C4 = split_7845D.column(heading='', align=False)
    col_7D2C4.alert = False
    col_7D2C4.enabled = True
    col_7D2C4.active = True
    col_7D2C4.use_property_split = False
    col_7D2C4.use_property_decorate = False
    col_7D2C4.scale_x = 1.0
    col_7D2C4.scale_y = 1.0
    col_7D2C4.alignment = 'Expand'.upper()
    col_7D2C4.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
    op = col_7D2C4.operator('sna.create_model_63761', text='', icon_value=31, emboss=True, depress=False)
    op = col_7D2C4.operator('sna.remove_model_08467', text='', icon_value=32, emboss=True, depress=False)
    op = box_866A3.operator('sna.createlink_af238', text='Create Link', icon_value=0, emboss=True, depress=False)
    op = box_866A3.operator('sna.clone_link_11408', text='Clone Link', icon_value=0, emboss=True, depress=False)
    op = box_866A3.operator('sna.add_include_d77ba', text='Create Instance', icon_value=0, emboss=True, depress=False)


class SNA_PT_NEW_PANEL_EFE02(bpy.types.Panel):
    bl_label = 'New Panel'
    bl_idname = 'SNA_PT_NEW_PANEL_EFE02'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_order = 0
    bl_parent_id = 'RENDER_PT_context'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        col_1DD57 = layout.column(heading='', align=False)
        col_1DD57.alert = False
        col_1DD57.enabled = True
        col_1DD57.active = True
        col_1DD57.use_property_split = False
        col_1DD57.use_property_decorate = False
        col_1DD57.scale_x = 1.0
        col_1DD57.scale_y = 1.0
        col_1DD57.alignment = 'Expand'.upper()
        col_1DD57.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_1DD57.label(text='My Label', icon_value=0)


class SNA_GROUP_sna_property_group(bpy.types.PropertyGroup):
    string: bpy.props.StringProperty(name='String', description='', default='', subtype='NONE', maxlen=0)


class SNA_GROUP_sna_sog(bpy.types.PropertyGroup):
    new_property: bpy.props.StringProperty(name='New Property', description='', default='', subtype='NONE', maxlen=0)


class SNA_GROUP_sna_new_property(bpy.types.PropertyGroup):
    iron: bpy.props.FloatProperty(name='Iron', description='', default=5.235420227050781, subtype='NONE', unit='MASS', step=3, precision=6)
    aluminum: bpy.props.FloatProperty(name='Aluminum', description='', default=1.0, subtype='NONE', unit='MASS', step=3, precision=6)


class SNA_GROUP_sna_materialmass(bpy.types.PropertyGroup):
    aluminum: bpy.props.FloatProperty(name='Aluminum', description='', default=1.399999976158142, subtype='NONE', unit='NONE', step=3, precision=3)


class SNA_GROUP_sna_errorsgroup(bpy.types.PropertyGroup):
    pass


def sna_update_sna_visualmaterial(self, context):
    sna_update_sna_visualmaterial_6C149(self, context)
    sna_update_sna_visualmaterial_E3F9C(self, context)


def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.utils.register_class(SNA_GROUP_sna_property_group)
    bpy.utils.register_class(SNA_GROUP_sna_sog)
    bpy.utils.register_class(SNA_GROUP_sna_new_property)
    bpy.utils.register_class(SNA_GROUP_sna_materialmass)
    bpy.utils.register_class(SNA_GROUP_sna_errorsgroup)
    bpy.types.Scene.sna_source_collection = bpy.props.CollectionProperty(name='Source Collection', description='', type=SNA_GROUP_sna_property_group)
    bpy.types.Scene.sna_duplicate_to_delete = bpy.props.PointerProperty(name='Duplicate to delete', description='', type=bpy.types.Object)
    bpy.types.Scene.sna_cylcaplocation = bpy.props.FloatProperty(name='CylCapLocation', description='', default=0.0, subtype='NONE', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_selectedobjsforexp = bpy.props.PointerProperty(name='SelectedObjsForExp', description='', type=bpy.types.Collection)
    bpy.types.Object.sna_radius = bpy.props.FloatProperty(name='Radius', description='', default=0.0, subtype='NONE', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_radiuscylinderx = bpy.props.FloatProperty(name='RadiusCylinderX', description='', default=0.0, subtype='NONE', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_radiuscylindery = bpy.props.FloatProperty(name='RadiusCylinderY', description='', default=0.0, subtype='NONE', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_perobj = bpy.props.BoolProperty(name='PerObj', description='', default=False)
    bpy.types.Object.sna_actobjcollider = bpy.props.PointerProperty(name='ActObjCollider', description='', type=bpy.types.Scene)
    bpy.types.Scene.sna_minbox = bpy.props.BoolProperty(name='MinBox', description='', default=False)
    bpy.types.Scene.sna_filepath = bpy.props.StringProperty(name='FilePath', description='', default='C:/', subtype='DIR_PATH', maxlen=0)
    bpy.types.Scene.sna_filepathtype = bpy.props.StringProperty(name='FilePathType', description='', default='', subtype='FILE_PATH', maxlen=0)
    bpy.types.Scene.sna_scale = bpy.props.FloatProperty(name='Scale', description='', default=0.0, subtype='NONE', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_visualname = bpy.props.StringProperty(name='VisualName', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Collection.sna_isstatic = bpy.props.BoolProperty(name='IsStatic', description='', default=True)
    bpy.types.Scene.sna_linkname = bpy.props.StringProperty(name='LinkName', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_ismeshselected = bpy.props.BoolProperty(name='IsMeshSelected', description='', default=False)
    bpy.types.Scene.sna_linkscale = bpy.props.FloatProperty(name='LinkScale', description='', default=0.0, subtype='NONE', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_parentobj = bpy.props.PointerProperty(name='ParentObj', description='', type=bpy.types.Object)
    bpy.types.Scene.sna_transformmatrix = bpy.props.StringProperty(name='TransformMatrix', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_link = bpy.props.PointerProperty(name='Link', description='', type=bpy.types.Object)
    bpy.types.Scene.sna_source_location = bpy.props.EnumProperty(name='Source Location', description='', items=[])
    bpy.types.Scene.sna_mass = bpy.props.FloatProperty(name='Mass', description='', default=1.0, subtype='NONE', unit='NONE', step=3, precision=3)
    bpy.types.Scene.sna_inertiaobject = bpy.props.PointerProperty(name='InertiaObject', description='', type=bpy.types.Object)
    bpy.types.Scene.sna_new_property_001 = bpy.props.CollectionProperty(name='New Property 001', description='', type=SNA_GROUP_sna_new_property)
    bpy.types.Collection.sna_new_property_002 = bpy.props.PointerProperty(name='New Property 002', description='', type=SNA_GROUP_sna_new_property)
    bpy.types.Scene.sna_new_property_003 = bpy.props.IntProperty(name='New Property 003', description='', default=0, subtype='NONE')
    bpy.types.Scene.sna_stored_matrix = bpy.props.EnumProperty(name='stored_matrix', description='', items=[])
    bpy.types.Scene.sna_link_location = bpy.props.FloatVectorProperty(name='Link_Location', description='', size=3, default=(0.0, 0.0, 0.0), subtype='NONE', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_link_rotation = bpy.props.FloatVectorProperty(name='Link_Rotation', description='', size=3, default=(0.0, 0.0, 0.0), subtype='NONE', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_collidervisibiity = bpy.props.BoolProperty(name='ColliderVisibiity', description='Show/Hide Colliders', default=True, update=sna_update_sna_collidervisibiity_8151C)
    bpy.types.Object.sna_jointtype = bpy.props.StringProperty(name='JointType', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_jointname = bpy.props.StringProperty(name='JointName', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_jointtypes = bpy.props.EnumProperty(name='JointTypes', description='', items=[('Fixed', 'Fixed', '', 0, 0), ('Revolute', 'Revolute', '', 0, 1), ('Prismatic', 'Prismatic', '', 0, 2)])
    bpy.types.Object.sna_pose = bpy.props.StringProperty(name='Pose', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Object.sna_parent = bpy.props.PointerProperty(name='Parent', description='', type=bpy.types.Collection)
    bpy.types.Object.sna_child = bpy.props.PointerProperty(name='Child', description='', type=bpy.types.Collection)
    bpy.types.Object.sna_limits_lower = bpy.props.FloatProperty(name='Limits_Lower', description='', default=0.0, subtype='ANGLE', unit='ROTATION', min=-6.28318977355957, max=0.0, step=3, precision=6, update=sna_update_sna_limits_lower_AAA88)
    bpy.types.Object.sna_limits_upper = bpy.props.FloatProperty(name='Limits_Upper', description='', default=0.0, subtype='ANGLE', unit='ROTATION', min=0.0, max=6.28318977355957, step=3, precision=6, update=sna_update_sna_limits_upper_9ECDF)
    bpy.types.Object.sna_axis_x = bpy.props.FloatProperty(name='Axis X', description='', default=0.0, subtype='NONE', unit='NONE', min=-1.0, max=1.0, step=3, precision=6)
    bpy.types.Object.sna_axis_y = bpy.props.FloatProperty(name='Axis Y', description='', default=0.0, subtype='NONE', unit='NONE', min=-1.0, max=1.0, step=3, precision=6)
    bpy.types.Object.sna_axis_z = bpy.props.FloatProperty(name='Axis Z', description='', default=0.0, subtype='NONE', unit='NONE', min=-1.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_joint_shape = bpy.props.StringProperty(name='Joint Shape', description='', default='CUBE', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_stringtest = bpy.props.StringProperty(name='StringTest', description='', default='AGJUFH', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_jointobj = bpy.props.PointerProperty(name='JointObj', description='', type=bpy.types.Object)
    bpy.types.Scene.sna_mainjoint = bpy.props.PointerProperty(name='MainJoint', description='', type=bpy.types.Object)
    bpy.types.Scene.sna_upper_limit = bpy.props.PointerProperty(name='upper_limit', description='', type=bpy.types.Object)
    bpy.types.Scene.sna_lower_limit = bpy.props.PointerProperty(name='lower_limit', description='', type=bpy.types.Object)
    bpy.types.Object.sna_collider_collection_exists = bpy.props.BoolProperty(name='Collider Collection Exists', description='', default=False)
    bpy.types.Scene.sna_collider_collection_name = bpy.props.StringProperty(name='Collider Collection Name', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_in_scene_collection = bpy.props.BoolProperty(name='In Scene Collection', description='', default=False)
    bpy.types.Scene.sna_in_correct_collection = bpy.props.BoolProperty(name='In correct collection', description='', default=False)
    bpy.types.Scene.sna_active_visual_object = bpy.props.PointerProperty(name='Active Visual Object', description='', type=bpy.types.Object)
    bpy.types.Scene.sna_jointvisibility = bpy.props.BoolProperty(name='JointVisibility', description='Show/Hide Links', default=True, update=sna_update_sna_jointvisibility_80CDE)
    bpy.types.Object.sna_iscontinuous = bpy.props.BoolProperty(name='IsContinuous', description='', default=False, update=sna_update_sna_iscontinuous_810A8)
    bpy.types.Scene.sna_upperlimitprint = bpy.props.StringProperty(name='UpperLimitPrint', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_lowerlimitprint = bpy.props.StringProperty(name='LowerLimitPrint', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Object.sna_limits_upper_distance = bpy.props.FloatProperty(name='Limits_Upper_Distance', description='', default=0.0, subtype='NONE', unit='LENGTH', min=0.0, step=3, precision=6, update=sna_update_sna_limits_upper_distance_183F5)
    bpy.types.Object.sna_limits_lower_distance = bpy.props.FloatProperty(name='Limits_Lower_Distance', description='', default=0.0, subtype='NONE', unit='LENGTH', max=0.0, step=3, precision=6, update=sna_update_sna_limits_lower_distance_80B68)
    bpy.types.Scene.sna_exportfiletype = bpy.props.EnumProperty(name='ExportFileType', description='', items=[('glb', 'glb', '', 0, 0), ('gltf', 'gltf', '', 0, 1), ('dae', 'dae', '', 0, 2)])
    bpy.types.Scene.sna_collectionlength = bpy.props.PointerProperty(name='CollectionLength', description='', type=bpy.types.Collection)
    bpy.types.Scene.sna_materialmasscol = bpy.props.CollectionProperty(name='MaterialMassCol', description='', type=SNA_GROUP_sna_materialmass)
    bpy.types.Object.sna_materialsmass = bpy.props.EnumProperty(name='MaterialsMass', description='', items=[('Default - 1.0', 'Default - 1.0', '', 0, 0), ('Aluminum – 2.7', 'Aluminum – 2.7', '', 0, 1), ('Brass – 8.57', 'Brass – 8.57', '', 0, 2), ('Bronze – 8.15', 'Bronze – 8.15', '', 0, 3), ('Carbon Fiber – 1.6', 'Carbon Fiber – 1.6', '', 0, 4), ('Copper – 8.96', 'Copper – 8.96', '', 0, 5), ('Glass – 2.60', 'Glass – 2.60', '', 0, 6), ('Iron (Cast) – 7.05', 'Iron (Cast) – 7.05', '', 0, 7), ('Iron (Wrought) – 7.88', 'Iron (Wrought) – 7.88', '', 0, 8), ('Lead – 11.34', 'Lead – 11.34', '', 0, 9), ('Magnesium – 1.74', 'Magnesium – 1.74', '', 0, 10), ('Nickel – 8.90', 'Nickel – 8.90', '', 0, 11), ('Plastic (ABS) – 1.05', 'Plastic (ABS) – 1.05', '', 0, 12), ('Plastic (Polyethylene) – 0.94', 'Plastic (Polyethylene) – 0.94', '', 0, 13), ('Plastic (Polypropylene) – 0.91', 'Plastic (Polypropylene) – 0.91', '', 0, 14), ('Rubber – 1.20', 'Rubber – 1.20', '', 0, 15), ('Steel (Carbon) – 7.85', 'Steel (Carbon) – 7.85', '', 0, 16), ('Steel (Stainless) – 7.90', 'Steel (Stainless) – 7.90', '', 0, 17), ('Tin – 7.30', 'Tin – 7.30', '', 0, 18), ('Titanium – 4.51', 'Titanium – 4.51', '', 0, 19), ('Tungsten – 19.30', 'Tungsten – 19.30', '', 0, 20), ('inc – 7.13', 'inc – 7.13', '', 0, 21)])
    bpy.types.Scene.sna_geninertia = bpy.props.BoolProperty(name='GenInertia', description='', default=False)
    bpy.types.Scene.sna_index = bpy.props.IntProperty(name='Index', description='', default=0, subtype='NONE')
    bpy.types.Scene.sna_model_name = bpy.props.StringProperty(name='Model Name', description='', default='Model', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_empty_color = bpy.props.FloatVectorProperty(name='Empty Color', description='', size=3, default=(0.0, 1.0, 1.0), subtype='COLOR', unit='NONE', step=3, precision=6)
    bpy.types.Collection.sna_link_density = bpy.props.FloatProperty(name='Link_Density', description='', default=1.0, subtype='NONE', unit='MASS', step=3, precision=6)
    bpy.types.Collection.sna_link_geninertia = bpy.props.BoolProperty(name='Link_GenInertia', description='', default=False)
    bpy.types.Collection.sna_issourcemodel = bpy.props.BoolProperty(name='IsSourceModel', description='', default=False)
    bpy.types.Scene.sna_includename = bpy.props.StringProperty(name='IncludeName', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Object.sna_includemodel = bpy.props.PointerProperty(name='IncludeModel', description='', type=bpy.types.Collection)
    bpy.types.Scene.sna_sdf_file_paths = bpy.props.EnumProperty(name='SDF_File_Paths', description='', items=[('Blank', 'Blank', 'Blank', 0, 0), ('Same as export path', 'Same as export path', 'Same as export path', 0, 1), ('Custom', 'Custom', 'Custom', 0, 2)])
    bpy.types.Scene.sna_sdf_custom_path = bpy.props.StringProperty(name='SDF_Custom_Path', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_sdf_export_path = bpy.props.StringProperty(name='SDF_Export_Path', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_sdf_export_modelname = bpy.props.StringProperty(name='SDF_Export_ModelName', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_parentcompare = bpy.props.StringProperty(name='ParentCompare', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_childcompare = bpy.props.StringProperty(name='ChildCompare', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Object.sna_sdf_child = bpy.props.StringProperty(name='SDF_Child', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_modelname = bpy.props.StringProperty(name='ModelName', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Object.sna_custommassbool = bpy.props.BoolProperty(name='CustomMassBool', description='', default=False)
    bpy.types.Object.sna_custommass = bpy.props.FloatProperty(name='CustomMass', description='', default=1.0, subtype='NONE', unit='NONE', step=10, precision=3)
    bpy.types.Scene.sna_errors = bpy.props.StringProperty(name='Errors', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_errorcollection = bpy.props.CollectionProperty(name='ErrorCollection', description='', type=bpy.types.PropertyGroup.__subclasses__()[0])
    bpy.types.Scene.sna_export_parent = bpy.props.StringProperty(name='Export_Parent', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_export_child = bpy.props.StringProperty(name='Export_Child', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_islink = bpy.props.BoolProperty(name='islink', description='', default=False)
    bpy.types.Scene.sna_userpath = bpy.props.StringProperty(name='UserPath', description='', default='', subtype='FILE_PATH', maxlen=0)
    bpy.types.Object.sna_cylrad = bpy.props.FloatProperty(name='CylRad', description='', default=0.0, subtype='DISTANCE', unit='NONE', step=1, precision=6, update=sna_update_sna_cylrad_0B327)
    bpy.types.Scene.sna_collidermargin = bpy.props.FloatProperty(name='ColliderMargin', description='', default=0.0, subtype='DISTANCE', unit='NONE', min=0.0, step=3, precision=6, update=sna_update_sna_collidermargin_4105F)
    bpy.types.Scene.sna_objectvolume = bpy.props.FloatProperty(name='ObjectVolume', description='', default=1.0, subtype='NONE', unit='NONE', step=3, precision=3)
    bpy.types.Scene.sna_isobjectmode = bpy.props.BoolProperty(name='IsObjectMode', description='', default=False)
    bpy.types.Object.sna_visualmaterial = bpy.props.EnumProperty(name='VisualMaterial', description='', items=[('NONE', 'NONE', '', 0, 0), ('Aluminum', 'Aluminum', '', 0, 1)], update=sna_update_sna_visualmaterial)
    bpy.types.Scene.sna_selectedobjects = bpy.props.CollectionProperty(name='SelectedObjects', description='', type=bpy.types.PropertyGroup.__subclasses__()[0])
    bpy.types.Scene.sna_hierarchy_model_exists = bpy.props.BoolProperty(name='Hierarchy model exists', description='', default=False)
    bpy.types.WindowManager.sna_sceneindex = bpy.props.IntProperty(name='SceneIndex', description='', default=0, subtype='NONE', update=sna_update_sna_sceneindex_6B93D)
    bpy.types.Object.sna_includescene = bpy.props.PointerProperty(name='IncludeScene', description='', type=bpy.types.Scene)
    bpy.types.Scene.sna_includesceneindex = bpy.props.IntProperty(name='IncludeSceneIndex', description='', default=0, subtype='NONE')
    bpy.types.Scene.sna_tabscreate = bpy.props.EnumProperty(name='TabsCreate', description='', items=[('Hierarchy', 'Hierarchy', '', 0, 0), ('Colliders', 'Colliders', '', 0, 1), ('Joints', 'Joints', '', 0, 2)])
    bpy.types.WindowManager.sna_initialscene = bpy.props.PointerProperty(name='InitialScene', description='', type=bpy.types.Scene)
    bpy.types.WindowManager.sna_exportscene = bpy.props.PointerProperty(name='ExportScene', description='', type=bpy.types.Scene)
    bpy.types.Scene.sna_tabsprops = bpy.props.EnumProperty(name='TabsProps', description='', items=[])
    bpy.utils.register_class(SNA_OT_Box_9D9E4)
    bpy.utils.register_class(SNA_OT_Minbox_0936B)
    bpy.utils.register_class(SNA_OT_Scale_Cage_4E08E)
    bpy.utils.register_class(SNA_OT_Select_Cylinder_Face_8A190)
    bpy.utils.register_class(SNA_OT_Move_To_Collision_Collection_B7E42)
    bpy.utils.register_class(SNA_OT_Move_To_Colllder_Collection_1Fa60)
    bpy.utils.register_class(SNA_OT_Set_Active_Collection_50942)
    bpy.utils.register_class(SNA_OT_Set_Collider_Material_33Bff)
    bpy.utils.register_class(SNA_OT_Set_Active_Object_40Bc9)
    bpy.utils.register_class(SNA_OT_Scalecylradius_E1610)
    bpy.utils.register_class(SNA_OT_Scalesphereradius_Bd79D)
    bpy.utils.register_class(SNA_OT_Add_Margin_Modifier_43181)
    bpy.utils.register_class(SNA_OT_Collider_Creation_Setiup_8E177)
    bpy.utils.register_class(SNA_OT_Create_Cone_3Ded7)
    bpy.utils.register_class(SNA_OT_Cylinder_050B8)
    bpy.utils.register_class(SNA_OT_Cylinder_Z_83F4C)
    bpy.utils.register_class(SNA_OT_Cylinder_X_3A040)
    bpy.utils.register_class(SNA_OT_Cylinder_Y_F23B4)
    bpy.utils.register_class(SNA_OT_Export_All_B6B8D)
    bpy.utils.register_class(SNA_OT_Set_File_Path_Fb37A)
    bpy.utils.register_class(SNA_OT_Sdf_Link_Clone_2564F)
    bpy.utils.register_class(SNA_OT_Sdf_Include_0A203)
    bpy.utils.register_class(SNA_OT_Selectflatfaces_0Bf7C)
    bpy.utils.register_class(SNA_OT_Cylindercap_0F9D8)
    bpy.utils.register_class(SNA_OT_Boxcap_7899E)
    bpy.utils.register_class(SNA_OT_Conecap_53679)
    bpy.utils.register_class(SNA_OT_Select_Cone_Tip_6A0B7)
    bpy.utils.register_class(SNA_OT_Planecap_E5C55)
    bpy.utils.register_class(SNA_OT_Mesh_85D40)
    bpy.utils.register_class(SNA_PT_UTILITIES_9531D)
    bpy.utils.register_class(SNA_OT_Import_Stl_90582)
    bpy.utils.register_class(SNA_OT_Import_Fbx_644D9)
    bpy.utils.register_class(SNA_OT_Import_Obj_Befeb)
    bpy.utils.register_class(SNA_OT_Import_Dae_A17Ee)
    bpy.utils.register_class(SNA_OT_Clear_Hierarchy_9Ff17)
    bpy.utils.register_class(SNA_OT_Separate_Parts_17Bd5)
    bpy.utils.register_class(SNA_OT_Separate_By_Material_8Dbf4)
    bpy.utils.register_class(SNA_OT_Select_Small_Geometry_8Dbe4)
    bpy.types.VIEW3D_MT_add.append(sna_add_to_view3d_mt_add_CED9A)
    bpy.utils.register_class(SNA_OT_Set_Joint_Shape_Ded74)
    bpy.utils.register_class(SNA_OT_Link_Properties_28B11)
    bpy.utils.register_class(SNA_OT_Create_Joint_D6784)
    bpy.utils.register_class(SNA_OT_Create_Fixed_Joint_61041)
    bpy.types.OBJECT_PT_context_object.append(sna_add_to_object_pt_context_object_449E2)
    bpy.utils.register_class(SNA_OT_Create_Prismatic_Joint_A9Ec2)
    bpy.utils.register_class(SNA_OT_Scale_Joint_0971A)
    bpy.utils.register_class(SNA_OT_Create_Revolute_Joint_941Aa)
    bpy.utils.register_class(SNA_OT_Createlink_Af238)
    bpy.utils.register_class(SNA_OT_Clone_Link_11408)
    bpy.utils.register_class(SNA_OT_Add_Include_D77Ba)
    bpy.utils.register_class(SNA_UL_display_collection_list001_E2509)
    bpy.utils.register_class(SNA_OT_Create_Model_63761)
    bpy.utils.register_class(SNA_OT_Remove_Model_08467)
    bpy.utils.register_class(SNA_OT_Plane_Z_01890)
    bpy.utils.register_class(SNA_OT_Plane_182F2)
    bpy.utils.register_class(SNA_OT_Plane_X_3923A)
    bpy.utils.register_class(SNA_OT_Plane_Y_E935A)
    bpy.utils.register_class(SNA_PT_VISUAL_PROPERTIES_71786)
    bpy.utils.register_class(SNA_PT_VISIBILITY_0147F)
    bpy.utils.register_class(SNA_PT_EXPORT_0BD82)
    bpy.utils.register_class(SNA_PT_CREATE_88892)
    bpy.utils.register_class(SNA_OT_Sphere_F5Cd9)
    bpy.utils.register_class(SNA_OT_Sphereop_6D8A0)
    bpy.utils.register_class(SNA_PT_PROPERTIES_7CC42)
    bpy.utils.register_class(SNA_OT_Decimate_5Ed31)
    bpy.utils.register_class(SNA_UL_display_collection_list_1546D)
    bpy.utils.register_class(SNA_PT_NEW_PANEL_EFE02)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    del bpy.types.Scene.sna_tabsprops
    del bpy.types.WindowManager.sna_exportscene
    del bpy.types.WindowManager.sna_initialscene
    del bpy.types.Scene.sna_tabscreate
    del bpy.types.Scene.sna_includesceneindex
    del bpy.types.Object.sna_includescene
    del bpy.types.WindowManager.sna_sceneindex
    del bpy.types.Scene.sna_hierarchy_model_exists
    del bpy.types.Scene.sna_selectedobjects
    del bpy.types.Object.sna_visualmaterial
    del bpy.types.Scene.sna_isobjectmode
    del bpy.types.Scene.sna_objectvolume
    del bpy.types.Scene.sna_collidermargin
    del bpy.types.Object.sna_cylrad
    del bpy.types.Scene.sna_userpath
    del bpy.types.Scene.sna_islink
    del bpy.types.Scene.sna_export_child
    del bpy.types.Scene.sna_export_parent
    del bpy.types.Scene.sna_errorcollection
    del bpy.types.Scene.sna_errors
    del bpy.types.Object.sna_custommass
    del bpy.types.Object.sna_custommassbool
    del bpy.types.Scene.sna_modelname
    del bpy.types.Object.sna_sdf_child
    del bpy.types.Scene.sna_childcompare
    del bpy.types.Scene.sna_parentcompare
    del bpy.types.Scene.sna_sdf_export_modelname
    del bpy.types.Scene.sna_sdf_export_path
    del bpy.types.Scene.sna_sdf_custom_path
    del bpy.types.Scene.sna_sdf_file_paths
    del bpy.types.Object.sna_includemodel
    del bpy.types.Scene.sna_includename
    del bpy.types.Collection.sna_issourcemodel
    del bpy.types.Collection.sna_link_geninertia
    del bpy.types.Collection.sna_link_density
    del bpy.types.Scene.sna_empty_color
    del bpy.types.Scene.sna_model_name
    del bpy.types.Scene.sna_index
    del bpy.types.Scene.sna_geninertia
    del bpy.types.Object.sna_materialsmass
    del bpy.types.Scene.sna_materialmasscol
    del bpy.types.Scene.sna_collectionlength
    del bpy.types.Scene.sna_exportfiletype
    del bpy.types.Object.sna_limits_lower_distance
    del bpy.types.Object.sna_limits_upper_distance
    del bpy.types.Scene.sna_lowerlimitprint
    del bpy.types.Scene.sna_upperlimitprint
    del bpy.types.Object.sna_iscontinuous
    del bpy.types.Scene.sna_jointvisibility
    del bpy.types.Scene.sna_active_visual_object
    del bpy.types.Scene.sna_in_correct_collection
    del bpy.types.Scene.sna_in_scene_collection
    del bpy.types.Scene.sna_collider_collection_name
    del bpy.types.Object.sna_collider_collection_exists
    del bpy.types.Scene.sna_lower_limit
    del bpy.types.Scene.sna_upper_limit
    del bpy.types.Scene.sna_mainjoint
    del bpy.types.Scene.sna_jointobj
    del bpy.types.Scene.sna_stringtest
    del bpy.types.Scene.sna_joint_shape
    del bpy.types.Object.sna_axis_z
    del bpy.types.Object.sna_axis_y
    del bpy.types.Object.sna_axis_x
    del bpy.types.Object.sna_limits_upper
    del bpy.types.Object.sna_limits_lower
    del bpy.types.Object.sna_child
    del bpy.types.Object.sna_parent
    del bpy.types.Object.sna_pose
    del bpy.types.Scene.sna_jointtypes
    del bpy.types.Scene.sna_jointname
    del bpy.types.Object.sna_jointtype
    del bpy.types.Scene.sna_collidervisibiity
    del bpy.types.Scene.sna_link_rotation
    del bpy.types.Scene.sna_link_location
    del bpy.types.Scene.sna_stored_matrix
    del bpy.types.Scene.sna_new_property_003
    del bpy.types.Collection.sna_new_property_002
    del bpy.types.Scene.sna_new_property_001
    del bpy.types.Scene.sna_inertiaobject
    del bpy.types.Scene.sna_mass
    del bpy.types.Scene.sna_source_location
    del bpy.types.Scene.sna_link
    del bpy.types.Scene.sna_transformmatrix
    del bpy.types.Scene.sna_parentobj
    del bpy.types.Scene.sna_linkscale
    del bpy.types.Scene.sna_ismeshselected
    del bpy.types.Scene.sna_linkname
    del bpy.types.Collection.sna_isstatic
    del bpy.types.Scene.sna_visualname
    del bpy.types.Scene.sna_scale
    del bpy.types.Scene.sna_filepathtype
    del bpy.types.Scene.sna_filepath
    del bpy.types.Scene.sna_minbox
    del bpy.types.Object.sna_actobjcollider
    del bpy.types.Scene.sna_perobj
    del bpy.types.Scene.sna_radiuscylindery
    del bpy.types.Scene.sna_radiuscylinderx
    del bpy.types.Object.sna_radius
    del bpy.types.Scene.sna_selectedobjsforexp
    del bpy.types.Scene.sna_cylcaplocation
    del bpy.types.Scene.sna_duplicate_to_delete
    del bpy.types.Scene.sna_source_collection
    bpy.utils.unregister_class(SNA_GROUP_sna_errorsgroup)
    bpy.utils.unregister_class(SNA_GROUP_sna_materialmass)
    bpy.utils.unregister_class(SNA_GROUP_sna_new_property)
    bpy.utils.unregister_class(SNA_GROUP_sna_sog)
    bpy.utils.unregister_class(SNA_GROUP_sna_property_group)
    bpy.utils.unregister_class(SNA_OT_Box_9D9E4)
    bpy.utils.unregister_class(SNA_OT_Minbox_0936B)
    bpy.utils.unregister_class(SNA_OT_Scale_Cage_4E08E)
    bpy.utils.unregister_class(SNA_OT_Select_Cylinder_Face_8A190)
    bpy.utils.unregister_class(SNA_OT_Move_To_Collision_Collection_B7E42)
    bpy.utils.unregister_class(SNA_OT_Move_To_Colllder_Collection_1Fa60)
    bpy.utils.unregister_class(SNA_OT_Set_Active_Collection_50942)
    bpy.utils.unregister_class(SNA_OT_Set_Collider_Material_33Bff)
    bpy.utils.unregister_class(SNA_OT_Set_Active_Object_40Bc9)
    bpy.utils.unregister_class(SNA_OT_Scalecylradius_E1610)
    bpy.utils.unregister_class(SNA_OT_Scalesphereradius_Bd79D)
    bpy.utils.unregister_class(SNA_OT_Add_Margin_Modifier_43181)
    bpy.utils.unregister_class(SNA_OT_Collider_Creation_Setiup_8E177)
    bpy.utils.unregister_class(SNA_OT_Create_Cone_3Ded7)
    bpy.utils.unregister_class(SNA_OT_Cylinder_050B8)
    bpy.utils.unregister_class(SNA_OT_Cylinder_Z_83F4C)
    bpy.utils.unregister_class(SNA_OT_Cylinder_X_3A040)
    bpy.utils.unregister_class(SNA_OT_Cylinder_Y_F23B4)
    bpy.utils.unregister_class(SNA_OT_Export_All_B6B8D)
    bpy.utils.unregister_class(SNA_OT_Set_File_Path_Fb37A)
    bpy.utils.unregister_class(SNA_OT_Sdf_Link_Clone_2564F)
    bpy.utils.unregister_class(SNA_OT_Sdf_Include_0A203)
    bpy.utils.unregister_class(SNA_OT_Selectflatfaces_0Bf7C)
    bpy.utils.unregister_class(SNA_OT_Cylindercap_0F9D8)
    bpy.utils.unregister_class(SNA_OT_Boxcap_7899E)
    bpy.utils.unregister_class(SNA_OT_Conecap_53679)
    bpy.utils.unregister_class(SNA_OT_Select_Cone_Tip_6A0B7)
    bpy.utils.unregister_class(SNA_OT_Planecap_E5C55)
    bpy.utils.unregister_class(SNA_OT_Mesh_85D40)
    bpy.utils.unregister_class(SNA_PT_UTILITIES_9531D)
    bpy.utils.unregister_class(SNA_OT_Import_Stl_90582)
    bpy.utils.unregister_class(SNA_OT_Import_Fbx_644D9)
    bpy.utils.unregister_class(SNA_OT_Import_Obj_Befeb)
    bpy.utils.unregister_class(SNA_OT_Import_Dae_A17Ee)
    bpy.utils.unregister_class(SNA_OT_Clear_Hierarchy_9Ff17)
    bpy.utils.unregister_class(SNA_OT_Separate_Parts_17Bd5)
    bpy.utils.unregister_class(SNA_OT_Separate_By_Material_8Dbf4)
    bpy.utils.unregister_class(SNA_OT_Select_Small_Geometry_8Dbe4)
    bpy.types.VIEW3D_MT_add.remove(sna_add_to_view3d_mt_add_CED9A)
    bpy.utils.unregister_class(SNA_OT_Set_Joint_Shape_Ded74)
    bpy.utils.unregister_class(SNA_OT_Link_Properties_28B11)
    bpy.utils.unregister_class(SNA_OT_Create_Joint_D6784)
    bpy.utils.unregister_class(SNA_OT_Create_Fixed_Joint_61041)
    bpy.types.OBJECT_PT_context_object.remove(sna_add_to_object_pt_context_object_449E2)
    bpy.utils.unregister_class(SNA_OT_Create_Prismatic_Joint_A9Ec2)
    bpy.utils.unregister_class(SNA_OT_Scale_Joint_0971A)
    bpy.utils.unregister_class(SNA_OT_Create_Revolute_Joint_941Aa)
    bpy.utils.unregister_class(SNA_OT_Createlink_Af238)
    bpy.utils.unregister_class(SNA_OT_Clone_Link_11408)
    bpy.utils.unregister_class(SNA_OT_Add_Include_D77Ba)
    bpy.utils.unregister_class(SNA_UL_display_collection_list001_E2509)
    bpy.utils.unregister_class(SNA_OT_Create_Model_63761)
    bpy.utils.unregister_class(SNA_OT_Remove_Model_08467)
    bpy.utils.unregister_class(SNA_OT_Plane_Z_01890)
    bpy.utils.unregister_class(SNA_OT_Plane_182F2)
    bpy.utils.unregister_class(SNA_OT_Plane_X_3923A)
    bpy.utils.unregister_class(SNA_OT_Plane_Y_E935A)
    bpy.utils.unregister_class(SNA_PT_VISUAL_PROPERTIES_71786)
    bpy.utils.unregister_class(SNA_PT_VISIBILITY_0147F)
    bpy.utils.unregister_class(SNA_PT_EXPORT_0BD82)
    bpy.utils.unregister_class(SNA_PT_CREATE_88892)
    bpy.utils.unregister_class(SNA_OT_Sphere_F5Cd9)
    bpy.utils.unregister_class(SNA_OT_Sphereop_6D8A0)
    bpy.utils.unregister_class(SNA_PT_PROPERTIES_7CC42)
    bpy.utils.unregister_class(SNA_OT_Decimate_5Ed31)
    bpy.utils.unregister_class(SNA_UL_display_collection_list_1546D)
    bpy.utils.unregister_class(SNA_PT_NEW_PANEL_EFE02)
