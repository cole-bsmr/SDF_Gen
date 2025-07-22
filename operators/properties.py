import bpy
from ..operators.create import switch_to_viewlayer
from ..operators.general_functions import get_armature
from mathutils import Vector

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

bpy.types.Scene.use_relative_link_poses = bpy.props.BoolProperty(default=False)

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

    def enable_bone_constraints(context, enable_bone_constraints):
        for pose_bone in context.object.pose.bones:
            for constraint in pose_bone.constraints:
                constraint.enabled = enable_bone_constraints

    def bone_to_pose(context):
        # bpy.ops.object.mode_set(mode='EDIT')
        armature = context.object
        for pose_bone in armature.pose.bones:
            bpy.ops.pose.armature_apply(selected=False)

    def unparent_bones(context):
        """Saves parent data to a custom property on the armature and then un-parents."""
        stored_parent_data = {}
        
        armature = context.object
        bpy.ops.object.mode_set(mode='EDIT')
        
        for bone in armature.data.edit_bones:
            parent_name = bone.parent.name if bone.parent else None
            

            stored_parent_data[bone.name] = {
                'parent': parent_name,
                'connected': bone.use_connect
            }
            
            bone.parent = None
                
        armature.data['bone_parent_data'] = stored_parent_data
        
        bpy.ops.object.mode_set(mode='POSE')

    def restore_bone_parents(context):
        """Restores parent relationships."""

        print("Restoring bone parents...")
        armature = context.object

        parent_data = armature.data.get('bone_parent_data')

        if not parent_data:
            print("Warning: No parent data found to restore.")
            return

        bpy.ops.object.mode_set(mode='EDIT')
        
        for bone_name, parent_info in parent_data.items():
            edit_bone = armature.data.edit_bones.get(bone_name)
            
            if not edit_bone:
                continue
            
            parent_name = parent_info['parent']
            use_connect = parent_info['connected']
            
            if parent_name:
                parent_bone = armature.data.edit_bones.get(parent_name)
                if parent_bone:
                    edit_bone.parent = parent_bone
                    edit_bone.use_connect = use_connect
            else:
                edit_bone.parent = None

        del armature.data['bone_parent_data']
        
        bpy.ops.object.mode_set(mode='POSE')

    def enable_constraints(context, enable_childof):
        # Disables all 'Child Of' constraints in the scene.
        for obj in context.scene.objects:
            for constraint in obj.constraints:
                if constraint.type == 'CHILD_OF':
                    constraint.enabled = enable_childof

    def set_inverse(context):
        previous_selection = None
        # Store previous bone selection
        if bpy.context.active_pose_bone:
            previous_selection = bpy.context.active_pose_bone.name
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
                        bpy.context.view_layer.objects.active = obj
                        # bpy.context.view_layer.objects.active = obj_inverse

                        # Set the inverse
                        bpy.ops.constraint.childof_set_inverse(constraint="Child Of", owner='OBJECT')

        armature_object = get_armature()
        bpy.context.view_layer.objects.active = armature_object
        bpy.ops.object.mode_set(mode='POSE')
        if previous_selection != None:
            pose_bone = armature_object.pose.bones.get(previous_selection)
            pose_bone.bone.select = True
            armature_object.data.bones.active = pose_bone.bone
        
    if bpy.context.scene.move_joints == True:
        # Reset poses
        for bone in bpy.context.active_object.pose.bones:
            bone.location = (0, 0, 0)
            bone.rotation_euler = (0, 0, 0)
        # Unlink objects from bones
        enable_constraints(context, False)

        # Disable bone constraints
        enable_bone_constraints(context, False)

        # Unlink bones
        unparent_bones(context)
    
    if bpy.context.scene.move_joints == False:
        bone_to_pose(context)
        restore_bone_parents(context)
        enable_constraints(context, True)
        enable_bone_constraints(context, True)
        set_inverse(context)

bpy.types.Scene.move_joints = bpy.props.BoolProperty(
    name="Move Joints",
    description="Toggles the joint constraints and parent/child relationships so that joints can be moved.",
    default=False,
    update=update_move_joints,
)