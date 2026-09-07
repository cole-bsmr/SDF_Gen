import bpy
from ..operators.create import switch_to_viewlayer
from ..operators.general_functions import get_armature
from mathutils import Vector
from bpy.props import FloatVectorProperty

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
        ("FrameObject", "Frame Object", "Object is a frame.")
    ],
    default="StandardObject",
)

def get_link_collections_for_prop(self, context):
    items = [('None', 'None', 'No Parent')]
    for coll in bpy.data.collections:
        if coll.collection_type == 'LinkCollection':
            items.append((coll.name, coll.name, f"Parent to {coll.name}"))
    return items

bpy.types.Object.frame_parent = bpy.props.EnumProperty(
    name="Frame Parent",
    description="The parent link of this frame.",
    items=get_link_collections_for_prop
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

bpy.types.Camera.is_thumbcam = bpy.props.BoolProperty(default=False)

bpy.types.Scene.links_expand = bpy.props.BoolProperty(default=True)

bpy.types.Scene.sdf_options_expand = bpy.props.BoolProperty(default=False)

bpy.types.Scene.joints_expand = bpy.props.BoolProperty(default=True)

bpy.types.Scene.utilities_advanced = bpy.props.BoolProperty(default=False)

bpy.types.Scene.export_config = bpy.props.BoolProperty(default=False)

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

bpy.types.Scene.use_relative_link_poses = bpy.props.BoolProperty(default=True)

bpy.types.Scene.zip_files = bpy.props.BoolProperty(default=True)

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

def update_move_joints(self, context):
    """Updates the move_joints property."""

    armature = get_armature()
    if armature is None or not hasattr(armature, 'pose'):
        return

    def enable_bone_constraints(armature_obj, enable):
        for pose_bone in armature_obj.pose.bones:
            for constraint in pose_bone.constraints:
                constraint.enabled = enable

    def bone_to_pose(armature_obj):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply()

    def unparent_bones(armature_obj):
        """Saves parent data to a custom property on the armature and then un-parents."""
        stored_parent_data = {}
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        for bone in armature_obj.data.edit_bones:
            parent_name = bone.parent.name if bone.parent else None
            
            stored_parent_data[bone.name] = {
                'parent': parent_name,
                'connected': bone.use_connect
            }
            
            bone.parent = None
                
        armature_obj.data['bone_parent_data'] = stored_parent_data
        
        bpy.ops.object.mode_set(mode='POSE')

    def restore_bone_parents(armature_obj):
        """Restores parent relationships."""

        print("Restoring bone parents...")

        parent_data = armature_obj.data.get('bone_parent_data')

        if not parent_data:
            print("Warning: No parent data found to restore.")
            return

        bpy.ops.object.mode_set(mode='EDIT')
        
        for bone_name, parent_info in parent_data.items():
            edit_bone = armature_obj.data.edit_bones.get(bone_name)
            
            if not edit_bone:
                continue
            
            parent_name = parent_info['parent']
            use_connect = parent_info['connected']
            
            if parent_name:
                parent_bone = armature_obj.data.edit_bones.get(parent_name)
                if parent_bone:
                    edit_bone.parent = parent_bone
                    edit_bone.use_connect = use_connect
            else:
                edit_bone.parent = None

        del armature_obj.data['bone_parent_data']
        
        bpy.ops.object.mode_set(mode='POSE')

    def enable_constraints(enable_childof):
        # Disables all 'Child Of' constraints in the scene.
        for obj in context.scene.objects:
            for constraint in obj.constraints:
                if constraint.type == 'CHILD_OF':
                    constraint.enabled = enable_childof

    def set_inverse():
        previous_selection = None
        # Store previous bone selection
        if context.active_pose_bone:
            previous_selection = context.active_pose_bone.name
        # Switch to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Iterate through all objects in the scene
        for obj in context.scene.objects:
            # Check if the object has any constraints
            if obj.constraints:
                # Iterate through the object's constraints
                for constraint in obj.constraints:
                    # Check if the constraint is a Child Of constraint
                    if constraint.type == 'CHILD_OF':
                        context.view_layer.objects.active = obj
                        # context.view_layer.objects.active = obj_inverse

                        # Set the inverse
                        bpy.ops.constraint.childof_set_inverse(constraint="Child Of", owner='OBJECT')

        armature_object = get_armature()
        if armature_object:
            context.view_layer.objects.active = armature_object
            bpy.ops.object.mode_set(mode='POSE')
            if previous_selection is not None:
                pose_bone = armature_object.pose.bones.get(previous_selection)
                if pose_bone:
                    pose_bone.select = True
                    armature_object.data.bones.active = pose_bone.bone
        
    if context.scene.move_joints == True:
        # Reset poses
        for bone in armature.pose.bones:
            bone.location = (0, 0, 0)
            bone.rotation_euler = (0, 0, 0)
        # Unlink objects from bones
        enable_constraints(False)

        # Disable bone constraints
        enable_bone_constraints(armature, False)

        # Unlink bones
        unparent_bones(armature)
    
    if context.scene.move_joints == False:
        bone_to_pose(armature)
        restore_bone_parents(armature)
        enable_constraints(True)
        enable_bone_constraints(armature, True)
        set_inverse()

bpy.types.Scene.move_joints = bpy.props.BoolProperty(
    name="Move Joints",
    description="Toggles the joint constraints and parent/child relationships so that joints can be moved.",
    default=False,
    update=update_move_joints,
)

def update_pose_bone_location(self, context):
    bpy.context.active_pose_bone.location = bpy.context.active_pose_bone.bone.matrix_local.inverted() @ bpy.context.active_pose_bone.pose_bone_location
    return

bpy.types.PoseBone.pose_bone_location = FloatVectorProperty(
    name="Pose Bone Location",
    description="A custom XYZ vector for moving pose bones",
    default=(0.0, 0.0, 0.0),
    subtype='TRANSLATION',
    unit='LENGTH',
    update=update_pose_bone_location
)

# Alpha Wrap Collider Properties
bpy.types.Scene.alpha_wrap_expand = bpy.props.BoolProperty(
    name="Alpha Wrap Expand",
    description="Expand or collapse the Alpha Wrap settings section",
    default=True,
)

# Default values for Alpha Wrap modes
DEFAULT_ALPHA_PERCENTAGE = 2.0
DEFAULT_OFFSET_PERCENTAGE = 0.5
DEFAULT_ALPHA_ABSOLUTE = 0.02
DEFAULT_OFFSET_ABSOLUTE = 0.005

_is_updating_alpha_wrap_mode = False


def _on_alpha_wrap_alpha_update(self, context):
    global _is_updating_alpha_wrap_mode
    if _is_updating_alpha_wrap_mode:
        return
    mode = getattr(self, "alpha_wrap_mode", "PERCENTAGE")
    if mode == "PERCENTAGE":
        self.alpha_wrap_alpha_percentage = self.alpha_wrap_alpha
    else:
        self.alpha_wrap_alpha_absolute = self.alpha_wrap_alpha


def _on_alpha_wrap_offset_update(self, context):
    global _is_updating_alpha_wrap_mode
    if _is_updating_alpha_wrap_mode:
        return
    mode = getattr(self, "alpha_wrap_mode", "PERCENTAGE")
    if mode == "PERCENTAGE":
        self.alpha_wrap_offset_percentage = self.alpha_wrap_offset
    else:
        self.alpha_wrap_offset_absolute = self.alpha_wrap_offset


def _on_alpha_wrap_mode_update(self, context):
    global _is_updating_alpha_wrap_mode
    _is_updating_alpha_wrap_mode = True
    try:
        if self.alpha_wrap_mode == "PERCENTAGE":
            self.alpha_wrap_alpha = self.alpha_wrap_alpha_percentage
            self.alpha_wrap_offset = self.alpha_wrap_offset_percentage
        else:
            self.alpha_wrap_alpha = self.alpha_wrap_alpha_absolute
            self.alpha_wrap_offset = self.alpha_wrap_offset_absolute
    finally:
        _is_updating_alpha_wrap_mode = False


# Stored last-entered values per mode
bpy.types.Scene.alpha_wrap_alpha_percentage = bpy.props.FloatProperty(
    name="Alpha (Percentage)",
    description="Stored Alpha value for Percentage mode",
    default=DEFAULT_ALPHA_PERCENTAGE,
    soft_min=0.0001,
    precision=4,
)

bpy.types.Scene.alpha_wrap_offset_percentage = bpy.props.FloatProperty(
    name="Offset (Percentage)",
    description="Stored Offset value for Percentage mode",
    default=DEFAULT_OFFSET_PERCENTAGE,
    soft_min=0.0001,
    precision=4,
)

bpy.types.Scene.alpha_wrap_alpha_absolute = bpy.props.FloatProperty(
    name="Alpha (Absolute)",
    description="Stored Alpha value for Absolute mode",
    default=DEFAULT_ALPHA_ABSOLUTE,
    soft_min=0.0001,
    precision=4,
)

bpy.types.Scene.alpha_wrap_offset_absolute = bpy.props.FloatProperty(
    name="Offset (Absolute)",
    description="Stored Offset value for Absolute mode",
    default=DEFAULT_OFFSET_ABSOLUTE,
    soft_min=0.0001,
    precision=4,
)

bpy.types.Scene.alpha_wrap_alpha = bpy.props.FloatProperty(
    name="Alpha",
    description=(
        "Probe ball radius / feature resolution: controls how tightly the wrap conforms to the surface.\n"
        "Smaller values capture finer geometric details, cavities, and indentations.\n"
        "Larger values bridge across holes and gaps, creating a smoother outer shell.\n"
        "Performance: computation duration scales sharply with smaller Alpha (~3x-8x longer when halved),\n"
        "as 3D spatial cell and facet counts scale with (1 / Alpha^2) to (1 / Alpha^3).\n"
        "Values between 1.0% and 3.0% provide an optimal balance of speed and fidelity.\n"
        "Must be strictly positive (> 0) as required by CGAL 3D Alpha Wrapping.\n"
        "Expressed as % of bounding box diagonal (Percentage mode, default: 2.0%) or meters (Absolute mode, default: 0.02m)"
    ),
    default=DEFAULT_ALPHA_PERCENTAGE,
    soft_min=0.0001,
    precision=4,
    update=_on_alpha_wrap_alpha_update,
)

bpy.types.Scene.alpha_wrap_offset = bpy.props.FloatProperty(
    name="Offset",
    description=(
        "Offset distance: thickness added outward from the input surface.\n"
        "Guarantees the collision wrap strictly encloses the visual mesh with at least this margin.\n"
        "Also thickens thin walls and non-manifold geometry into a solid watertight volume.\n"
        "Must be strictly positive (> 0) as required by CGAL 3D Alpha Wrapping.\n"
        "Expressed as % of bounding box diagonal (Percentage mode, default: 0.5%) or meters (Absolute mode, default: 0.005m)"
    ),
    default=DEFAULT_OFFSET_PERCENTAGE,
    soft_min=0.0001,
    precision=4,
    update=_on_alpha_wrap_offset_update,
)

bpy.types.Scene.alpha_wrap_mode = bpy.props.EnumProperty(
    name="Mode",
    description="Coordinate units used for Alpha and Offset values",
    items=[
        (
            "PERCENTAGE",
            "Percentage",
            "Values are calculated as a percentage of the object bounding box diagonal. "
            "Scale-independent and recommended for objects of varying sizes",
        ),
        (
            "ABSOLUTE",
            "Absolute",
            "Values are in absolute metric units (meters). "
            "Useful when exact physical tolerances or clearances are required",
        ),
    ],
    default="PERCENTAGE",
    update=_on_alpha_wrap_mode_update,
)

bpy.types.Scene.alpha_wrap_decimate_angle = bpy.props.FloatProperty(
    name="Planar Angle",
    description=(
        "Planar decimation angle limit in degrees (uses Blender's built-in Decimate Planar modifier):\n"
        "Dissolves adjacent coplanar faces meeting at a dihedral angle below this threshold.\n"
        "Significantly reduces polygon count on flat surfaces while cleanly preserving sharp edges.\n"
        "Set to 0 to disable planar decimation"
    ),
    default=5.0,
    min=0.0,
    max=180.0,
    precision=2,
)

bpy.types.Scene.alpha_wrap_decimate_faces = bpy.props.IntProperty(
    name="Target Faces",
    description=(
        "Target face count for Quadric Edge Collapse decimation.\n"
        "Further simplifies the mesh to the specified maximum number of triangular faces.\n"
        "Applied after planar angle decimation.\n"
        "Set to 0 to disable and keep all faces from the planar decimation step"
    ),
    default=0,
    min=0,
)

bpy.types.Scene.alpha_wrap_per_obj = bpy.props.BoolProperty(
    name="Per Object",
    description=(
        "Multi-selection handling:\n"
        "Enabled: creates an individual Alpha Wrap collider for each selected mesh or child mesh.\n"
        "Disabled: merges all selected meshes into a single unified watertight wrap enclosing them all"
    ),
    default=True,
)

# Alpha Wrap Async State
bpy.types.WindowManager.alpha_wrap_in_progress = bpy.props.BoolProperty(
    name="Alpha Wrap In Progress",
    description="Indicates if an alpha wrap operation is currently running in the background",
    default=False,
)

bpy.types.WindowManager.alpha_wrap_status = bpy.props.StringProperty(
    name="Alpha Wrap Status",
    description="Current status of the background alpha wrap operation",
    default="",
)