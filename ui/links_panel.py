import bpy

class SNA_UL_display_scenes_list(bpy.types.UIList):
    # List of scenes for the model window.

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        row = layout
        layout.prop(item, "name", text="", icon_value=0, emboss=False)

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        if not self.filter_name:
            for i in range(len(getattr(data, propname))):
                flt_flags.append(self.bitflag_filter_item)
            return flt_flags, flt_neworder

        for item in getattr(data, propname):
            if self.filter_name.lower() in item.name.lower():
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0)

        return flt_flags, flt_neworder
