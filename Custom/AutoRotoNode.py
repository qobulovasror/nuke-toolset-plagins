import nuke
import numpy as np

class AutoRotoNode:
    def __init__(self, node):
        self.node = node

    def execute(self):
        x = self.node['x_coord'].value()
        y = self.node['y_coord'].value()

        target_color = self.get_pixel_color(x, y)
        if target_color is not None:
            self.create_roto_for_color(target_color)
        else:
            nuke.message("Rang topilmadi!")

    def get_pixel_color(self, x, y):
        """Tanlangan nuqtaning rangini olish"""
        node = nuke.selectedNode()
        if node:
            color = np.array([
                node.sample('rgba.red', x, y),
                node.sample('rgba.green', x, y),
                node.sample('rgba.blue', x, y)
            ])
            return color
        return None

    def create_roto_for_color(self, target_color, tolerance=0.05):
        """Berilgan rangga mos keladigan joylarni roto bilan belgilash"""
        node = nuke.selectedNode()
        if not node:
            nuke.message("Iltimos, tugunni tanlang!")
            return

        width = node.width()
        height = node.height()
        matching_points = []

        for y in range(height):
            for x in range(width):
                color = np.array([
                    node.sample('rgba.red', x, y),
                    node.sample('rgba.green', x, y),
                    node.sample('rgba.blue', x, y)
                ])
                if np.linalg.norm(color - target_color) < tolerance:
                    matching_points.append((x, y))

        if not matching_points:
            nuke.message("Hech qanday mos rang topilmadi!")
            return

        roto = nuke.createNode("Roto")
        shape = roto['curves'].rootLayer.append(nuke.rotopaint.Shape())

        for x, y in matching_points:
            shape.append(nuke.rotopaint.ShapeControlPoint(x, y))

        nuke.message("Roto yaratildi!")

def create_auto_roto_node():
    """AutoRoto Node yaratish"""
    node = nuke.createNode("NoOp", inpanel=True)
    node.setName("AutoRoto")

    # X va Y koordinatalari uchun knoblar
    node.addKnob(nuke.Int_Knob("x_coord", "X koordinatasi"))
    node.addKnob(nuke.Int_Knob("y_coord", "Y koordinatasi"))

    # Tugma qo'shish
    execute_button = nuke.PyScript_Knob("execute_auto_roto", "Roto yaratish")
    node.addKnob(execute_button)

    # ✅ **Tugma bosilganda to‘g‘ri funksiyani chaqirish**
    node.knob("execute_auto_roto").setCommand("import nuke; exec(nuke.thisNode()['python_script'].value())")

    # **Kodni tugun ichida saqlash**
    python_script = """
import nuke
node = nuke.thisNode()
auto_roto = AutoRotoNode(node)
auto_roto.execute()
"""
    node.addKnob(nuke.Text_Knob("divider", ""))
    node.addKnob(nuke.String_Knob("python_script", "Python Script"))
    node["python_script"].setValue(python_script)




