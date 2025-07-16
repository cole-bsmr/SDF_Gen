import bpy
import bpy
import bmesh
import mathutils

class SDFG_OT_UtilitiesOperator(bpy.types.Operator):
    """Operator for utilities panel buttons."""
    
    bl_idname = "scene.utility_operator"
    bl_label = "Utilities"
    bl_options = {"REGISTER", "UNDO"}
    
    # One type for each button in the utilities panel
    utility_type: bpy.props.EnumProperty(
        name="Utility Type",
        description="Utility Type",
        items=[
            ('SeparateLoose', "Separate by Loose", "Separate by loose parts."),
            ('SeparateMaterial', "Separate by Material", "Separate by material."),
            ('CleanMesh', "Clean up Mesh", "Clean up imported CAD mesh.")
        ],
    ) # type: ignore
    
    def separate_mesh(self, separate_type):
        
        # Set object to 'EDIT' mode.
        if not bpy.context.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        # Set selection mode to face and select all.
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')

        # Separate by loose parts.
        bpy.ops.mesh.separate(type=separate_type)

        # Return object to 'OBJECT' mode.
        bpy.ops.object.mode_set(mode='OBJECT')
        
    def clean_mesh(self):
        selected_objects = bpy.context.selected_objects
        meshes = [obj for obj in selected_objects if obj.type == 'MESH']
        empties = [obj for obj in selected_objects if obj.type == 'EMPTY']

        # Process meshes
        for obj in meshes:
            print(f"Imported new object: {obj.name}")

            # Make single user (direct data manipulation)
            if obj.data.users > 1:
                obj.data = obj.data.copy()

            # Clear hierarchy
            obj.parent = None
            obj.matrix_parent_inverse.identity()

            # Apply transforms (location and scale)
            obj.location = (0, 0, 0)
            obj.scale = (1, 1, 1)
            obj.data.transform(obj.matrix_world)
            obj.matrix_world.identity()

        # Remove empty objects (batch removal)
        for obj in empties:
            print(f"Imported empty: {obj.name}")
            bpy.data.objects.remove(obj)

        #Redraw viewport
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    
    def execute(self, context):
        # Separate by Loose Parts
        if self.utility_type == 'SeparateLoose':
            separate_type = 'LOOSE'
            self.separate_mesh( separate_type)
        
        # Separate by Materials
        elif self.utility_type == 'SeparateMaterial':
            separate_type = 'MATERIAL'
            self.separate_mesh(separate_type)
            
        elif self.utility_type == 'CleanMesh':
            self.clean_mesh()
        
        return {'FINISHED'}
    
class SDFG_OT_Convert(bpy.types.Operator):
    bl_idname = "scene.convert_collections"
    bl_label = "Convert"

    def execute(self, context):
        for collection in bpy.data.collections:
            if "_link" in collection.name:
                collection.collection_type = 'LinkCollection'
            elif "_visual" in collection.name:
                collection.collection_type = 'VisualCollection'
            elif "_colliders" in collection.name:
                collection.collection_type = 'ColliderCollection'

        for obj in bpy.data.objects:
            if "collider" in obj.name:
                obj.object_type = 'ColliderObject'
            if "_box" in obj.name:
                obj.collider_type = 'BoxCollider'
            if "_cylinder" in obj.name:
                obj.collider_type = 'CylinderCollider'
            if "_sphere" in obj.name:
                obj.collider_type = 'SphereCollider'
            if "_cone" in obj.name:
                obj.collider_type = 'ConeCollider'
            if "_plane" in obj.name:
                obj.collider_type = 'PlaneCollider'
        return {"FINISHED"}

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

visual_volume: bpy.props.FloatProperty(
    name="joint Location",
    description="Set the location of the joint",
    default=(0.0, 0.0, 0.0),
    ) # type: ignore

bpy.types.Scene.visual_volume = bpy.props.FloatProperty(
    name="joint Location",
    description="Set the location of the joint",
    default=0.1,
    min=0.0001,
    step=0.001,
    precision=4
)

class SDFG_OT_SelectSmallParts(bpy.types.Operator):
    bl_idname = "scene.select_small_parts"
    bl_label = "Select Small Parts"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            for collection in obj.users_collection:
                if collection.collection_type == 'VisualCollection':
                    volume = get_mesh_volume(obj)
                    print (obj.name)
                    print(volume)
                    if volume <= context.scene.visual_volume:
                        obj.select_set(True)

        return {'FINISHED'}
                
