import bpy
import mathutils
from mathutils import Vector, Matrix, Quaternion
import bmesh
from ..operators.general_functions import get_all_collections
from ..operators.general_functions import show_message_box
from ..operators.general_functions import get_instances_collection
from ..operators.create import update_scene
from ..operators.create import switch_to_viewlayer


class MESH_OT_add_hierarchy(bpy.types.Operator):
    bl_idname = "collection.add_hierarchy"
    bl_label = "Add Hierarchy"
    bl_description = "Add collider object"
    bl_options = {"REGISTER", "UNDO"}

    collection_button: bpy.props.EnumProperty(
        name="CollectionButtons",
        description="Collection Buttons",
        items=[
            ("CreateModel", "Create Model", "Create a model collection."),
            ("CreateLink", "Create Link", "Create a link collection."),
        ],
    )  # type: ignore

class SDFG_OT_AddSceneOperator(bpy.types.Operator):
    bl_idname = "scene.add_simple"
    bl_label = "Add Scene"
    bl_description = "Add new scene"

    def execute(self, context):
        # Create a new scene
        new_scene = bpy.ops.scene.new(type="NEW")  

        # Switch to the new scene
        context.window.scene = bpy.context.scene

        # Update the list index to match the new scene
        context.window_manager.my_list_index = len(bpy.data.scenes) - 1

        # Redraw the UI to reflect the changes
        context.area.tag_redraw()

        return {"FINISHED"}

class SDFG_OT_DeleteSceneOperator(bpy.types.Operator):
    bl_idname = "scene.delete_scene"
    bl_label = "Delete Scene"
    bl_description = "Add a new scene"

    def execute(self, context):
        # Delete the currently active scene
        bpy.data.scenes.remove(bpy.context.scene)

        update_scene.is_running = True  # Temporarily disable the update function
        context.window_manager.my_list_index = context.window_manager.my_list_index - 1
        update_scene.is_running = False  # Re-enable the update function

        return {"FINISHED"}

def scene_setup():
    # Check if view layers exist and if not, create them
    if "Links" not in bpy.context.scene.view_layers:
        bpy.context.view_layer.name = "Links"

    # Check if the collection that stores instances exists and if not, create it
    instances_collection_found = False
    for collection in bpy.data.collections:
        if collection.collection_type == "InstancesCollection":
            instances_collection = collection
            instances_collection_found == True
            break

    if instances_collection_found == False:
        bpy.ops.collection.create(name=bpy.context.scene.name + "_instances_collection")
        instances_collection = bpy.data.collections[
            bpy.context.scene.name + "_instances_collection"
        ]
        if (
            instances_collection.name
            not in bpy.context.scene.collection.children.keys()
        ):
            bpy.context.scene.collection.children.link(instances_collection)
        instances_collection.collection_type = "InstancesCollection"
        # instances_collection.empty_display_size

    # Check if armature exists and if not, create it
    armature_object_exists = False
    for obj in bpy.context.scene.objects:
        if obj.object_type == "ArmatureObject":
            armature_object_exists = True
            break
    if armature_object_exists == False:
        bpy.ops.object.armature_add()
        armature_object = bpy.context.active_object
        armature_object.name = bpy.context.scene.name + "_jointrig"

        # Set object type
        armature_object.object_type = "ArmatureObject"

        # Link armature to instance collection
        instances_collection.objects.link(armature_object)
        bpy.context.collection.objects.unlink(armature_object)
    
    bpy.context.scene.tab_option = 'LINKS'

class SDFG_OT_CreateLinkCollectionsOperator(bpy.types.Operator):
    bl_idname = "scene.create_link_collections"
    bl_label = "Create Link Collections"
    bl_description = "Creates link collection and nested visual and collider collections."

    # Name for link and link subcategories
    base_name: bpy.props.StringProperty(
        name="Base Name:", description="Base name for collections", default=""
    )  # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Set base name
        base_name = self.base_name.strip()
        if not base_name:
            self.report({"ERROR"}, "Name cannot be blank")
            return {"CANCELLED"}

        # Create a new link collection and set collection type
        link_collection = bpy.data.collections.new(f"{base_name}_link")
        bpy.context.scene.collection.children.link(link_collection)
        link_collection.collection_type = "LinkCollection"

        # Create a visual collection for the link and set collection type
        visual_collection = bpy.data.collections.new(f"{base_name}_visual")
        link_collection.children.link(visual_collection)
        visual_collection.collection_type = "VisualCollection"

        # Create a colliders collection for the link and set collection type
        collider_collection = bpy.data.collections.new(f"{base_name}_colliders")
        link_collection.children.link(collider_collection)
        collider_collection.collection_type = "ColliderCollection"

        self.report(
            {"INFO"}, f"Created link, visual, and collider collections for {base_name}"
        )
        return {"FINISHED"}


class SDFG_OT_CreateFrameOperator(bpy.types.Operator):
    bl_idname = "scene.create_frame"
    bl_label = "Create Frame"
    bl_description = "Creates frame that can be used as a reference or attachment point."
    bl_options = {'REGISTER', 'UNDO'}

    frame_name: bpy.props.StringProperty(
        name="Frame Name:", description="Base name for collections", default=""
    )  # type: ignore

    def get_link_collections(self, context):
        items = []
        for coll in bpy.data.collections:
            if coll.collection_type == 'LinkCollection':
                items.append((coll.name, coll.name, ""))
        if not items:
            items.append(("None", "No Links Found", "No links available to parent to"))
        return items

    parent_link: bpy.props.EnumProperty(
        name="Parent Link",
        description="The parent link for this frame.",
        items=get_link_collections
    )  # type: ignore

    use_geometry_center: bpy.props.BoolProperty(
        name="Center to Geometry",
        description="Place the frame at the geometry center instead of the object origin",
        default=False
    )  # type: ignore

    align_to_normal: bpy.props.BoolProperty(
        name="Align to Normal",
        description="Align the frame's Z-axis to the selection surface normal (Edit Mode)",
        default=False
    )  # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        
        # Name input with _frame suffix label
        row = layout.row(align=True)
        row.prop(self, "frame_name")
        row.label(text="_frame")
        
        layout.prop(self, "parent_link")
        layout.separator()

        layout.prop(self, "use_geometry_center")

        target = context.edit_object or context.active_object
        if target and target.mode == 'EDIT':
            layout.prop(self, "align_to_normal")

    def execute(self, context):
        parent_link = self.parent_link
        frame_name = self.frame_name.strip()

        # Validation
        if not frame_name or parent_link == "None":
            self.report({"ERROR"}, "Name and Parent Link cannot be blank")
            return {"CANCELLED"}

        # Force dependency graph evaluation for accurate matrix calculation
        context.view_layer.update()

        active_obj = context.edit_object or context.active_object or context.object
        empty_name = f"{frame_name}_frame"
        
        final_empty_size = 1.0
        origin_location = Vector((0.0, 0.0, 0.0))
        rot_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))

        if active_obj and active_obj.type == 'MESH':
            # Display size fallback from object bounds
            try:
                valid_dimensions = [dim for dim in active_obj.dimensions if dim > 0.0001]
                if valid_dimensions:
                    final_empty_size = min(valid_dimensions)
            except AttributeError:
                pass

            # Helper to calculate geometry bounding center in world space
            def get_geometry_center(obj):
                if obj.bound_box:
                    bbox_center = sum((Vector(b) for b in obj.bound_box), Vector((0.0, 0.0, 0.0))) / 8.0
                    return obj.matrix_world @ bbox_center
                return obj.matrix_world.translation

            # --- EDIT MODE ---
            if active_obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(active_obj.data)
                bm.verts.ensure_lookup_table()
                bm.faces.ensure_lookup_table()
                bm.normal_update()
                
                selected_verts = [v for v in bm.verts if v.select]
                selected_faces = [f for f in bm.faces if f.select]

                if selected_verts:
                    # If geometry center is checked, compute the center of the full mesh bounds,
                    # otherwise use the median location of the current selection.
                    if self.use_geometry_center:
                        origin_location = get_geometry_center(active_obj)
                    else:
                        local_center = sum((v.co for v in selected_verts), Vector((0.0, 0.0, 0.0))) / len(selected_verts)
                        origin_location = active_obj.matrix_world @ local_center

                    # Orientation (World Z-up vs Surface Normal)
                    if self.align_to_normal:
                        if selected_faces:
                            local_normal = sum((f.normal for f in selected_faces), Vector((0.0, 0.0, 0.0)))
                        else:
                            local_normal = sum((v.normal for v in selected_verts), Vector((0.0, 0.0, 0.0)))

                        if local_normal.length > 1e-6:
                            local_normal.normalize()
                        else:
                            local_normal = Vector((0.0, 0.0, 1.0))

                        # Transform normal into world space
                        normal_matrix = active_obj.matrix_world.to_3x3().inverted().transposed()
                        world_normal = (normal_matrix @ local_normal).normalized()
                        
                        # Build orthonormal basis (Z = normal)
                        z_axis = world_normal
                        up = Vector((0.0, 1.0, 0.0)) if abs(z_axis.z) > 0.99 else Vector((0.0, 0.0, 1.0))
                        x_axis = up.cross(z_axis).normalized()
                        y_axis = z_axis.cross(x_axis).normalized()
                        
                        rot_matrix = Matrix((x_axis, y_axis, z_axis)).transposed()
                        rot_quaternion = rot_matrix.to_quaternion()
                    else:
                        # World alignment (Z straight up)
                        rot_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
                else:
                    origin_location = get_geometry_center(active_obj) if self.use_geometry_center else active_obj.matrix_world.translation
                    rot_quaternion = active_obj.matrix_world.to_quaternion()

            # --- OBJECT MODE ---
            else:
                origin_location = get_geometry_center(active_obj) if self.use_geometry_center else active_obj.matrix_world.translation
                rot_quaternion = active_obj.matrix_world.to_quaternion()

        # Create the Empty
        new_empty = bpy.data.objects.new(empty_name, None)
        new_empty.empty_display_type = 'ARROWS'
        new_empty.empty_display_size = final_empty_size
        
        # Apply transformation in world coordinates
        trans_mat = Matrix.Translation(origin_location)
        rot_mat = rot_quaternion.to_matrix().to_4x4()
        new_empty.matrix_world = trans_mat @ rot_mat
        
        new_empty.show_in_front = True
        new_empty.object_type = "FrameObject"
        new_empty.frame_parent = parent_link

        scene_collection = context.scene.collection
        
        for col in list(new_empty.users_collection):
            if col != scene_collection:
                col.objects.unlink(new_empty)

        if new_empty.name not in scene_collection.objects:
            scene_collection.objects.link(new_empty)

        return {"FINISHED"}

class SDFG_OT_CreateLinkItems(bpy.types.Operator):
    bl_idname = "scene.create_link_items"
    bl_label = "Create Link Item Collections"
    bl_description = "Creates collections for subcategories of links."

    def invoke(self, context, event):
        if context.collection.collection_type != "LinkCollection":
            show_message_box(
                message="Active collection is not a link. Please select a link collection.",
                title="Error",
                icon="INFO",
            )
            return {"CANCELLED"}

        else:
            return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        print("SOMETHING")
        return {"FINISHED"}
