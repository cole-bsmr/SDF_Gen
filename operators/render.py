import math
import mathutils
import bpy
from bpy.props import FloatProperty


class OBJECT_OT_capture_thumbnail(bpy.types.Operator):
    """Creates and positions a thumbnail camera targeting visible objects"""

    bl_idname = "object.capture_thumbnail"
    bl_label = "Setup Thumbnail Camera"
    bl_options = {"REGISTER", "UNDO"}

    azimuth: FloatProperty(
        name="Azimuth Angle",
        description="Side angle rotation in degrees (0 = front view, 90 = side view)",
        default=30.0,
        min=-180.0,
        max=180.0,
    )  # type: ignore

    elevation: FloatProperty(
        name="Elevation Angle",
        description="Downward angle in degrees (0 = eye level, 90 = top down)",
        default=30.0,
        min=-89.0,
        max=89.0,
    )  # type: ignore

    padding: FloatProperty(
        name="Padding Factor",
        description="Margin multiplier around the model",
        default=1.35,
        min=1.0,
        max=5.0,
    )  # type: ignore

    def execute(self, context):
        scene = context.scene

        # 1. Target selected visible mesh objects, or fall back to all visible mesh objects
        target_objects = [
            obj
            for obj in context.selected_objects
            if obj.type == "MESH" and obj.visible_get()
        ]

        if not target_objects:
            target_objects = [
                obj
                for obj in scene.objects
                if obj.type == "MESH" and obj.visible_get()
            ]

        if not target_objects:
            self.report(
                {"ERROR"},
                "No visible mesh objects found in scene to set up camera.",
            )
            return {"CANCELLED"}

        # 2. Compute world-space bounding box center and bounding radius
        min_co = mathutils.Vector((float("inf"), float("inf"), float("inf")))
        max_co = mathutils.Vector((float("-inf"), float("-inf"), float("-inf")))

        for obj in target_objects:
            matrix = obj.matrix_world
            for corner in obj.bound_box:
                world_corner = matrix @ mathutils.Vector(corner)
                min_co.x = min(min_co.x, world_corner.x)
                min_co.y = min(min_co.y, world_corner.y)
                min_co.z = min(min_co.z, world_corner.z)
                max_co.x = max(max_co.x, world_corner.x)
                max_co.y = max(max_co.y, world_corner.y)
                max_co.z = max(max_co.z, world_corner.z)

        center = (min_co + max_co) / 2.0
        bounding_radius = (max_co - min_co).length / 2.0

        # 3. Remove existing cameras marked with is_thumbcam = True
        for obj in list(bpy.data.objects):
            if obj.type == "CAMERA" and obj.data:
                if getattr(obj.data, "is_thumbcam", False):
                    bpy.data.objects.remove(obj, do_unlink=True)

        # 4. Create camera in the top-level scene collection & mark it
        cam_name = "Thumbnail_Camera"
        cam_data = bpy.data.cameras.new(name=cam_name)
        cam_data.is_thumbcam = True

        cam_obj = bpy.data.objects.new(name=cam_name, object_data=cam_data)
        scene.collection.objects.link(cam_obj)

        # 5. Position and align camera based on custom azimuth/elevation
        fov = cam_data.angle
        distance = (bounding_radius / math.sin(fov / 2.0)) * self.padding

        rad_az = math.radians(self.azimuth)
        rad_el = math.radians(self.elevation)

        offset = mathutils.Vector(
            (
                distance * math.cos(rad_el) * math.sin(rad_az),
                -distance * math.cos(rad_el) * math.cos(rad_az),
                distance * math.sin(rad_el),
            )
        )

        cam_obj.location = center + offset
        direction = center - cam_obj.location
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

        # 6. Set as active scene camera & set render resolution
        scene.camera = cam_obj
        scene.render.resolution_x = 1024
        scene.render.resolution_y = 1024

        # 7. Set view thumbnail camera
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.region_3d.view_perspective = "CAMERA"
                        space.lock_camera = True

        self.report({"INFO"}, "Thumbnail camera created and positioned.")
        return {"FINISHED"}