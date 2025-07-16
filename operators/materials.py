import bpy
from ..operators.general_functions import show_message_box

class SDFG_OT_SwapMaterial(bpy.types.Operator):
    """Deletes the joint."""
    bl_idname = "object.swap_material"
    bl_label = "Swwap Material"
    bl_options = {'REGISTER', 'UNDO'}

    original_color = (0, 0, 0, 1)

    def execute(self, context):
        selected_index = bpy.context.object.active_material_index 
        material = bpy.context.object.material_slots[selected_index].material
        principled = material.node_tree.nodes["Principled BSDF"]
        
        self.original_color = principled.inputs["Base Color"].default_value

        if context.object:  # Check if an object is selected
            reset_material_to_principled_bsdf()
        else:
           show_message_box(message="No active object.", title="Error", icon="INFO")

        apply_material(self.original_color)

        return {'FINISHED'}

bpy.types.Scene.material_type = bpy.props.EnumProperty(
    name="Materials",
        items=[
            ("Aluminum", "Aluminum", ""),
            ("Brass", "Brass", ""),
            ("Chromium", "Chromium", ""),
            ("Copper", "Copper", ""),
            ("Diamond", "Diamond", ""),
            ("Gold", "Gold", ""),
            ("Iron", "Iron", ""),
            ("Lead", "Lead", ""),
            ("Nickel", "Nickel", ""),
            ("Plastic_Acrylic", "Plastic Acrylic", ""),
            ("Plastic_PC", "Plastic PC", ""),
            ("Plastic_PET", "Plastic PET", ""),
            ("Plastic_PP", "Plastic PP", ""),
            ("Plastic_PVC", "Plastic PVC", ""),
            ("Platinum", "Platinum", ""),
            ("Polyurethane", "Polyurethane", ""),
            ("Rubber", "Rubber", ""),
            ("Silicon", "Silicon", ""),
            ("Silver", "Silver", ""),
            ("Titanium", "Titanium", ""),
            ("Tungsten", "Tungsten", ""),
            ("Vanadium", "Vanadium", ""),
            ("Zinc", "Zinc", ""),
        ]
    )

MATERIAL_PROPERTIES = {
    'Aluminum': {
        "Base Color": (0.912, 0.914, 0.92, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.4,
    },
    'Plastic_PC': {
        "Base Color": (1.0, 1.0, 1.0, 1.0),
        "Metallic": 0.0,
        "Roughness": 0.4,
        'Transmission Weight': 1.0,
        'IOR': 1.5848,
    },
    'Plastic_PET': {
        "Base Color": (1.0, 1.0, 1.0, 1.0),
        "Metallic": 0.0,
        "Roughness": 0.4,
        'Transmission Weight': 1.0,
        'IOR': 1.575,
    },
    'Plastic_PP': {
        "Base Color": (1.0, 1.0, 1.0, 1.0),
        "Metallic": 0.0,
        "Roughness": 0.4,
        'Transmission Weight': 1.0,
        'IOR': 1.492,
    },
    'Plastic_PVC': {
        "Base Color": (1.0, 1.0, 1.0, 1.0),
        "Metallic": 0.0,
        "Roughness": 0.3,
        'Transmission Weight': 1.0,
        'IOR': 1.531,
    },
    'Platinum': {
        "Base Color": (0.679, 0.642, 0.588, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.1,
        "Specular Tint": (0.785, 0.789, 0.784, 1.0),
    },
    'Chromium': {
        "Base Color": (0.638, 0.651, 0.663, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.01,
        "Specular Tint": (0.632, 0.718, 0.809, 1.0),
    },
    'Diamond': {
        "Base Color": (1.0, 1.0, 1.0, 1.0),
        "Metallic": 0.0,
        "Roughness": 0.01,
        'Transmission Weight': 1.0,
        'IOR': 2.4168,
    },
    'Copper': {
        "Base Color": (0.926, 0.721, 0.504, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.4,
        "Specular Tint": (0.996, 0.957, 0.823, 1.0),
    },
    'Brass': {
        "Base Color": (0.887, 0.789, 0.434, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.4,
        "Specular Tint": (0.988, 0.976, 0.843, 1.0),
    },
    'Gold': {
        "Base Color": (0.944, 0.776, 0.373, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.05,
        "Specular Tint": (0.998, 0.981, 0.751, 1.0),
    },
    'Iron': {
        "Base Color": (0.531, 0.512, 0.496, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.6,
        "Specular Tint": (0.571, 0.54, 0.586, 1.0),
    },
    'Plastic_Acrylic': {
        "Base Color": (1.0, 1.0, 1.0, 1.0),
        "Metallic": 0.0,
        "Roughness": 0.05,
        'Transmission Weight': 1.0,
        'IOR': 1.476,
    },
    'Nickel': {
        "Base Color": (0.649, 0.61, 0.541, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.4,
        "Specular Tint": (0.797, 0.801, 0.789, 1.0),
    },
    'Silicon': {
        "Base Color": (0.344, 0.367, 0.419, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.4,
    },
    'Polyurethane': {
        "Base Color": (1.0, 1.0, 1.0, 1.0),
        "Metallic": 0.0,
        "Roughness": 0.4,
        'Transmission Weight': 1.0,
        'IOR': 1.6,
    },
    'Vanadium': {
        "Base Color": (0.52, 0.532, 0.541, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.4,
        "Specular Tint": (0.402, 0.447, 0.395, 1.0),
    },
    'Rubber': {
        "Base Color": (0.023, 0.023, 0.023, 1.0),
        "Metallic": 0.0,
        "Roughness": 0.5,
        'IOR': 1.5,
    },
    'Tungsten': {
        "Base Color": (0.504, 0.498, 0.478, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.4,
        "Specular Tint": (0.403, 0.418, 0.423, 1.0),
    },
    'Silver': {
        "Base Color": (0.962, 0.949, 0.922, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.1,
        "Specular Tint": (0.999, 0.998, 0.998, 1.0),
    },
    'Titanium': {
        "Base Color": (0.616, 0.582, 0.544, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.3,
        "Specular Tint": (0.689, 0.683, 0.689, 1.0),
    },
    'Lead': {
        "Base Color": (0.632, 0.626, 0.641, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.6,
        "Specular Tint": (0.803, 0.808, 0.862, 1.0),
    },
    'Zinc': {
        "Base Color": (0.802, 0.844, 0.863, 1.0),
        "Metallic": 1.0,
        "Roughness": 0.1,
        "Specular Tint": (0.817, 0.922, 0.964, 1.0),
    }
}

bpy.types.Scene.keep_color = bpy.props.BoolProperty(default=False)

def reset_material_to_principled_bsdf():
    """Resets the given material to a new Principled BSDF."""

    selected_index = bpy.context.object.active_material_index 
    material = bpy.context.object.material_slots[selected_index].material

    # Create a new Principled BSDF node
    principled = bpy.data.materials.new(name="Principled BSDF")
    principled.use_nodes = True

    # Remove existing nodes
    nodes = material.node_tree.nodes
    for node in nodes:
        if node.type != 'OUTPUT_MATERIAL':  # Keep the output node
            nodes.remove(node)

    # Add the new Principled BSDF node
    new_principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    # Link the new Principled BSDF to the Material Output
    material.node_tree.links.new(new_principled_node.outputs['BSDF'], nodes['Material Output'].inputs['Surface'])

def apply_material(original_color):
    selected_index = bpy.context.object.active_material_index
    material = bpy.context.object.material_slots[selected_index].material
    principled = material.node_tree.nodes["Principled BSDF"]

    material.name = bpy.context.scene.material_type

    keep_color = bpy.context.scene.keep_color
    material_type = bpy.context.scene.material_type

    if material_type in MATERIAL_PROPERTIES:
        properties = MATERIAL_PROPERTIES[material_type]
        for input_name, input_value in properties.items():
            principled.inputs[input_name].default_value = input_value

    if keep_color:
        principled.inputs["Base Color"].default_value = original_color 
