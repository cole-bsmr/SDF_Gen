import bpy
from ..operators.joints import JointBoneProperties


class SDFG_PT_LinkPropertiesPanel(bpy.types.Panel):
    bl_label = "Link Properties Panel"
    bl_idname = "SDFG_PT_LinkPropertiesPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SDF_Gen"

    @classmethod
    def poll(cls, context):
        layer_coll = bpy.context.view_layer.active_layer_collection
        coll = layer_coll.collection
        if len(bpy.context.selected_objects) == 0 and coll.collection_type == 'LinkCollection':
            return True
        # Check if no objects are selected
        else:
            return False
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Link Properties")

        col = layout.column()
        split = col.split(factor=0.3, align=True)  # Control the split size
        split.label(text="Static:")
        split.prop(context.collection.link_grp, 'is_static', text="")

class SDFG_PT_VisualPropertiesPanel(bpy.types.Panel):
    bl_label = "Visual Properties Panel"
    bl_idname = "SDFG_PT_VisualPropertiesPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SDF_Gen"

    @classmethod
    def poll(cls, context):
        if not context.object == None:
            # Ensure there are selected objects
            if not context.selected_objects:
                return False

            if not context.selected_ids:
                return False
            
            if not context.object.type == 'MESH':
                return False

        # Get the active object
        active_obj = context.active_object

        # Ensure there is an active object and it is linked to collections
        if active_obj and active_obj.users_collection:
            # Check if any collection name contains "_visual"
            return any("_visual" in col.name for col in active_obj.users_collection)

        return False

    def draw(self, context):
        layout = self.layout
        layout.label(text="Visual Properties: " + bpy.context.active_object.name)
        # box = layout.box()
        
        
        if context.object.modifiers.get('Decimate'):
            box = layout.box()
            box.label(text="Decimate Mesh")
            box.prop(context.object.modifiers['Decimate'], "ratio", text="Mesh Resolution")
            triangle_count = len(context.object.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.loop_triangles)
            box.label(text=f"Triangles: {triangle_count}")
        else:
            layout.operator("object.modifier_add", text="Decimate Mesh").type = 'DECIMATE'
        
        # box = layout.box()
        if context.object.modifiers.get('Smooth by Angle'):
            box = layout.box()
            box.label(text="Smooth Mesh")
            box.prop(context.object.modifiers['Smooth by Angle'], '["Input_1"]', text="Smooth Angle")
            row = box.row()
            row.label(text="Ignore Sharpness:")
            row.prop(context.object.modifiers['Smooth by Angle'], '["Socket_1"]', text="")
        # box.prop(context.object, "active_material_index", text="")
        else:
            layout.operator("object.shade_auto_smooth", text="Smooth Mesh")

class LinkCollectionProperties(bpy.types.PropertyGroup):
    bl_label = "Link Properties"
    bl_idname = "LinkCollectionProperties"

    is_static: bpy.props.BoolProperty(name="Static", default=True) # type: ignore
    
class SDFG_PT_JointPropertiesPanel(bpy.types.Panel):
    bl_label = "Joint Properties"
    bl_idname = "SDFG_PT_JointPropertiesPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SDF_Gen"

    @classmethod
    def poll(cls, context):
        # Ensure there are selected objects
        if not context.active_pose_bone or context.active_pose_bone.joint_grp.joint_type == 'NotJoint':
            return False

        return True

    def draw(self, context):
        layout = self.layout
        # box = layout.box()
        col = layout.column()
        col.label(text=(context.active_pose_bone.name + ":"))

        # Joint location
        col.prop(context.active_pose_bone, "head")
        
        # Joint size
        row = col.row()
        split = row.split(factor=0.4) 
        split.label(text="Joint Size:")
        split.prop(context.active_pose_bone.joint_grp, "joint_size", text="")

        col.separator(type='LINE')
        # Choose child link
        row = col.row()
        split = row.split(factor=0.27)
        split.label(text="Child Link:")
        split.label(text=bpy.context.active_pose_bone.joint_grp.child_link)

        # Choose parent link
        row = col.row()
        split = row.split(factor=0.31)
        split.label(text="Parent Link:")

        # split.operator("object.set_joint_parent", text = context.active_pose_bone.joint_grp.parent_link)
        split.prop(context.active_pose_bone.joint_grp, "parent_link", text="")

        col.separator(type='LINE')

        if context.active_pose_bone.joint_grp.joint_type == 'RevoluteJoint':
            col.label(text="Revolute Properties:")
            col.prop(context.active_pose_bone.joint_grp, "revolute_continuous")
            if context.active_pose_bone.joint_grp.revolute_continuous == False:
                col.prop(context.active_pose_bone.joint_grp, "revolute_min")
                col.prop(context.active_pose_bone.joint_grp, "revolute_max")

        if context.active_pose_bone.joint_grp.joint_type == 'PrismaticJoint':
            col.label(text="Revolute Properties:")
            col.prop(context.active_pose_bone.joint_grp, "prismatic_min")
            col.prop(context.active_pose_bone.joint_grp, "prismatic_max")


        col.prop(context.active_pose_bone.joint_grp, "revolute_range")

class SDFG_PT_LightPropertiesPanel(bpy.types.Panel):
    bl_label = "Light Properties"
    bl_idname = "SDFG_PT_LightPropertiesPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SDF_Gen"

    @classmethod
    def poll(cls, context):
        # Ensure there are selected objects
        if context.object and context.object.type == 'LIGHT':
            return True
        else:
            return False
    
    def draw(self, context):
        # light = bpy.data.lights[context.object.name]
        obj = context.object 
        light = obj.data
        layout = self.layout
        layout.label(text=light.name)
        layout.prop(light, "type", text="Type")
        layout.prop(light, "energy", text="Intensity")
        if context.object.data.type == 'POINT':
            layout.prop(light, "shadow_soft_size", text="Range")
        if context.object.data.type == 'SPOT':
            layout.prop(light, "cutoff_distance", text="Range")
        layout.prop(light, "color", text="Diffuse Color")
        # layout.prop(context.object, "hide_render", text="Light On")
        # layout.prop(context.object, "hide_viewport", text="Visualize")
        layout.prop(light, "use_shadow", text="Shadows")
        layout.prop(light, "specular_factor", text="Specular Factor") 
        layout.prop(light, "spot_blend", text="Falloff") 
        layout.prop(light, "linear_attenuation", text="linear_attenuation") 
        layout.prop(light, "spot_size", text="Spot Angle")