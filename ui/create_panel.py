import bpy
import addon_utils
from ..operators.joints import SDFG_OT_CreateJoint
from ..operators.joints import SDFG_OT_ResetJoints
from ..operators.general_functions import show_message_box
from ..operators.general_functions import links_check
from ..operators.general_functions import get_armature
from ..operators.general_functions import get_instances_collection
from ..operators.create import switch_to_viewlayer
from ..operators.joints import MoveJoint

# bpy.types.Scene.armature_found = bpy.props.BoolProperty(default=False)

class SDFG_PT_CreateTabs(bpy.types.Panel):
    """Create tabs: Hierachy, Colliders, Joints"""
    bl_label = "Create"
    bl_idname = "SDFG_PT_CreatePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SDF_Gen"

    

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Spaces:")
        row.prop(scene, "tab_option", expand=True, icon_only=True)  # Creates buttons for each enum item

        if scene.tab_option == "LINKS":
            row = box.row()
            row.label(text="Models:")
            row = box.row()
            row.template_list(
                "SNA_UL_display_scenes_list",
                "",
                bpy.data,
                "scenes",
                context.window_manager,
                "my_list_index",
                rows=len(bpy.data.scenes) # + 1
            )

            col = row.column(align=True)
            col.operator("scene.add_simple", icon="ADD", text="")
            col.operator("scene.delete_scene", icon="REMOVE", text="")

            box = layout.box()
            col = box.column()
            col.label(text="Collections:")
            col.operator("scene.create_link_collections", text="Create Link")
            row = col.row()
            row.operator("scene.create_link_items", text="Visual")
            row.operator("scene.create_link_items", text="Collision")

            row = layout.row()

            row.prop(context.scene, "links_expand", 
                    icon="TRIA_DOWN" if context.scene.links_expand else "TRIA_RIGHT", 
                    icon_only=True, emboss=False)
            row.label(text="Links List")

            if context.scene.links_expand:
                
                box = layout.box()
                col = box.column()
                for collection in context.scene.collection.children:
                    if collection.collection_type == 'LinkCollection':
                        row = col.row()
                        row.label(text=collection.name)

        elif scene.tab_option == "COLLIDERS":
            links_found = links_check()
            split = box.split()
            col = split.column()

            if links_found == False:
                col.label(text="Something")

            col.operator("mesh.add_collider", text="Box").shape_type = "Box"
            col.operator("mesh.add_collider", text="Cylinder").shape_type = "Cylinder"
            col.operator("mesh.add_collider", text="Sphere").shape_type = "Sphere"
            col.operator("mesh.add_collider", text="Cone").shape_type = "Cone"
            col.operator("mesh.add_collider", text="Plane").shape_type = "Plane"

            col = split.column()
            col.operator("mesh.add_collider", text="Mesh Collider").shape_type = "Mesh"
            col.label(text="Transform:")
            col.operator("wm.tool_set_by_id", text="Scale Cage").name = (
                "builtin.scale_cage"
            )
            col.prop(
                bpy.context.scene,
                "face_snap",
                text="Face Snap",
                icon="SNAP_ON" if bpy.context.scene.face_snap else "SNAP_OFF",
            )

            row = layout.row()
            row.label(text="Collider Margin:")
            row.prop(bpy.context.scene, "collider_margin_thickness", text="")

            row = layout.row()

        elif scene.tab_option == "JOINTS":
            armature_object = get_armature()
            if armature_object == None:
                box.label(text="No armature found.")
                box.operator("object.create_armature", text="Create Armature")

            else:
                if bpy.context.mode == 'POSE':
                    row = box.row()
                    box.operator("scene.create_joint", text="Create Joint")
                    box.prop(bpy.context.scene, "move_joints", toggle=True, text="Adjust Joint Positions/Rotations")
                    if MoveJoint.is_running:
                        box.label(text="Pres ESC to cancel")
                        box.operator("object.joint_to_cursor", text="Move joint to cursor")

                    box.operator("scene.delete_joint", text="Delete Joints")
                    box.operator("scene.reset_joints", text="Reset Joints")

                    armature_object = get_armature()
                    instances_collection = get_instances_collection()
                    
                    
                    def draw_bone_hierarchy(bone, indent_level):
                        indent = "*" * (indent_level + 1) + " "
                        row = box.row()
                        row.label(text=indent + bone.name)
                        row.operator("object.select_joint", icon='RESTRICT_SELECT_OFF', text="").bone_name = bone.name
                        for obj in instances_collection.all_objects:
                            if obj.object_type == 'LinkInstanceObject':
                                if obj.constraints['Child Of'].subtarget and obj.constraints['Child Of'].subtarget == bone.name:
                                    row = box.row()
                                    row.label(text="*" + indent + obj.name)

                        for child_bone in bone.children:
                            draw_bone_hierarchy(child_bone, indent_level + 1)

                    root_bones = [bone for bone in armature_object.data.bones if bone.parent is None]

                    row = layout.row()
                    row.prop(context.scene, "joints_expand", 
                            icon="TRIA_DOWN" if context.scene.joints_expand else "TRIA_RIGHT", 
                            icon_only=True, emboss=False)
                    row.label(text="Joint Hierarchy")

                    if context.scene.joints_expand:
                        box = layout.box()
                        box.scale_y = 0.5
                        for root_bone in root_bones:
                            draw_bone_hierarchy(root_bone, 0)
                else:
                    box = layout.box()
                    box.label(text="Switch to pose mode to add and modify joints")

        elif scene.tab_option == "SENSORS":
            col = box.column()
            col.label(text="Sensors Tab")
            col.label(text="Under Construction", icon="WARNING_LARGE")

        elif scene.tab_option == "MATERIALS":

            obj = context.object
            
            if obj and obj.type == 'MESH':
                selected_index = bpy.context.object.active_material_index
                row = box.row()

                # Use a UIList for the material slots
                row.template_list("MATERIAL_UL_matslots", "", obj, "material_slots", obj, "active_material_index")

                col = row.column(align=True)
                # Add and remove material slots buttons
                col.operator("object.material_slot_add", icon='ADD', text="")
                col.operator("object.material_slot_remove", icon='REMOVE', text="")
                if bpy.context.selected_objects:
                    col.operator("object.material_slot_remove_unused", text="", icon='X')

                box = layout.box()

                # Add the "Browse material to be linked" button
                row = box.row()
                row.template_ID(obj, "active_material", new="material.new")

                if bpy.context.object.active_material_index != None and bpy.context.object.material_slots[selected_index].material:
                    selected_index = bpy.context.object.active_material_index
                    material = bpy.context.object.material_slots[selected_index].material
                    
                    if material.node_tree.nodes['Principled BSDF'].inputs[0]:
                        split = box.split(factor=0.4)
                        split.label(text="Color:")
                        split.prop(material.node_tree.nodes['Principled BSDF'].inputs[0], "default_value", text="")

                    if material.node_tree.nodes['Principled BSDF'].inputs[1]:
                        split = box.split(factor=0.4)
                        split.label(text="Metallness:")
                        split.prop(material.node_tree.nodes['Principled BSDF'].inputs[1], "default_value", text="")

                    if material.node_tree.nodes['Principled BSDF'].inputs[2]:
                        split = box.split(factor=0.4)
                        split.label(text="Roughness:")
                        split.prop(material.node_tree.nodes['Principled BSDF'].inputs[2], "default_value", text="")

                    if material.node_tree.nodes['Principled BSDF'].inputs[4]:
                        split = box.split(factor=0.4)
                        split.label(text="Transparency:")
                        split.prop(material.node_tree.nodes['Principled BSDF'].inputs[4], "default_value", text="")

                layout = self.layout
                box = layout.box()

                col=box.column()
                
                row = col.row()
                row.label(text="New Material:")
                row.prop(context.scene, "material_type", text="")

                col.operator("object.swap_material", text="Replace Material")

                split=col.split(factor=0.35, align=True)
                split.label(text="Keep Color:")
                split.prop(context.scene, "keep_color", text="")

            else:
                layout.label(text="Select an object.")

        elif scene.tab_option == "LIGHTS":
            box.operator("object.create_light", text="Point Light").light_type = 'POINT'
            box.operator("object.create_light", text="Spot Light").light_type = 'SPOT'
            box.operator("object.create_light", text="Directional Light").light_type = 'DIRECTIONAL'

        elif scene.tab_option == "UTILITIES":
            # Import
            box.label(text="Import")
            is_stepper_enabled = addon_utils.check("STEPper")[1]
            if is_stepper_enabled:
                box.operator("import_scene.occ_import_step", text="Import STEP")
            else:
                box.label(text="STEPper addon not installed/enabled")
                box.operator("wm.open_external_link", text="Get STEPper Addon", icon="LIBRARY_DATA_DIRECT")

            # Mesh tools
            box.label(text="Mesh tools")
            # Mesh utility buttons
            box.operator("scene.utility_operator", text="Clean Mesh").utility_type = 'CleanMesh'
            box.operator("scene.utility_operator", text="Separate by Loose Parts").utility_type = 'SeparateLoose'
            box.operator("scene.utility_operator", text="Separate by Material").utility_type = 'SeparateMaterial'

            box.label(text="")
            #split = box.split(factor=0.6)
            box.operator("scene.select_small_parts", text="Select Small Parts")
            split = box.split(factor=0.4, align=True)
            split.label(text="Objects under")
            split.prop(bpy.context.scene, "visual_volume", text="")
            split.label(text="cm³")

            row = box.row()
            # box.prop(bpy.context.scene, "utilities_advanced", text="Advanced", toggle=True)
            row.prop(context.scene, "utilities_advanced", 
                    icon="TRIA_DOWN" if context.scene.utilities_advanced else "TRIA_RIGHT", 
                    icon_only=True, emboss=False)
            row.label(text="Debug")

            if context.scene.utilities_advanced:
                box.operator("scene.convert_collections", text="Convert Collections")

        elif scene.tab_option == "RENDER":
            col = box.column()
            col.label(text="Render/Thumbnail Tab")
            col.label(text="Under Construction", icon="WARNING_LARGE")

        elif scene.tab_option == "EXPORT":
            col = box.column()
            row = col.row(align=True)
            row.label(text="Visual File Format:")
            row.prop(context.window_manager, "mesh_file_format", text="")
            col.prop(context.window_manager, "sdf_export_file_path", text="File Path")
            col.operator("sdf.export_sdf", text="Export SDF")
            
            row = layout.row()
            row.prop(context.scene, "sdf_options_expand", 
                    icon="TRIA_DOWN" if context.scene.sdf_options_expand else "TRIA_RIGHT", 
                    icon_only=True, emboss=False)
            row.label(text="SDF Options")

            if context.scene.sdf_options_expand:
                box = layout.box()
                col = box.column()
                col.prop(context.scene, "relative_link_poses", text="Relative link poses")

            col = layout.column()
            col.prop(context.scene, "export_config", text="Export Config File")
            if bpy.context.scene.export_config == True:
                box = layout.box()
                col = box.column()
                col.prop(context.scene, "author_name", text="Author")
                col.prop(context.scene, "author_email", text="Email")
                col.prop(context.scene, "model_description", text="Description")
