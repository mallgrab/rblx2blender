import bpy
from bpy.types import Panel

RobloxPlace = r'C:\Users\win-spike\Desktop\rbxl2obj\Pirate.rbxl'
RobloxInstallLocation = r'C:\Users\win-spike\Documents\CnCRemastered\roblox2008\content'

PlacePath = ""
InstallPath = ""

class RBLX_Place_Path(bpy.types.PropertyGroup):
    file_path: bpy.props.StringProperty(name="",
                                        description="The place you want to convert",
                                        default=RobloxPlace,
                                        maxlen=1024,
                                        subtype="FILE_PATH")

class RBLX_Install_Path(bpy.types.PropertyGroup):
    file_path: bpy.props.StringProperty(name="",
                                        description="The place you want to convert",
                                        default=RobloxInstallLocation,
                                        maxlen=1024,
                                        subtype="FILE_PATH")

class TestCheckBox(bpy.types.PropertyGroup):
    checkbox_bool: bpy.props.BoolProperty(name="A checkbox", description="Do this or that", default = False)

class StartConverting(bpy.types.Operator):
    bl_idname = "scene.button_operator_convert"
    bl_label = "Start Converting"

    def execute(self, context):
        print("Pressed button", PlacePath.file_path, InstallPath.file_path)
        return {'FINISHED'}

class RBLX_PT_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Place Converter"
    bl_category = "Rblx To Blender"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        global PlacePath
        global InstallPath

        PlacePath = scene.Place_Path
        InstallPath = scene.Install_Path

        row = layout.row()
        row.label(text="Place To Convert:")
        row = layout.row()
        row.prop(PlacePath, "file_path")

        row = layout.row()
        row.label(text="Roblox Installation Path:")
        row = layout.row()
        row.prop(InstallPath, "file_path")

        layout.operator("scene.button_operator_convert")
        layout.prop(scene.Test_Boolean, "checkbox_bool")


        