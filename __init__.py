bl_info = {
    "name": "SDF Gen",
    "author": "Cole Biesemeyer",
    "version": (1, 0, 0),
    "blender": (4, 3, 0),
    "location": "3D Viewport > Sidebar > SDF Gen",
    "description": "Creates SDF files from Blender scenes",
    "category": "View3D",
}

# This is only relevant on first run, on later reloads those modules
# are already in locals() and those statements do not do anything.
import bpy

from . import auto_load

auto_load.init()

# from .ui.utility_panel import SDFG_PT_Utilities  # Import your panel class
# from .operators.utility import SDFG_OT_UtilitiesOperator
# from .ui.links_panel import SNA_UL_display_scenes_list
# import operators.colliders
from .operators.create import update_scene
from .ui.object_properties_panel import LinkCollectionProperties
from .operators.joints import JointBoneProperties
    

def register():
    auto_load.register()
    bpy.types.WindowManager.my_list_index = bpy.props.IntProperty(update=update_scene)
    """keymaps = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
        name="3D View", space_type="VIEW_3D"
    )
    kmi = keymaps.keymap_items.new("my_panel.add_scene", "PLUS", "PRESS")
    kmi = keymaps.keymap_items.new("my_panel.delete_scene", "MINUS", "PRESS")"""

    bpy.types.Collection.link_grp = bpy.props.PointerProperty(type=LinkCollectionProperties)
    bpy.types.PoseBone.joint_grp = bpy.props.PointerProperty(type=JointBoneProperties)
    # bpy.types.Scene.utilties_advanced = bpy.props.BoolProperty(name="Utilities Advanced", default=False)


def unregister():
    # bpy.utils.unregister_class(JointObjectProperties)
    auto_load.unregister()
    # bpy.utils.unregister_class(MyPanel)
    del bpy.types.WindowManager.my_list_index
    del bpy.types.PoseBone.joint_grp
    del bpy.types.Collection.link_grp
    # del bpy.types.Scene.utilties_advanced


if __name__ == "__main__":
    register()

    