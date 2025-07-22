import bpy
import os
import xml.dom.minidom
import shutil
import re
import textwrap
from mathutils import Vector
from ..operators.general_functions import get_all_collections
from ..operators.general_functions import get_armature

bpy.types.WindowManager.export_in_progress = bpy.props.BoolProperty(default=False)

bpy.types.WindowManager.sdf_export_file_path = bpy.props.StringProperty(
    name="Export File Path",
    description="Select the file path to export the SDF file",
    subtype="DIR_PATH",
    default="//sdf_exports/"
)

class SDF_OT_export_sdf(bpy.types.Operator):
    bl_idname = "sdf.export_sdf"
    bl_label = "Export SDF"
    bl_description = "Exports scenes to SDF files"
    bl_options = {"REGISTER", "UNDO"}

    path = bpy.context.window_manager.sdf_export_file_path

    def make_sdf_folder(self, model_name):
        self.path = bpy.context.window_manager.sdf_export_file_path
        folder_path = bpy.path.abspath(os.path.join(self.path, model_name))
         # Check if the folder exists
        if os.path.exists(folder_path):
            # Clear the folder's contents without deleting the folder itself
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # Delete the file or symbolic link
                    elif os.path.isdir(file_path):
                        shutil.rmtree(
                            file_path
                        )  # Delete the directory and its contents
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            # If the folder doesn't exist, create it
            os.makedirs(folder_path)

        return folder_path

    def write_to_sdf(self, sdf_file_path, write_text):
        with open(sdf_file_path, "a") as file:
            file.write(write_text)

    def export_joints(self, sdf_file_path, use_relative_link_poses):
        armature = get_armature()
        print(bpy.context.scene, armature)
        if armature: 
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='POSE')
            print("Working Mode OG", bpy.context.mode)
            print(bpy.context.mode)
            for pose_bone in armature.pose.bones:
                # Switch to EDIT mode to get correct bone data                
                bpy.ops.object.mode_set(mode='EDIT')
                edit_bone = (armature.data.edit_bones[pose_bone.name])
                direction_vector = edit_bone.tail - edit_bone.head
                direction_vector.normalize()
                formatted_direction = f"{round(direction_vector.x, 4)} {round(direction_vector.y, 4)} {round(direction_vector.z, 4)}"

                parent_name = pose_bone.joint_grp.sdf_parent_link
                child_name = pose_bone.joint_grp.child_link
                
                joint_type = pose_bone.joint_grp.joint_type.replace("Joint", "").lower()
                write_text = (f"\n<joint name=\"{pose_bone.name}\" type=\"{joint_type}\">\n")
                if use_relative_link_poses:
                    previous_bone_name = get_joint_name(parent_name)
                    
                    if previous_bone_name is None:
                        pose_string = f"  <pose relative_to='{parent_name}'/>\n"
                    else:
                        edit_previous_bone = (armature.data.edit_bones[previous_bone_name])
                        position_vector = edit_bone.head - edit_previous_bone.head
                        relative_to_location = f"{round(position_vector.x, 4)} {round(position_vector.y, 4)} {round(position_vector.z, 4)} 0 0 0"
                        pose_string = f"  <pose relative_to='{parent_name}'>{relative_to_location}</pose>\n"
                    write_text += (f"{pose_string}")

                # Switch back to POSE mode to write SDF
                bpy.ops.object.mode_set(mode='POSE')
                write_text += (
                    f"  <parent>{parent_name}</parent>\n"
                    f"  <child>{child_name}</child>\n"
                    )

                if pose_bone.joint_grp.joint_type in {'RevoluteJoint', 'FixedJoint', 'PrismaticJoint'}:
                    write_text += (
                        f"  <axis>\n"
                        f"    <xyz>{formatted_direction}</xyz>\n"
                        )

                if pose_bone.joint_grp.joint_type == 'RevoluteJoint' and pose_bone.joint_grp.revolute_continuous == False:
                    write_text += (
                        f"      <limit>\n"
                        f"        <lower>{pose_bone.joint_grp.revolute_min}</lower>\n"
                        f"        <upper>{pose_bone.joint_grp.revolute_max}</upper>\n"
                        f"      </limit>\n"
                        )
                    
                elif pose_bone.joint_grp.joint_type == 'RevoluteJoint' and pose_bone.joint_grp.revolute_continuous == True:
                    write_text += (
                        f"    <limit>\n"
                        f"      <lower>-1.0e+9</lower>\n"
                        f"      <upper>1.0e+9</upper>\n"
                        f"    </limit>\n"
                        )

                elif pose_bone.joint_grp.joint_type == 'PrismaticJoint':
                    write_text += (
                        f"      <limit>\n"
                        f"        <lower>{round(pose_bone.joint_grp.prismatic_min, 6)}</lower>\n"
                        f"        <upper>{round(pose_bone.joint_grp.prismatic_max, 6)}</upper>\n"
                        f"      </limit>\n"
                        )

                if pose_bone.joint_grp.joint_type in {'RevoluteJoint', 'FixedJoint', 'PrismaticJoint'}:
                    write_text += (
                        f"  </axis>\n"
                        )

                if pose_bone.joint_grp.joint_type in {'RevoluteJoint', 'FixedJoint', 'PrismaticJoint'}:
                    write_text += (
                        f"</joint>"
                        )
                    self.write_to_sdf(sdf_file_path, write_text)

        # Switch to OBJECT mode to continue SDF generation
        bpy.ops.object.mode_set(mode='OBJECT')
        print("Joints Exported")

    def export_lights(self, sdf_file_path, light):

        if light.data.type == 'POINT':
            light_type = 'point'
            range = light.data.shadow_soft_size
        if light.data.type == 'SPOT':
            light_type = 'spot'
            range = light.data.cutoff_distance
        if light.data.type == 'SUN':
            light_type = 'directional'
            range = 10
        if light.data.type == 'AREA':
            return

        write_text = textwrap.dedent(f"""
            <light type="{light_type}" name="{light.name}">
                <pose>{round(light.location.x, 6)} {round(light.location.y, 6)} {round(light.location.z, 6)} {round(light.rotation_euler.x, 6)} {round(light.rotation_euler.y, 6)} {round(light.rotation_euler.z, 6)}</pose>
                <intensity>{light.data.energy}</intensity>
                <diffuse>{light.color[0], light.color[1], light.color[2], light.color[3]}</diffuse>
                <cast_shadows>{light.data.use_shadow}</cast_shadows>
                <specular>{light.data.specular_factor}, {light.data.specular_factor}, {light.data.specular_factor}</specular>
                <attenuation>
                  <range>{range}</range>
                  <linear>0.0</linear>
                  <constant>1.0</constant>
                  <quadratic>1.0</quadratic>
            """)
        if light_type == 'spot':
            write_text += textwrap.dedent(f"""
                    <outer_angle>{round(light.data.spot_size, 3)}</outer_angle>
                    <falloff>{round(light.data.spot_blend, 3)}</falloff>
                """)
                
        write_text += textwrap.dedent(f"""
                </attenuation>
            </light>"""
        )

        self.write_to_sdf(sdf_file_path, write_text)

    def loop_links(self, model_scene, all_collections, sdf_file_path, folder_path, use_relative_link_poses):
        all_collections = get_all_collections()
        link_translate = Vector((0.0, 0.0, 0.0))
        joined_translate = Vector((0.0, 0.0, 0.0))
        for collection in all_collections:
            if collection.collection_type == "LinkCollection":
                link_collection = collection

                write_text = f'\n<link name ="{collection.name}">'
                self.write_to_sdf(sdf_file_path, write_text)

                if link_collection.children:
                    for collection in link_collection.children:
                        if (
                            collection.collection_type == "VisualCollection"
                            and collection.all_objects
                        ):
                            for visual_mesh in collection.all_objects:
                                visual_mesh.select_set(True)

                            bpy.ops.object.duplicate()
                            bpy.context.view_layer.objects.active = (
                                bpy.context.selected_objects[0]
                            )
                            bpy.ops.object.join()
                            joined_obj = bpy.context.active_object
                            bpy.ops.object.select_all(action="DESELECT")
                            joined_obj.select_set(True)

                            # bone_location = get_joint_location(link_collection.name)
                            previous_joint_name = get_previous_bone_name(link_collection.name)
                            
                            
                            joined_translate = Vector((0.0, 0.0, 0.0))
                            if previous_joint_name != None:
                                bone_location = get_joint_location_from_name(previous_joint_name)
                                if use_relative_link_poses:
                                    write_text = (
                                        f"\n<pose relative_to='{previous_joint_name}'/>\n"
                                    )
                                else:
                                    write_text = (f'\n<pose>{round(bone_location.x, 6)} {round(bone_location.y, 6)} {round(bone_location.z, 6)} 0.0 0.0 0.0</pose>\n')
                                self.write_to_sdf(sdf_file_path, write_text)

                                joined_translate = -bone_location
                                joined_obj.location += joined_translate
                                # link_translate = joined_translate

                            visual_mesh_name = collection.name.replace(".", "")

                            # GLB Export
                            if bpy.context.window_manager.mesh_file_format == "GLB":
                                file_extension = ".glb"
                                bpy.ops.export_scene.gltf(
                                    filepath=os.path.join(
                                        folder_path, visual_mesh_name + file_extension
                                    ),
                                    check_existing=False,
                                    export_format="GLB",
                                    export_texcoords=True,
                                    export_normals=True,
                                    export_materials="EXPORT",
                                    use_selection=True,
                                    export_yup=False,
                                    export_apply=True,
                                    export_animations=False,
                                    export_morph=False,
                                )
                            # GLTF Export
                            if bpy.context.window_manager.mesh_file_format == "GLTF":
                                file_extension = ".gltf"
                                bpy.ops.export_scene.gltf(
                                    filepath=os.path.join(
                                        folder_path, visual_mesh_name + file_extension
                                    ),
                                    check_existing=False,
                                    export_format="GLTF_SEPARATE",
                                    export_texcoords=True,
                                    export_normals=True,
                                    export_materials="EXPORT",
                                    use_selection=True,
                                    export_yup=False,
                                    export_apply=True,
                                    export_animations=False,
                                    export_morph=False,
                                )

                            visual_mesh_name = collection.name.replace(".", "")

                            write_text = (
                                f'\n<visual name ="{collection.name}">\n'
                                f"  <geometry>\n"
                                f"    <mesh>\n"
                                f"      <uri>{visual_mesh_name}{file_extension}</uri>\n"
                                f"    </mesh>\n"
                                f"  </geometry>\n"
                                f"</visual>"
                            )
                            self.write_to_sdf(sdf_file_path, write_text)
                            bpy.data.objects.remove(joined_obj)

                if link_collection.children:
                    for collection in link_collection.children:
                        if (
                            collection.collection_type == "ColliderCollection"
                            and collection.all_objects
                        ):
                            for collider_object in collection.all_objects:

                                # Select object
                                collider_object.select_set(True)

                                # Set origin to zero
                                bpy.ops.object.origin_set(
                                    type="ORIGIN_GEOMETRY", center="BOUNDS"
                                )

                                # Deselect all objects
                                bpy.ops.object.select_all(action="DESELECT")

                                # Account for link translation in pose of collision
                                collider_location = collider_object.location + joined_translate
                                print(collider_location)

                                write_text = (
                                    f'\n<collision name="{collider_object.name}">'
                                )

                                if collider_object.collider_type != "MeshCollider":
                                    write_text += (
                                        f"\n  <pose>{round(collider_location.x, 6)} {round(collider_location.y, 6)} {round(collider_location.z, 6)} {round(collider_object.rotation_euler.x, 6)} {round(collider_object.rotation_euler.y, 6)} {round(collider_object.rotation_euler.z, 6)}</pose>"
                                        f"\n  <geometry>"
                                    )
                                # Check if the object is a Mesh Collider"
                                if collider_object.collider_type == "MeshCollider":
                                    bpy.ops.object.select_all(action="DESELECT")
                                    collider_object.select_set(True)
                                    mesh_collider_location = collider_object.location.copy()
                                    collider_object.location += joined_translate
                                    bpy.ops.wm.stl_export(
                                        filepath=os.path.join(
                                            folder_path, collider_object.name + ".stl"
                                        ),
                                        export_selected_objects=True,
                                        apply_modifiers=True,
                                    )
                                    collider_object.location = mesh_collider_location
                                    bpy.ops.object.select_all(action="DESELECT")
                                    write_text += (
                                        f"\n  <geometry>"
                                        f"\n    <mesh>"
                                        # {round(collider_object.dimensions.x, 6)}
                                        f"\n      <uri>{collider_object.name.replace('.', '')}.stl</uri>"
                                        f"\n    </mesh>"
                                    )
                                # Box collider
                                elif collider_object.collider_type == "BoxCollider":
                                    write_text += (
                                        f"\n    <box>"
                                        f"\n      <size>{round(collider_object.dimensions.x, 6)} {round(collider_object.dimensions.y, 6)} {round(collider_object.dimensions.z, 6)}</size>"
                                        f"\n    </box>"
                                    )
                                # Cylinder collider
                                elif (
                                    collider_object.collider_type == "CylinderCollider"
                                ):
                                    write_text += (
                                        f"\n    <cylinder>"
                                        f"\n      <radius>{round(collider_object.dimensions.x /2, 6)}</radius>"
                                        f"\n      <length>{round(collider_object.dimensions.z, 6)}</length>"
                                        f"\n    </cylinder>"
                                    )
                                # Sphere collider
                                elif collider_object.collider_type == "SphereCollider":
                                    write_text += (
                                        f"\n    <ellipsoid>"
                                        f"\n      <radii>{round(collider_object.dimensions.x /2, 6)} {collider_object.dimensions.y /2:.6f} {collider_object.dimensions.z /2:.6f}</radii>"
                                        f"\n    </ellipsoid>"
                                    )
                                # Cone collider
                                elif collider_object.collider_type == "ConeCollider":
                                    write_text += (
                                        f"\n    <cone>"
                                        f"\n      <radius>{round(collider_object.dimensions.x / 2, 6)}</radius>"
                                        f"\n      <length>{round(collider_object.dimensions.z, 6)}</length>"
                                        f"\n    </cone>"
                                    )
                                # Plane collider
                                elif collider_object.collider_type == "PlaneCollider":
                                    write_text += (
                                        f"\n    <plane>"
                                        f"\n      <size>{round(collider_object.dimensions.x, 6)} {collider_object.dimensions.y:.6f}</size>"
                                        f"\n    </plane>"
                                    )
                                # Close the geometry and collision tags
                                write_text += (
                                        f"\n  </geometry>"
                                        f"\n</collision>"
                                    )
                                self.write_to_sdf(sdf_file_path, write_text)

                # Export link lights
                for obj in link_collection.all_objects:
                    if obj.type == 'LIGHT':
                        light = obj
                        self.export_lights(sdf_file_path, light)

                write_text = "\n</link>"
                self.write_to_sdf(sdf_file_path, write_text)

    def create_config(self, config_file_path, model_scene):
        write_text = (
        f"<model>\n"
        f"    <name>{model_scene.name}</name>\n"
        f"    <version>1.0</version>\n"
        f"    <sdf version='1.6'>model.sdf</sdf>\n"
        )
        if model_scene.author_name != "":
            write_text += (
            f"\n"
            f"    <author>\n"
            f"        <name>{model_scene.author_name}</name>\n"
            f"        <email>{model_scene.author_email}</email>\n"
            f"    </author>\n"
            )
        if model_scene.author_name != "":
            write_text += (
            f"\n"
            f"    <description>\n"
            f"        {model_scene.model_description}\n"
            f"    </description>\n"
            )
        write_text += (
        f"</model>"
        )
        self.write_to_sdf(config_file_path, write_text)

    def execute(self, context):
        # Flag to ensure update function are disabled when accessing properties
        context.window_manager.export_in_progress = True

        # Set initial scene to return to after export is complete
        initial_scene: bpy.props.PointerProperty(
            name="Initial Scene",
        )  # type: ignore

        initial_scene = bpy.context.window.scene

        # Ensure no objects are in edit mode
        if len(bpy.context.view_layer.objects.selected) != 0:
            bpy.ops.object.mode_set("INVOKE_DEFAULT", mode="OBJECT")

        # Deselect all
        bpy.ops.object.select_all(action="DESELECT")

        # Loop through all scenes (models)
        for model_scene in bpy.data.scenes:
            # Switch scene
            bpy.context.window.scene = model_scene

            # Create folder
            self.make_sdf_folder(model_scene.name)

            folder_path = self.make_sdf_folder(model_scene.name)

            # Set sdf file path
            sdf_file_path = os.path.join(folder_path, "model.sdf")
            config_file_path = os.path.join(folder_path, "model.config")

            # Export config file
            if bpy.context.scene.export_config:
                self.create_config(config_file_path, model_scene)

            # Create model.sdf and append model text
            write_text = (
                f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<sdf version="1.6">\n'
                f'  <model name="{model_scene.name}">'
            )
            self.write_to_sdf(sdf_file_path, write_text)

            all_collections = get_all_collections()
            
            self.loop_links(model_scene, all_collections, sdf_file_path, folder_path, model_scene.use_relative_link_poses)

            # Check for armature
            found_armature = False

            # Iterate through all objects in the current scene
            for obj in bpy.context.scene.objects:
                # Check if the object's type is 'ARMATURE'
                if obj.type == 'ARMATURE':
                    found_armature = True
                    # Print the name of the found armature for confirmation
                    print(f"Found armature: '{obj.name}'")
                    # We can stop searching once we've found one
                    break

            # Export joints
            if found_armature:
                self.export_joints(sdf_file_path, model_scene.use_relative_link_poses)


            

            # Export scene lights
            for light in bpy.context.scene.objects:
                if light.type == 'LIGHT':
                    self.export_lights(sdf_file_path, light)

            write_text = f"\n  </model>\n" f"</sdf>"
            self.write_to_sdf(sdf_file_path, write_text)

            format_xml_file(sdf_file_path)

        bpy.context.window.scene = initial_scene
        context.window_manager.export_in_progress = False
        return {"FINISHED"}

# Formats XML file with indentation
def format_xml_file(input_file_path):
    # Read the XML content from the file
    with open(input_file_path, "r") as file:
        xml_string = file.read()

    # Parse the XML string
    dom = xml.dom.minidom.parseString(xml_string)

    # Convert it back to a pretty-printed XML string
    pretty_xml = dom.toprettyxml(indent="  ")  # 4 spaces for indentation

    # Remove extra blank lines
    cleaned_xml = re.sub(r"\n\s*\n", "\n", pretty_xml).strip()  # Remove extra newlines

    # Write the pretty XML back to the same file (overwrite)
    with open(input_file_path, "w") as file:
        file.write(cleaned_xml)

    return {"FINISHED"}

# Checks if link is the child of a joint
def get_joint_location(link_name):
    
    bone_location = None
    
    # Get the armature object
    armature_object = get_armature()

    if armature_object == None:
        bone_location = None

    else:
        # Loop through pose bones
        for bone in armature_object.pose.bones:
            if hasattr(bone, 'joint_grp') and hasattr(bone.joint_grp, 'child_link'):
                if bone.joint_grp.child_link == link_name:
                    bone_location = armature_object.data.bones[bone.name].head_local
                    break

    return bone_location

def get_joint_location_from_name(joint_name):
    armature_object = get_armature()
    return armature_object.data.bones[joint_name].head_local

# Checks if link is the child of a joint
def get_previous_bone_name(link_name):

    # Get the armature object
    armature_object = get_armature()

    if armature_object == None:
        return None

    else:
        # Loop through pose bones
        for bone in armature_object.pose.bones:
            if hasattr(bone, 'joint_grp') and hasattr(bone.joint_grp, 'child_link'):
                if bone.joint_grp.child_link == link_name:
                    return bone.name

    return None

# Checks if link is the child of a joint
def get_joint_name(link_name):
    # Get the armature object
    armature = get_armature()

    if armature == None:
        return None

    else:
        # Loop through pose bones
        for bone in armature.pose.bones:
            if hasattr(bone, 'joint_grp') and hasattr(bone.joint_grp, 'child_link'):
                if bone.joint_grp.child_link == link_name:
                    return bone.name

    return None