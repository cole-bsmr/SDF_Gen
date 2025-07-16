import bpy

class SDFG_OT_CreateLights(bpy.types.Operator):
    bl_idname = "object.create_light"
    bl_label = "Create a Light"
    bl_options = {'REGISTER', 'UNDO'}

    light_type: bpy.props.EnumProperty(
        name="Light Type",
        description="The type of light.",
        items=[
            ("POINT", "Point", "Create a point light"),
            ("SPOT", "Spot", "Create a spot light"),
            ("DIRECTIONAL", "Directional", "Create a directiona light"),
        ],
    )  # type: ignore

    def lights_collection_check(self, context):
        scene = context.scene
        lights_collection = bpy.data.collections.get("Lights")
        if lights_collection is None:
            # Create the "Lights" collection
            lights_collection = bpy.data.collections.new("Lights")
            # Link the collection to the scene
            scene.collection.children.link(lights_collection)
        layer_collection = bpy.context.view_layer.layer_collection.children[lights_collection.name]
        bpy.context.view_layer.active_layer_collection = layer_collection

    def execute(self, context):
        # self.lights_collection_check(context)

        if self.light_type == 'POINT':
            bpy.ops.object.light_add(type='POINT')

        if self.light_type == 'SPOT':
            bpy.ops.object.light_add(type='SPOT')

        if self.light_type == 'DIRECTIONAL':
            bpy.ops.object.light_add(type='SUN')

        return {'FINISHED'}

