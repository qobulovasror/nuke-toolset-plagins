import nuke
import sys
import subprocess


def createXMEMNode():
    # Maxsus NoOp node yaratamiz
    xmem_launcher = nuke.createNode("NoOp")
    xmem_launcher.setName("XMem_Launcher")

    # PyScript tugma yaratiladi
    launch_btn = nuke.PyScript_Knob("launch_xmem", "XMem2 ni ishga tushirish")

    # Tugmaga bajariladigan kod yoziladi
    script = """
node = nuke.thisNode()
input_node = node.input(0)
if input_node is None:
    nuke.message("Iltimos, bu nodeni Read node dan keyin ulang.")
else:
    try:
        # Read node dan file pathni olamiz
        file_path = input_node['file'].value()
        python_exe = "C:/Users/qobul/AppData/Local/Programs/Python/Python312/python.exe"
        path_components = os.path.split(file_path)
        new_path_components = list(path_components[:-1])
        new_path = os.path.join(*new_path_components)
        os.chdir(os.path.dirname(__file__))
        xmem_script = "C:/baza/nuke_tools/XMem2/interactive_demo.py"
        cmd = ["cmd", "/k", python_exe, xmem_script, "--video", file_path]
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        nuke.message("XMem2 running! Result will be saved at: XMem2/output")
    except Exception as e:
        nuke.message("Xatolik: " + str(e))
"""

    # Kodni tugmaga biriktiramiz
    launch_btn.setValue(script)
    xmem_launcher.addKnob(launch_btn)
