import bpy
from ..ui.links_panel import SNA_UL_display_scenes_list
from ..operators.general_functions import show_message_box
from ..operators.general_functions import get_armature
from ..operators.general_functions import links_check
from ..operators.joints import link_joint_shapes



def create_link_instances(context):
    """Create instances for all links"""
    bpy.ops.object.mode_set(mode="OBJECT")
    for link_collection in bpy.context.scene.collection.children:
        if link_collection.collection_type == "LinkCollection":
            existing_instance = next(
                (
                    obj
                    for obj in bpy.data.objects
                    if obj.type == "EMPTY"
                    and obj.instance_type == "COLLECTION"
                    and obj.instance_collection == link_collection
                ),
                None,
            )

            if existing_instance is None:
                bpy.ops.object.collection_instance_add(
                    name=link_collection.name,
                    collection=link_collection.name,
                    location=(0.0, 0.0, 0.0),
                    rotation=(0.0, 0.0, 0.0),
                    scale=(0.0, 0.0, 0.0),
                )
                collection_instance = context.object
                collection_instance.lock_location[0] = True
                collection_instance.lock_location[1] = True
                collection_instance.lock_location[2] = True
                collection_instance.lock_rotation[0] = True
                collection_instance.lock_rotation[1] = True
                collection_instance.lock_rotation[2] = True
                collection_instance.lock_scale[0] = True
                collection_instance.lock_scale[1] = True
                collection_instance.lock_scale[2] = True
                collection_instance.show_instancer_for_viewport = False
                collection_instance.show_instancer_for_render = False


def switch_to_viewlayer(self, context):
    """Switches the view layer based on the active tab."""
    context = bpy.context
    scene = bpy.context.scene

    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    viewport = space
                    space.shading.use_scene_lights = False
                    space.shading.type = "MATERIAL"
                    space.shading.use_scene_world = False

    for light in bpy.context.scene.objects:
        if light.type == 'LIGHT':
            light.hide_viewport = True

    if scene.tab_option == "LINKS":
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = None
        if "Links" not in scene.view_layers:
            scene.view_layers.new("Links")
        bpy.context.window.view_layer = scene.view_layers["Links"]
        

        # Set viewlayer visibility
        viewlayer_visibility(
            view_layer_name="Links", hide_instances=True, hide_colliders=True
        )

    elif scene.tab_option == "COLLIDERS":
        """links_found, colliders_found = links_check()
        if colliders_found == False:
            scene.tab_option = "LINKS"
            show_message_box(
                message="No colliders found. Ensure there is a link with a colliders collection within it.",
                title="Error",
                icon="INFO",
            )

        elif colliders_found == True:"""
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = None
        if "Colliders" not in scene.view_layers:
            scene.view_layers.new("Colliders")
        bpy.context.window.view_layer = scene.view_layers["Colliders"]

        # Update 3D view shading to SOLID
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "SOLID"
                        space.shading.color_type = "OBJECT"

        # Set viewlayer visibility
        viewlayer_visibility(view_layer_name="Colliders")
        viewlayer_visibility(view_layer_name="Colliders", hide_instances=True)

        """bpy.context.scene.view_layers["Colliders"].layer_collection.children[
            "Scene_instances_collection"
        ].hide_viewport = True"""

    elif scene.tab_option == "JOINTS":
        link_joint_shapes(self, context)
        links_found, colliders_found = links_check()

        """# Don't switch if there are no links
        if links_found == False:
            scene.tab_option = "LINKS"
            show_message_box(
                message="No links found. Create a link first",
                title="Error",
                icon="INFO",
            )"""


        if "Joints" not in scene.view_layers:
            scene.view_layers.new("Joints")
        bpy.context.window.view_layer = scene.view_layers["Joints"]

        # Update 3D view shading to MATERIAL
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"

        # Set viewlayer visibility
        viewlayer_visibility(view_layer_name="Joints")
        viewlayer_visibility(
            view_layer_name="Joints",
            hide_colliders=True,
            disable_colliders=True,
            hide_links=True,
        )

        # Get armature object
        
        armature_object = get_armature()
        if armature_object != None:
            armature_object.select_set(True)
            bpy.context.view_layer.objects.active = armature_object

            bpy.ops.object.mode_set(mode="POSE")

    elif scene.tab_option == "MATERIALS":
        if "Materials" not in scene.view_layers:
            scene.view_layers.new("Materials")
        bpy.context.window.view_layer = scene.view_layers["Materials"]

        # Set viewlayer visibility
        viewlayer_visibility(
            view_layer_name="Materials",
                hide_instances=True, 
                hide_colliders=True
        )

    elif scene.tab_option == "LIGHTS":
        if "Lights" not in scene.view_layers:
            scene.view_layers.new("Lights")
        bpy.context.window.view_layer = scene.view_layers["Lights"]

        for light in bpy.context.scene.objects:
            if light.type == 'LIGHT':
                light.hide_viewport = False
        space.shading.type = "MATERIAL"
        space.shading.use_scene_lights = True
        space.shading.use_scene_world = True

        # Set viewlayer visibility
        viewlayer_visibility(
            view_layer_name="Lights",
                hide_instances=True, 
                hide_colliders=True
        )

    elif scene.tab_option == "EXPORT":
        # Set viewlayer visibility
        if "Export" not in scene.view_layers:
            scene.view_layers.new("Export")
        bpy.context.window.view_layer = scene.view_layers["Export"]
        viewlayer_visibility(
            view_layer_name="Export", 
                hide_links=False,
                hide_visuals=False,
                hide_colliders=False,
                disable_colliders=False,
                hide_instances=False,
                hide_lights=False
        )

def update_scene(self, context):
    # Updates the active scene when the list selection changes.
    if not update_scene.is_running: 
        update_scene.is_running = True
        print("SCENE_UPDATE")
        index = context.window_manager.my_list_index
        try:
            context.window.scene = bpy.data.scenes[index]
            context.window_manager.my_list_index = index
        except IndexError:
            pass
        update_scene.is_running = False
update_scene.is_running = False

def viewlayer_visibility(
    view_layer_name,
    hide_links=False,
    hide_visuals=False,
    hide_colliders=False,
    disable_colliders=False,
    hide_instances=False,
    hide_lights=False
):
    """Set visibility for collections in a specific view layer."""
    view_layer = bpy.context.scene.view_layers[view_layer_name]
    root_layer_collection = (
        view_layer.layer_collection
    )

    # Recursively traverse the layer_collection tree
    def set_visibility(layer_collection):
        collection_type = getattr(layer_collection.collection, "collection_type", None)
        if collection_type == "LinkCollection":
            layer_collection.hide_viewport = hide_links
        elif collection_type == "VisualCollection":
            layer_collection.hide_viewport = hide_visuals
        elif collection_type == "ColliderCollection":
            layer_collection.hide_viewport = hide_colliders
            bpy.data.collections[layer_collection.name].hide_viewport = (
                disable_colliders
            )
        elif collection_type == "InstancesCollection":
            layer_collection.hide_viewport = hide_instances

        # Recursively apply to child collections
        for child in layer_collection.children:
            set_visibility(child)


    # Start recursive visibility check from the root layer collection
    set_visibility(root_layer_collection)

