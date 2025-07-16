import bpy
import webbrowser


def get_all_collections():
    model_scene = bpy.context.scene
    all_collections = []

    def recursive_get(collection):
        # Add the collection to the list
        all_collections.append(collection)

        # Recurse through all child collections
        for child in collection.children:
            recursive_get(child)

    # Start recursion from the scene collections
    for collection in model_scene.collection.children:
        recursive_get(collection)
    return all_collections

def show_message_box(message="", title="Message Box", icon="INFO"):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

def links_check():
    all_collections = get_all_collections()

    # Check for link collections
    links_found = False
    colliders_found = False

    # Return false if collections are not found
    if len(bpy.context.scene.collection.children) != 0:
        for collection in all_collections:
            if collection.collection_type == "LinkCollection":
                links_found = True
                for collection_child in collection.children:
                    if collection_child.collection_type == "ColliderCollection":
                        colliders_found = True

    return links_found, colliders_found

def get_armature():
    armature_object = None
    for obj in bpy.context.scene.objects:
        if obj.object_type == "ArmatureObject":
            armature_object = obj
            break
    return armature_object

def get_instances_collection():
    for collection in bpy.context.scene.collection.children:
        if collection.collection_type == "InstancesCollection":
            instances_collection = collection
            break
    return instances_collection

def get_riginstance_objects():
    link_instance_objects = []
    instances_collection = get_instances_collection()
    for obj in instances_collection.objects:
        if obj.object_type == "LinkInstanceObject":
            link_instance_objects.append(obj)
    return link_instance_objects

class ExternalLinkOperator(bpy.types.Operator):
    bl_idname = "wm.open_external_link"
    bl_label = "Open STEPper Link"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        webbrowser.open("https://ambient.gumroad.com/l/stepper")
        return {'FINISHED'}
