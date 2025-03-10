import nuke
import cv2
import numpy as np

def get_object_mask(image_path, x, y):
    """
    Ob’ekt chegaralarini aniqlab, maska yaratish
    :param image_path: Rasm fayli yo‘li
    :param x: Sichqoncha bosilgan x koordinatasi
    :param y: Sichqoncha bosilgan y koordinatasi
    :return: Ob’ekt maskasi (contour)
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Treshold qo‘yish
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Konturlarni aniqlash
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:  # Sichqoncha bosilgan nuqta ichida bo‘lsa
            return cnt
    return None

def create_roto_from_contour(contour):
    """
    OpenCV konturlarini Nuke Roto node'ga o‘tkazish
    """
    roto = nuke.createNode("Roto")
    shape = roto['curves'].rootLayer.createCurve()

    for point in contour:
        x, y = point[0]
        shape.append(nuke.rotopaint.Vertex(float(x), float(y)))

def select_object():
    """
    Foydalanuvchi bosgan joyga qarab avtomatik maska yaratish
    """
    node = nuke.selectedNode()
    file_path = node['file'].value()  # Rasmdan faylni olish

    # Sichqoncha bosilgan joy
    x, y = 100, 150  # (Bu joyni real vaqt rejimida olish kerak!)

    contour = get_object_mask(file_path, x, y)
    if contour is not None:
        create_roto_from_contour(contour)
    else:
        nuke.message("Ob’ekt topilmadi!")

# Nuke menyusiga qo‘shish
# nuke.menu("Nodes").addCommand("Custom/Object Select Roto", select_object)
