import bpy
from ..operators.create import switch_to_viewlayer

# from ..operators.colliders import update_face_snap
# from ..operators.colliders import update_visibility
# from ..operators.colliders import update_collider_margin_thickness
# Properties


def update_face_snap(self, context):
    """Updates the face_snap property which controls the snap settings for the 'Scale Cage' tool."""

    if self.face_snap == True:
        # Turn on snap and set snap settings to enable snapping to face
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements_base = {"FACE"}
        bpy.context.scene.tool_settings.use_snap_scale = True
        bpy.context.scene.tool_settings.use_snap_translate = True
        bpy.context.scene.transform_orientation_slots[0].type = "LOCAL"

    if self.face_snap == False:
        # Turn off snap
        bpy.context.scene.tool_settings.use_snap = False

bpy.types.Scene.face_snap = bpy.props.BoolProperty(
    name="Face Snap",
    description="Toggles face snapping on and off. For use with the 'Scale Cage' tool.",
    default=False,
    update=update_face_snap,
)

def update_visibility(self, context):
    """Toggles the visibility of objects depending on object_type"""

    if self.collider_visibility == True:
        for obj in bpy.data.objects:
            if obj.object_type == "ColliderObject":
                obj.hide_set(False)
    elif self.collider_visibility == False:
        for obj in bpy.data.objects:
            if obj.object_type == "ColliderObject":
                obj.hide_set(True)

bpy.types.WindowManager.collider_visibility = bpy.props.BoolProperty(
    name="Collider visibility",
    description="Hides or shows all the collider objects in the file.",
    default=True,
    update=update_visibility,
)

def update_collider_margin_thickness(self, context):
    """Updates all 'Collider Margin' modifiers in the active scene."""

    thickness = context.scene.collider_margin_thickness
    for obj in context.scene.objects:
        for mod in obj.modifiers:
            if mod.type == "SOLIDIFY" and mod.name == "Collider Margin":
                mod.thickness = thickness

bpy.types.Scene.collider_margin_thickness = bpy.props.FloatProperty(
    name="Collider Margin Thickness",
    description="Thickness for the collider margin modifier",
    default=0.0,
    min=0.0,
    update=update_collider_margin_thickness,
)

bpy.types.Scene.tab_option = bpy.props.EnumProperty(
    name="Tab Option",
    items=[
        ("UTILITIES", "Utilities", "Utilities Tab", "MODIFIER", -1),
        ("LINKS", "Links", "Links Tab", "LINKED", 0),
        ("COLLIDERS", "Colliders", "Colliders Tab", "MOD_SUBSURF", 1),
        ("JOINTS", "Joints", "Joints Tab", "CONSTRAINT_BONE", 2),
        ("SENSORS", "Sensors", "Sensors Tab", "PROP_ON", 3),
        ("MATERIALS", "Materials", "Materials Tab", "MATERIAL", 4),
        ("LIGHTS", "Lights", "Lights Tab", "LIGHT", 5),
        ("RENDER", "Render/thumbnail", "Render Tab", "VIEW_CAMERA_UNSELECTED", 6),
        ("EXPORT", "Export", "Export Tab", "FILEBROWSER", 7)
    ],
    default="LINKS",  # Default tab to show
    update=switch_to_viewlayer,
)

bpy.types.WindowManager.mesh_file_format = bpy.props.EnumProperty(
    name="Export Format",
    items=[
        ("GLB", "GLB", "Binary GLTF format"),
        ("GLTF", "GLTF", "GLTF format"),
    ],
    default="GLB",
)

bpy.types.Collection.collection_type = bpy.props.EnumProperty(
    name="Collection Type",
    description="Stores the type of collection",
    items=[
        (
            "StandardCollection",
            "Standard Collection",
            "Collection is a standard Blender collection.",
        ),
        ("LinkCollection", "Link Collection", "Collection is a link."),
        ("VisualCollection", "Visual Collection", "Collection contains visuals."),
        ("ColliderCollection", "Collider Collection", "Collection contains colliders."),
        ("InstanceCollection", "Instance Collection", "Collection is an instance."),
        (
            "InstancesCollection",
            "Instances Collection",
            "Collection that stores instances",
        ),
    ],
    default="StandardCollection",
)

bpy.types.Object.object_type = bpy.props.EnumProperty(
    name="Object Type",
    description="The type of object",
    items=[
        ("StandardObject", "Standard Object", "Object has no special properties."),
        ("ColliderObject", "Collider Object", "Object is a collider."),
        ("ArmatureObject", "Armature Object", "Object is an armature."),
        ("LinkInstanceObject", "Link Instance Object", "Object is a link instance."),
    ],
    default="StandardObject",
)

bpy.types.Object.collider_type = bpy.props.EnumProperty(
    name="Collider Type",
    description="The type of collider a collider object is",
    items=[
        ("NotCollider", "Not Collider", "Object has no collision properties."),
        ("BoxCollider", "Box Collider", "Collider is a box."),
        ("CylinderCollider", "Cylinder Collider", "Collider is a cylinder."),
        ("SphereCollider", "Sphere Collider", "Collider is a sphere."),
        ("ConeCollider", "Cone Collider", "Collider is a cone."),
        ("PlaneCollider", "Plane Collider", "Collider is a plane."),
        ("MeshCollider", "Mesh Collider", "Collider is a mesh"),
    ],
    default="NotCollider",
)

bpy.types.Scene.links_expand = bpy.props.BoolProperty(default=True)

bpy.types.Scene.sdf_options_expand = bpy.props.BoolProperty(default=False)

bpy.types.Scene.joints_expand = bpy.props.BoolProperty(default=True)

bpy.types.Scene.utilities_advanced = bpy.props.BoolProperty(default=False)

bpy.types.Scene.export_config = bpy.props.BoolProperty(default=True)

bpy.types.Scene.author_name = bpy.props.StringProperty(
    name="Author Name",
    description="Enter the name of the author of this model",
    default=""
)

bpy.types.Scene.author_email = bpy.props.StringProperty(
    name="Author Email",
    description="Enter the email of the author of this model",
    default=""
)

bpy.types.Scene.model_description = bpy.props.StringProperty(
    name="Model description",
    description="Enter a description of this model",
    default=""
)

bpy.types.Scene.relative_link_poses = bpy.props.BoolProperty(default=False)

def update_collider_radius(self, context):
    """Updates the collider_radius property."""
    
    obj = context.object
    obj.dimensions.x = obj.collider_radius
    obj.dimensions.y = obj.collider_radius

bpy.types.Object.collider_radius = bpy.props.FloatProperty(
    name="Radius of colliders",
    description="Adjusts the radius of round collider shapes",
    default=0.0,
    min=0.001,
    update=update_collider_radius,
)