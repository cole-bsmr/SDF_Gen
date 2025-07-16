import bpy
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
