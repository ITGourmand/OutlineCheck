import sys
import numpy as np
import copy
import math
from PIL import Image
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QFileDialog,
    QFrame,
    QSplitter,
    QAbstractItemView,
    QColorDialog,
    QComboBox,
    QCheckBox,
)
from PyQt6.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QColor,
    QShortcut,
    QKeySequence,
    QWheelEvent,
    QMouseEvent,
    QKeyEvent,
    QIcon,
    QPen,
    QBrush,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QSize

LANGUAGES = {
    "FR": {
        "title": "OUTLINECHECK",
        "open": "  Ouvrir Image",
        "save": "  Exporter PNG",
        "replacement_header": "COULEUR DE REMPLACEMENT",
        "groups_header": "GROUPES PAR COULEUR",
        "fix_btn": "CORRIGER LA SÉLECTION",
        "info": "Maintenez [Espace] pour naviguer",
        "detect_title": "<b>DÉTECTION (MOTIFS)</b>",
        "preview_title": "<b>APERÇU LIVE (RÉSULTAT)</b>",
        "pattern": "Motif",
        "cl_name": "Cluster",
        "brush_mode": "Mode Pinceau",
        "choose_color": "Choisir une couleur",
        "toggle_outline_on": "VOIR: COULEURS CONTOUR",
        "toggle_outline_off": "VOIR: TOUTES COULEURS",
        "layer_title": "Calques",
        "pp_checkbox": "Pixel Perfect",
        "tooltip_open": "Ouvrir une image",
        "tooltip_save": "Exporter l'image (Ctrl+S)",
        "tooltip_brush": "Outil Pinceau (P)",
        "tooltip_select": "Outil Sélection (S)\nShift: Retirer\nCtrl: Ajouter\nCtrl+C/V: Copier/Coller",
        "tooltip_pipette": "Pipette / Sélecteur (O)",
        "tooltip_add": "Ajouter un calque",
        "tooltip_del": "Supprimer le calque",
        "tooltip_merge": "Fusionner les calques sélectionnés",
        "tooltip_up": "Monter le calque",
        "tooltip_down": "Descendre le calque",
        "tooltip_nocolor": "Supprimer la couleur (D)",
    },
    "EN": {
        "title": "OUTLINECHECK",
        "open": "  Open Image",
        "save": "  Export PNG",
        "replacement_header": "REPLACEMENT COLOR",
        "groups_header": "GROUPS BY COLOR",
        "fix_btn": "FIX SELECTION",
        "info": "Hold [Space] to pan",
        "detect_title": "<b>DETECTION (PATTERNS)</b>",
        "preview_title": "<b>LIVE PREVIEW (RESULT)</b>",
        "pattern": "Pattern",
        "cl_name": "Cluster",
        "brush_mode": "Brush Mode",
        "choose_color": "Pick a color",
        "toggle_outline_on": "VIEW: OUTLINE COLORS",
        "toggle_outline_off": "VIEW: ALL COLORS",
        "layer_title": "Layers",
        "pp_checkbox": "Pixel Perfect",
        "tooltip_open": "Open an image",
        "tooltip_save": "Export image (Ctrl+S)",
        "tooltip_brush": "Brush Tool (P)",
        "tooltip_select": "Selection Tool (S)\nShift: Remove\nCtrl: Add\nCtrl+C/V: Copy/Paste",
        "tooltip_pipette": "Eye Dropper (O)",
        "tooltip_add": "Add new layer",
        "tooltip_del": "Delete selected layer",
        "tooltip_merge": "Merge selected layers",
        "tooltip_up": "Move layer up",
        "tooltip_down": "Move layer down",
        "tooltip_nocolor": "Remove color (D)",
    },
}

STYLESHEET = """
    QWidget#mainCanvas { background-color: #28292E; }
    QFrame#sidebar { background-color: #2C2D32; border-right: 1px solid #282c34; }
    QFrame#workArea { background-color: #28292E; }
    QFrame#toolPanel { background-color: #21252b; border-radius: 12px; border: 1px solid #282c34; }
    QLabel { color: #a0a0a5; font-size: 11px; font-family: 'Segoe UI', sans-serif; font-weight: bold; }
    QPushButton { 
        background-color: #232328; color: #efefef; border: 1px solid #2d2d33; 
        padding: 10px; border-radius: 8px; font-weight: 600; text-align: left;
    }
    QPushButton:hover { background-color: #2d2d33; border-color: #3d3d45; }
    
    QComboBox#langCombo {
        background-color: #21252b; color: #00c3ff; border: 1px solid #282c34;
        border-radius: 6px; padding: 4px 8px; font-weight: bold; font-size: 11px;
    }
    QComboBox#langCombo QAbstractItemView { background-color: #21252b; selection-background-color: #25252f; color: #00c3ff; border: 1px solid #282c34; }

    #colorPreviewBtn { border-radius: 10px; border: 2px solid #333; padding: 0px; }
    #toolBtn { border-radius: 10px; background-color: #222; text-align: center; padding: 0px; }
    #toolBtn:hover { background-color: #333; border-color: #00c3ff; }
    
    QTreeWidget { 
        background: #21252b; border: 1px solid #282c34; border-radius: 8px; 
        outline: none; color: #d0d0d5;
    }
    QTreeWidget::item { padding: 6px; border-bottom: 1px solid #212126; }
    QTreeWidget::item:selected { background-color: #25252f; color: #00c3ff; }
    QScrollArea { border: 1px solid #282c34; border-radius: 12px; background: #404040; }
"""

LAYER_LIST_STYLE = """
    QTreeWidget {
        background: #21252b; 
        border: 1px solid #282c34; 
        border-radius: 4px;
        font-size: 12px;
    }
    QTreeWidget::item { 
        height: 40px; 
        border-bottom: 1px solid #282c34;
        padding-left: 5px;
    }
    QTreeWidget::item:selected { 
        background-color: #3e4451; 
        color: #ffffff;
    }
    QTreeWidget::item:hover {
        background-color: #2c313a;
    }
"""


class ErrorLayer:
    def __init__(self, id, x, y, color_key, category="OT", category_color=None):
        self.id = id
        self.x = x
        self.y = y
        self.color_key = color_key
        self.category = category
        self.category_color = category_color


class AnalysisResult:
    def __init__(self):
        self.layers = []
        self.pixel_to_layers = {}
        self.outline_colors = set()
        self.unique_colors = []
        self.img_np = None


class IconFactory:

    @staticmethod
    def create_selection_icon(size=QSize(32, 32)):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#00c3ff"), 4)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRect(4, 4, 32, 32)

        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.setBrush(Qt.GlobalColor.white)
        cursor = [QPoint(18, 18), QPoint(18, 26), QPoint(21, 23), QPoint(26, 26)]
        painter.drawPolygon(cursor)

        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_tool_icon(name):
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if name == "eyedropper":
            painter.setPen(QPen(Qt.GlobalColor.white, 4))
            triangle = [QPoint(14, 55), QPoint(22, 50), QPoint(30, 55)]
            painter.drawPolygon(triangle)
            painter.setPen(QPen(Qt.GlobalColor.black, 10))
            painter.drawLine(20, 44, 44, 20)
            painter.setPen(QPen(Qt.GlobalColor.white, 4))
            painter.drawLine(20, 44, 44, 20)
            painter.setPen(QPen(Qt.GlobalColor.black, 5))
            painter.drawRect(40, 10, 14, 14)
            painter.drawRect(45, 12, 5, 10)
            painter.drawLine(50, 35, 28, 15)

        elif name == "cross":
            painter.setPen(QPen(QColor(255, 60, 60), 5))
            margin = 16
            painter.drawLine(margin, margin, 64 - margin, 64 - margin)
            painter.drawLine(64 - margin, margin, margin, 64 - margin)

        elif name == "brush":
            black, white = Qt.GlobalColor.black, Qt.GlobalColor.white
            painter.setPen(QPen(black, 14))
            painter.drawLine(20, 55, 44, 20)
            painter.setPen(QPen(black, 20))
            painter.setBrush(black)
            painter.drawEllipse(40, 10, 5, 20)
            painter.setPen(QPen(black, 2))
            painter.drawPolygon([QPoint(45, 35), QPoint(45, 5), QPoint(60, 10)])
            painter.setPen(QPen(QColor(200, 140, 10), 7))
            painter.drawLine(20, 55, 44, 20)
            painter.setPen(QPen(white, 10))
            painter.setBrush(white)
            painter.drawEllipse(40, 10, 5, 20)
            painter.setPen(QPen(white, 1))
            painter.drawPolygon([QPoint(45, 35), QPoint(45, 5), QPoint(55, 10)])
            for pts, color in [
                ([QPoint(45, 35), QPoint(45, 20), QPoint(55, 10)], QColor(230, 40, 80)),
                (
                    [QPoint(45, 20), QPoint(45, 5), QPoint(55, 10)],
                    QColor(100, 100, 230),
                ),
            ]:
                painter.setBrush(color)
                painter.setPen(QPen(color, 2))
                painter.drawPolygon(pts)

        elif name == "pen":
            silver = QColor("#C0C0C0")
            dark_silver = QColor("#808080")
            gold = QColor("#D4AF37")

            painter.setPen(QPen(dark_silver, 1))
            painter.setBrush(silver)
            points = [
                QPoint(32, 55),
                QPoint(20, 30),
                QPoint(32, 5),
                QPoint(44, 30),
            ]
            painter.drawPolygon(points)

            painter.setPen(QPen(dark_silver, 2))
            painter.drawLine(32, 55, 32, 35)
            painter.setBrush(dark_silver)
            painter.drawEllipse(30, 32, 4, 4)

            painter.setBrush(gold)
            painter.setPen(Qt.GlobalColor.transparent)
            painter.drawRect(28, 5, 8, 10)

        painter.end()
        return QIcon(pix)

    @staticmethod
    def create_action_icon(name):
        pix = QPixmap(32, 32)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#d0d0d5")
        painter.setPen(QPen(color, 2))

        if name == "add":
            painter.drawLine(16, 8, 16, 24)
            painter.drawLine(8, 16, 24, 16)
        elif name == "del":
            painter.drawRect(10, 12, 12, 14)
            painter.drawLine(8, 12, 24, 12)
            painter.drawLine(14, 10, 18, 10)
        elif name == "up":
            painter.drawLine(16, 8, 16, 24)
            painter.drawLine(16, 8, 10, 14)
            painter.drawLine(16, 8, 22, 14)
        elif name == "down":
            painter.drawLine(16, 8, 16, 24)
            painter.drawLine(16, 24, 10, 18)
            painter.drawLine(16, 24, 22, 18)
        elif name == "merge":
            painter.drawLine(10, 8, 16, 16)
            painter.drawLine(22, 8, 16, 16)
            painter.drawLine(16, 16, 16, 24)

        painter.end()
        return QIcon(pix)

    @staticmethod
    def create_state_icon(icon_type, state):
        pix = QPixmap(20, 20)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color_active = QColor("#d0d0d5")
        color_inactive = QColor("#555555")

        if icon_type == "eye":
            if state:
                painter.setPen(QPen(color_active, 2))
                painter.drawEllipse(2, 5, 16, 10)
                painter.setBrush(color_active)
                painter.drawEllipse(8, 8, 4, 4)
            else:
                painter.setPen(QPen(color_inactive, 2))
                painter.drawEllipse(2, 5, 16, 10)
                painter.drawLine(3, 3, 17, 17)
        elif icon_type == "lock":
            if state:
                painter.setPen(QPen(QColor("#FC7D2B"), 2))
                painter.drawRect(5, 8, 10, 8)
                painter.drawArc(7, 2, 6, 8, 0, 180 * 16)
            else:
                painter.setPen(QPen(color_inactive, 1))
                painter.drawRect(5, 9, 10, 7)
                painter.drawLine(10, 9, 10, 7)

        painter.end()
        return QIcon(pix)

    @staticmethod
    def create_thumbnail(pil_img, size=32):
        thumb = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        aspect = pil_img.width / pil_img.height
        if aspect > 1:
            new_w = size
            new_h = int(size / aspect)
        else:
            new_h = size
            new_w = int(size * aspect)

        small_img = pil_img.resize((new_w, new_h), Image.Resampling.NEAREST)
        offset_x = (size - new_w) // 2
        offset_y = (size - new_h) // 2
        thumb.paste(small_img, (offset_x, offset_y))

        data = thumb.tobytes("raw", "RGBA")
        qim = QImage(data, size, size, QImage.Format.Format_RGBA8888)
        return QIcon(QPixmap.fromImage(qim))


class ImageAnalyzer:
    CL_PATTERN_1 = np.array([[2, 1, 1], [2, 3, 1], [2, 2, 2]])
    CL_PATTERN_2 = np.array([[1, 1, 2], [1, 3, 2], [2, 2, 2]])
    OT_PATTERN = np.array([[2, 1, 0], [2, 3, 1], [2, 1, 0]])

    BASE_PATTERN = np.array([[2, 1, 0], [2, 3, 1], [0, 2, 2]])

    OSC_PATTERN_1 = np.array([[2, 4, 0], [2, 3, 2], [0, 2, 2]])
    OSC_PATTERN_2 = np.array([[2, 2, 0], [2, 3, 4], [0, 2, 2]])
    SC_PATTERN = np.array([[2, 4, 0], [2, 3, 4], [0, 2, 2]])

    def __init__(self):
        self.cl_rotations = [np.rot90(self.CL_PATTERN_1, k) for k in range(4)] + [
            np.rot90(self.CL_PATTERN_2, k) for k in range(4)
        ]
        self.ot_rotations = [np.rot90(self.OT_PATTERN, k) for k in range(4)]

        self.base_rotations = [np.rot90(self.BASE_PATTERN, k) for k in range(4)]

        self.osc_rotations = [np.rot90(self.OSC_PATTERN_1, k) for k in range(4)] + [
            np.rot90(self.OSC_PATTERN_2, k) for k in range(4)
        ]

        self.sc_rotations = [np.rot90(self.SC_PATTERN, k) for k in range(4)]

    def analyze_matrix(self, matrix):
        h, w = matrix.shape
        corrected_matrix = matrix.copy()

        rows, cols = np.where(matrix == 1)

        for i in range(len(rows)):
            y, x = rows[i], cols[i]
            if 0 < y < h - 1 and 0 < x < w - 1:
                sub_mask = corrected_matrix[y - 1 : y + 2, x - 1 : x + 2]
                if any(
                    self._check_pattern_match_optimized(rot, sub_mask)
                    for rot in self.base_rotations
                ):
                    corrected_matrix[y, x] = 0

        return corrected_matrix

    def analyze(self, pil_image):
        result = AnalysisResult()
        if not pil_image:
            return result

        result.img_np = np.array(pil_image)
        h, w, _ = result.img_np.shape
        result.unique_colors = np.unique(result.img_np.reshape(-1, 4), axis=0)
        alpha = result.img_np[:, :, 3]
        is_opaque = alpha > 0
        is_trans = alpha == 0
        trans_padded = np.pad(is_trans, 1, constant_values=True)
        t_up = trans_padded[:-2, 1:-1]
        t_down = trans_padded[2:, 1:-1]
        t_left = trans_padded[1:-1, :-2]
        t_right = trans_padded[1:-1, 2:]
        has_trans_neighbor = t_up | t_down | t_left | t_right
        is_outline = is_opaque & has_trans_neighbor
        outline_pixels = result.img_np[is_outline]

        if outline_pixels.size > 0:
            u_out_colors = np.unique(outline_pixels.reshape(-1, 4), axis=0)
            result.outline_colors = set(tuple(c) for c in u_out_colors)
        color_count = {}
        img_np = result.img_np

        for y in range(h):
            for x in range(w):
                color = tuple(img_np[y, x])
                if color[3] < 10:
                    continue
                y_start = max(0, y - 1)
                y_end = min(h, y + 2)
                x_start = max(0, x - 1)
                x_end = min(w, x + 2)

                sub_region = img_np[y_start:y_end, x_start:x_end]
                sub_mask = np.all(sub_region == color, axis=-1)
                mask_3x3 = np.zeros((3, 3), dtype=bool)
                mask_y_offset = 1 - (y - y_start)
                mask_x_offset = 1 - (x - x_start)

                for dy in range(sub_region.shape[0]):
                    for dx in range(sub_region.shape[1]):
                        mask_y = mask_y_offset + dy
                        mask_x = mask_x_offset + dx
                        if 0 <= mask_y < 3 and 0 <= mask_x < 3:
                            mask_3x3[mask_y, mask_x] = sub_mask[dy, dx]

                if any(
                    self._check_pattern_match_optimized(rot, mask_3x3)
                    for rot in self.cl_rotations
                ):
                    if color not in color_count:
                        color_count[color] = []
                    color_count[color].append((x, y, "CL"))

                if any(
                    self._check_pattern_match_optimized(rot, mask_3x3)
                    for rot in self.ot_rotations
                ):
                    if color not in color_count:
                        color_count[color] = []
                    color_count[color].append((x, y, "OT"))
                elif any(
                    self._check_pattern_match_optimized(rot, mask_3x3)
                    for rot in self.base_rotations
                ):
                    if color not in color_count:
                        color_count[color] = []
                    color_count[color].append((x, y, "BAD"))
        for color_tuple, pixels in color_count.items():
            for x, y, p_type in pixels:
                lid = len(result.layers)
                new_layer = ErrorLayer(lid, x, y, color_tuple)

                if p_type == "CL":
                    self._apply_category_style(new_layer, "CL")
                elif p_type == "OT":
                    self._apply_category_style(new_layer, "OT")
                else:
                    self._apply_category_style(new_layer, "CR")

                result.layers.append(new_layer)

                if (x, y) not in result.pixel_to_layers:
                    result.pixel_to_layers[(x, y)] = []
                result.pixel_to_layers[(x, y)].append(lid)
        bad_pixel_mask = np.zeros((h, w), dtype=bool)
        for layer in result.layers:
            bad_pixel_mask[layer.y, layer.x] = True

        self._categorize_errors(result.layers, img_np, bad_pixel_mask)
        return result

    def _check_pattern_match_optimized(self, pattern, sub_mask):
        for r in range(3):
            for c in range(3):
                p_val = pattern[r, c]
                m_val = sub_mask[r, c]
                if (p_val == 3 or p_val == 1) and not m_val:
                    return False
                if p_val == 0 and m_val:
                    return False
        return True

    def _apply_category_style(self, layer, pattern_type):
        styles = {
            "CL": (QColor(115, 0, 115), "CL"),
            "SC": (QColor(255, 0, 0), "SC"),
            "OSC": (QColor(255, 155, 0), "OSC"),
            "OT": (QColor(255, 0, 200), "OT"),
            "CR": (QColor(255, 255, 0), "CR"),
        }
        color, code = styles.get(pattern_type, (QColor(255, 255, 0), "CR"))
        layer.category = code
        layer.category_color = color

    def _check_full_pattern_match(self, pattern, color_mask, bad_pixel_mask):
        for r in range(3):
            for c in range(3):
                p_val = pattern[r, c]
                if p_val == 2 or p_val == 3:
                    continue
                color_val = color_mask[r, c]
                if p_val == 1 and not color_val:
                    return False
                if p_val == 0 and color_val:
                    return False
                if p_val == 4 and (not color_val or not bad_pixel_mask[r, c]):
                    return False
        return True

    def _categorize_errors(self, layers, img_np, bad_pixel_mask):
        h, w, _ = img_np.shape
        other_layers = [l for l in layers if l.category != "CL" and l.category != "OT"]
        for layer in other_layers:
            x, y = layer.x, layer.y
            if y < 1 or y >= h - 1 or x < 1 or x >= w - 1:
                self._apply_category_style(layer, "CR")
                continue

            layer_color = layer.color_key
            color_mask = np.all(
                img_np[y - 1 : y + 2, x - 1 : x + 2] == layer_color, axis=-1
            )
            bad_mask = color_mask & bad_pixel_mask[y - 1 : y + 2, x - 1 : x + 2]

            if any(
                self._check_full_pattern_match(rot, color_mask, bad_mask)
                for rot in self.osc_rotations
            ):
                self._apply_category_style(layer, "OSC")
                if any(
                    self._check_full_pattern_match(rot, color_mask, bad_mask)
                    for rot in self.sc_rotations
                ):
                    self._apply_category_style(layer, "SC")
            else:
                self._apply_category_style(layer, "CR")
        pos_to_layer = {(l.x, l.y): l for l in layers}
        staircase_layers = [l for l in layers if l.category == "SC"]
        queue = list(staircase_layers)

        while queue:
            current = queue.pop(0)
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    neighbor_pos = (current.x + dx, current.y + dy)
                    if neighbor_pos in pos_to_layer:
                        neighbor = pos_to_layer[neighbor_pos]
                        if neighbor.category in ["OSC", "CR"]:
                            self._apply_category_style(neighbor, "SC")
                            queue.append(neighbor)


class PixelCanvas(QWidget):
    pixelSelected = pyqtSignal(int, bool)
    colorPicked = pyqtSignal(QColor)
    brushPainted = pyqtSignal(int, int)
    brushFinished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent_app = parent
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.last_brush_pos = None
        self.original_pixmap = None
        self.zoom = 6.0
        self.error_map = {}
        self.visible_layers = set()
        self.selected_layers = set()
        self.layers = []

        self.offset_x = 0.0
        self.offset_y = 0.0
        self.is_dragging = False
        self.drag_start = QPoint()
        self.drag_offset_start = (0.0, 0.0)

        self.picker_mode = False
        self.brush_mode = False
        self.drag_mode = False
        self.selection_mode = False
        self.current_selection = set()
        self.pen_mode = False
        self.pen_points = []
        self.pen_drag_index = None
        self.selected_point = None
        self.checker_brush = self._create_checker_brush()
        self.pen_preview_pixmap = None
        self.pen_color = (255, 0, 0, 255)

    def _create_checker_brush(self):
        size = 20
        pixmap = QPixmap(size * 2, size * 2)
        pixmap.fill(QColor("#D3D4D4"))
        painter = QPainter(pixmap)
        color_dark = QColor("#949A98")
        painter.fillRect(0, 0, size, size, color_dark)
        painter.fillRect(size, size, size, size, color_dark)
        painter.end()
        return QBrush(pixmap)

    def set_image(self, pixmap, error_map=None, reset_view=True):
        self.original_pixmap = pixmap
        self.error_map = error_map if error_map is not None else {}
        if reset_view and self.original_pixmap:
            self._center_image()
        self.update()

    def _center_image(self):
        w_canvas, h_canvas = self.width(), self.height()
        w_img, h_img = self.original_pixmap.width(), self.original_pixmap.height()
        self.offset_x = (w_img - w_canvas / self.zoom) / 2
        self.offset_y = (h_img - h_canvas / self.zoom) / 2

    def set_layers(self, layers):
        self.layers = layers

    def get_layer_color(self, layer_id):
        if layer_id < len(self.layers):
            layer = self.layers[layer_id]
            if layer.category_color:
                c = layer.category_color
                return QColor(c.red(), c.green(), c.blue(), 255)
        return QColor(0, 0, 0, 150)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.checker_brush)

        if not self.original_pixmap:
            painter.end()
            return

        temp_pixmap = self.original_pixmap.copy()
        if self.error_map:
            self._draw_error_overlay(temp_pixmap)

        screen_x = int(-self.offset_x * self.zoom)
        screen_y = int(-self.offset_y * self.zoom)
        scaled_size = temp_pixmap.size() * self.zoom
        scaled_pixmap = temp_pixmap.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

        painter.drawPixmap(screen_x, screen_y, scaled_pixmap)
        if self.current_selection:
            pen = QPen(QColor(0, 195, 255), 2)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)
            for px, py in self.current_selection:
                sx = int((px - self.offset_x) * self.zoom)
                sy = int((py - self.offset_y) * self.zoom)
                sz = int(self.zoom)
                painter.drawRect(sx, sy, sz, sz)

        if self.pen_mode and len(self.pen_points) > 1:
            try:
                all_pixels = self.get_pixels_on_pen_line_for_display()

                if self.parent_app and self.parent_app.pixel_perfect_mode:
                    all_pixels = self.apply_pixel_perfect_filter(all_pixels)

                preview_color = QColor(255, 0, 0, 255)
                if self.parent_app and self.parent_app.replacement_color:
                    c = self.parent_app.replacement_color
                    preview_color = QColor(c.red(), c.green(), c.blue(), 255)

                for px, py in all_pixels:
                    screen_px = int((px - self.offset_x) * self.zoom)
                    screen_py = int((py - self.offset_y) * self.zoom)
                    painter.fillRect(
                        screen_px,
                        screen_py,
                        int(self.zoom),
                        int(self.zoom),
                        preview_color,
                    )
            except Exception:
                pass

        if self.pen_mode and len(self.pen_points) > 0:
            brush_color = QColor(0, 255, 0, 255)

            for px, py in self.pen_points:
                sx = int((px - self.offset_x) * self.zoom)
                sy = int((py - self.offset_y) * self.zoom)
                sz = int(self.zoom)

                painter.fillRect(sx, sy, sz, sz, brush_color)

            if len(self.pen_points) > 1:
                pen_color = QColor(0, 255, 0)
                line_width = max(1.0, self.zoom / 16.0)

                pen = QPen(pen_color, line_width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)

                for i in range(len(self.pen_points) - 1):
                    p1 = self.pen_points[i]
                    p2 = self.pen_points[i + 1]

                    x1 = int((p1[0] - self.offset_x) * self.zoom + self.zoom / 2)
                    y1 = int((p1[1] - self.offset_y) * self.zoom + self.zoom / 2)
                    x2 = int((p2[0] - self.offset_x) * self.zoom + self.zoom / 2)
                    y2 = int((p2[1] - self.offset_y) * self.zoom + self.zoom / 2)

                    painter.drawLine(x1, y1, x2, y2)

        painter.end()

    def _draw_error_overlay(self, pixmap):
        temp_painter = QPainter(pixmap)
        for (x, y), layer_ids in self.error_map.items():
            for lid in layer_ids:
                if lid in self.visible_layers:
                    color = self.get_layer_color(lid)
                    if lid in self.selected_layers:
                        color = QColor(0, 200, 255, 200)
                    temp_painter.fillRect(x, y, 1, 1, color)
        temp_painter.end()

    def get_pixels_on_pen_line_for_display(self):
        if len(self.pen_points) < 2:
            return []

        all_pixels = []
        for i in range(len(self.pen_points) - 1):
            x1, y1 = self.pen_points[i]
            x2, y2 = self.pen_points[i + 1]

            if self.parent_app and self.parent_app.pixel_perfect_mode:
                all_pixels.extend(self.bresenham_line(x1, y1, x2, y2))
            else:
                all_pixels.extend(self.get_line_pixels_for_display(x1, y1, x2, y2))

        return all_pixels

    def bresenham_line(self, x0, y0, x1, y1):
        dx = x1 - x0
        dy = y1 - y0
        incX = 1 if dx > 0 else (-1 if dx < 0 else 0)
        incY = 1 if dy > 0 else (-1 if dy < 0 else 0)
        dx = abs(dx)
        dy = abs(dy)

        pixels = []

        if dy == 0:
            x = x0
            while x != x1 + incX:
                pixels.append((x, y0))
                x += incX
        elif dx == 0:
            y = y0
            while y != y1 + incY:
                pixels.append((x0, y))
                y += incY
        elif dx >= dy:
            slope = 2 * dy
            error = -dx
            errorInc = -2 * dx
            y = y0
            x = x0
            while x != x1 + incX:
                pixels.append((x, y))
                error += slope
                if error >= 0:
                    y += incY
                    error += errorInc
                x += incX
        else:
            slope = 2 * dx
            error = -dy
            errorInc = -2 * dy
            x = x0
            y = y0
            while y != y1 + incY:
                pixels.append((x, y))
                error += slope
                if error >= 0:
                    x += incX
                    error += errorInc
                y += incY

        return pixels

    def _compute_bresenham_line(self, x1, y1, x2, y2, perfect_diag=True):
        pixels = [(x1, y1)]
        delta_x = x2 - x1
        delta_y = y2 - y1
        step_y = 1 if delta_y > 0 else -1
        delta_y = abs(delta_y)
        step_x = 1 if delta_x > 0 else -1
        delta_x = abs(delta_x)
        two_delta_y = 2 * delta_y
        two_delta_x = 2 * delta_x
        curr_x, curr_y = x1, y1

        if two_delta_x >= two_delta_y:
            error = delta_x
            error_prev = delta_x
            for _ in range(delta_x):
                curr_x += step_x
                error += two_delta_y
                if error > two_delta_x:
                    curr_y += step_y
                    error -= two_delta_x
                    if error + error_prev < two_delta_x:
                        pixels.append((curr_x, curr_y - step_y))
                    elif error + error_prev > two_delta_x:
                        pixels.append((curr_x - step_x, curr_y))
                    elif not perfect_diag:
                        pixels.append((curr_x, curr_y - step_y))
                        pixels.append((curr_x - step_x, curr_y))
                pixels.append((curr_x, curr_y))
                error_prev = error
        else:
            error = delta_y
            error_prev = delta_y
            for _ in range(delta_y):
                curr_y += step_y
                error += two_delta_x
                if error > two_delta_y:
                    curr_x += step_x
                    error -= two_delta_y
                    if error + error_prev < two_delta_y:
                        pixels.append((curr_x - step_x, curr_y))
                    elif error + error_prev > two_delta_y:
                        pixels.append((curr_x, curr_y - step_y))
                    elif not perfect_diag:
                        pixels.append((curr_x - step_x, curr_y))
                        pixels.append((curr_x, curr_y - step_y))
                pixels.append((curr_x, curr_y))
                error_prev = error
        return pixels

    def get_line_pixels_for_display(self, x1, y1, x2, y2, perfect_diag=True):
        return self._compute_bresenham_line(x1, y1, x2, y2, perfect_diag)

    def apply_pixel_perfect_filter(self, pixels):
        return pixels

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        prev_zoom = self.zoom
        self.zoom *= 1.1 if delta > 0 else (1 / 1.1)
        self.zoom = max(0.5, min(self.zoom, 100.0))

        mouse_x, mouse_y = event.position().x(), event.position().y()
        world_x = mouse_x / prev_zoom + self.offset_x
        world_y = mouse_y / prev_zoom + self.offset_y

        self.offset_x = world_x - mouse_x / self.zoom
        self.offset_y = world_y - mouse_y / self.zoom
        self.update()

    def mousePressEvent(self, event: QMouseEvent):

        x = int(event.position().x() / self.zoom + self.offset_x)
        y = int(event.position().y() / self.zoom + self.offset_y)

        if self.pen_mode:
            if event.button() == Qt.MouseButton.LeftButton:
                for i, pt in enumerate(self.pen_points):
                    if pt == (x, y):
                        self.pen_drag_index = i
                        self.selected_point = (x, y)
                        break
                if self.pen_drag_index is None:
                    if not self.pen_points or self.pen_points[-1] != (x, y):
                        self.pen_points.append((x, y))
                        self.pen_drag_index = len(self.pen_points) - 1

                self.update()
                return

            elif event.button() == Qt.MouseButton.RightButton:
                for i, pt in enumerate(self.pen_points):
                    if pt == (x, y):
                        self.pen_points.pop(i)
                        self.brushFinished.emit()
                        self.update()
                        return

        if self.drag_mode or event.button() == Qt.MouseButton.RightButton:
            self.is_dragging = True
            self.drag_start = event.globalPosition().toPoint()
            self.drag_offset_start = (self.offset_x, self.offset_y)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if self.selection_mode and event.button() == Qt.MouseButton.LeftButton:
            modifiers = event.modifiers()
            if not (
                modifiers & Qt.KeyboardModifier.ControlModifier
                or modifiers & Qt.KeyboardModifier.ShiftModifier
            ):
                parent = self.window()
                if hasattr(parent, "deselect_all"):
                    parent.deselect_all()
            self.last_brush_pos = QPoint(x, y)
            self.brushPainted.emit(x, y)
            return

        if self.picker_mode:
            if self.original_pixmap:
                img = self.original_pixmap.toImage()
                if 0 <= x < img.width() and 0 <= y < img.height():
                    self.colorPicked.emit(img.pixelColor(x, y))
            return

        if self.brush_mode or self.selection_mode:
            self.last_brush_pos = QPoint(x, y)
            self.brushPainted.emit(x, y)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if (x, y) in self.error_map:
                add_to = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
                self.pixelSelected.emit(self.error_map[(x, y)][0], add_to)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            delta = event.globalPosition().toPoint() - self.drag_start
            self.offset_x = self.drag_offset_start[0] - delta.x() / self.zoom
            self.offset_y = self.drag_offset_start[1] - delta.y() / self.zoom
            self.update()
            return
        if self.pen_mode:
            x = int(event.position().x() / self.zoom + self.offset_x)
            y = int(event.position().y() / self.zoom + self.offset_y)

            if self.pen_drag_index is not None:
                self.pen_points[self.pen_drag_index] = (x, y)
                self.update()
            return

        if not self.drag_mode:
            if self.picker_mode:
                self.setCursor(Qt.CursorShape.CrossCursor)
            elif self.brush_mode:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                if event.buttons() & Qt.MouseButton.LeftButton:
                    x = int(event.position().x() / self.zoom + self.offset_x)
                    y = int(event.position().y() / self.zoom + self.offset_y)
                    current_pos = QPoint(x, y)
                    if self.last_brush_pos is not None:
                        self._interpolate_line(self.last_brush_pos, current_pos)
                    else:
                        self.brushPainted.emit(x, y)
                    self.last_brush_pos = current_pos
            elif self.selection_mode:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    x = int(event.position().x() / self.zoom + self.offset_x)
                    y = int(event.position().y() / self.zoom + self.offset_y)
                    current_pos = QPoint(x, y)
                    if self.last_brush_pos is not None:
                        self._interpolate_line(self.last_brush_pos, current_pos)
                    else:
                        self.brushPainted.emit(x, y)
                    self.last_brush_pos = current_pos

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging = False
        self.last_brush_pos = None
        self.pen_drag_index = None

        if self.pen_mode and event.button() == Qt.MouseButton.LeftButton:
            x = int(event.position().x() / self.zoom + self.offset_x)
            y = int(event.position().y() / self.zoom + self.offset_y)
            if not self.pen_points or (
                self.selected_point == (x, y)
                and self.pen_points[-1] != (x, y)
                and self.pen_points[-2] != (x, y)
            ):
                print(
                    f"Adding point ({x}, {y}) to pen points. et selected_point: {self.selected_point}"
                )
                self.pen_points.append((x, y))
                self.update()

        if self.brush_mode and event.button() == Qt.MouseButton.LeftButton:
            self.brushFinished.emit()

        if self.drag_mode:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif self.picker_mode:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self.brush_mode:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _interpolate_line(self, p1, p2):
        curr_x, curr_y = p1.x(), p1.y()
        target_x, target_y = p2.x(), p2.y()

        delta_x = abs(target_x - curr_x)
        delta_y = abs(target_y - curr_y)
        step_x = 1 if curr_x < target_x else -1
        step_y = 1 if curr_y < target_y else -1
        error = delta_x - delta_y

        while True:
            self.brushPainted.emit(curr_x, curr_y)
            if curr_x == target_x and curr_y == target_y:
                break
            error_times_2 = 2 * error
            if error_times_2 > -delta_y:
                error -= delta_y
                curr_x += step_x
            if error_times_2 < delta_x:
                error += delta_x
                curr_y += step_y


class OutlineCheckApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = "EN"
        self.setWindowTitle("OutlineCheck - OTC Software")
        self.setWindowIcon(QIcon("OutlineCheck.ico"))
        self.resize(1400, 950)
        self.setStyleSheet(STYLESHEET)
        self.history = []
        self.history_index = -1
        self.current_img = None
        self.pixel_layers = []
        self.replacement_color = None
        self.show_only_outlines = True
        self.analyzer = ImageAnalyzer()
        self.analysis_result = AnalysisResult()
        self.pixel_perfect_mode = False
        self.last_brush_position = None
        self.temp_stroke_layer = None
        self.active_layer_index = None
        self._init_ui()
        self._setup_shortcuts()
        self._load_default_state()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _init_ui(self):
        central = QWidget()
        central.setObjectName("mainCanvas")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_sidebar(main_layout)
        self._create_work_area(main_layout)
        self.update_tooltips()

    def _create_sidebar(self, parent_layout):
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        header_row = QHBoxLayout()
        self.title_label = QLabel(LANGUAGES[self.current_lang]["title"])
        self.title_label.setStyleSheet(
            "font-size: 22px; font-weight: 900; color: #FC7D2B; letter-spacing: 2px;"
        )
        header_row.addWidget(self.title_label)
        header_row.addStretch()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["EN", "FR"])
        self.lang_combo.setFixedWidth(60)
        self.lang_combo.setObjectName("langCombo")
        self.lang_combo.currentTextChanged.connect(self.change_language)
        header_row.addWidget(self.lang_combo)
        layout.addLayout(header_row)
        self.btn_open = QPushButton(LANGUAGES[self.current_lang]["open"])
        self.btn_open.clicked.connect(self.open_image)
        self.btn_save = QPushButton(LANGUAGES[self.current_lang]["save"])
        self.btn_save.clicked.connect(self.save_image)
        layout.addWidget(self.btn_open)
        layout.addWidget(self.btn_save)
        self._create_tool_panel(layout)
        group_row = QHBoxLayout()
        self.groups_label = QLabel(LANGUAGES[self.current_lang]["groups_header"])
        group_row.addWidget(self.groups_label)
        group_row.addStretch()
        layout.addLayout(group_row)
        self.btn_toggle_outline = QPushButton()
        self.btn_toggle_outline.clicked.connect(self.toggle_outline_view)
        self.btn_toggle_outline.setStyleSheet(
            "background-color: #3A3B42; color: #FC7D2B; font-size: 10px;"
        )
        self.update_toggle_text()
        layout.addWidget(self.btn_toggle_outline)
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderHidden(True)
        self.layer_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.layer_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.layer_tree.itemChanged.connect(self.on_item_visibility_changed)
        layout.addWidget(self.layer_tree)
        self.info_label = QLabel(LANGUAGES[self.current_lang]["info"])
        self.info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.info_label)

        parent_layout.addWidget(sidebar)

    def _create_tool_panel(self, parent_layout):
        panel = QFrame()
        panel.setObjectName("toolPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.pipette_header = QLabel(LANGUAGES[self.current_lang]["replacement_header"])
        self.pipette_header.setStyleSheet(
            "color: #888; font-size: 10px; letter-spacing: 1px;"
        )
        layout.addWidget(self.pipette_header)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.pipette_header)
        header_layout.addStretch()

        self.pp_check = QCheckBox(LANGUAGES[self.current_lang]["pp_checkbox"])
        self.pp_check.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        self.pp_check.toggled.connect(self.toggle_pixel_perfect)
        header_layout.addWidget(self.pp_check)

        layout.addLayout(header_layout)

        row = QHBoxLayout()
        row.setSpacing(10)

        self.btn_brush = QPushButton()
        self.btn_brush.setFixedSize(48, 48)
        self.btn_brush.setObjectName("toolBtn")
        self.btn_brush.setIcon(IconFactory.create_tool_icon("brush"))
        self.btn_brush.setIconSize(QSize(28, 28))
        self.btn_brush.clicked.connect(self.toggle_brush_mode)
        row.addWidget(self.btn_brush)

        self.btn_select = QPushButton()
        self.btn_select.setIcon(IconFactory.create_selection_icon())
        self.btn_select.setFixedSize(48, 48)
        self.btn_select.setObjectName("toolBtn")
        self.btn_select.clicked.connect(self.toggle_selection_mode)
        row.addWidget(self.btn_select)

        self.btn_eye_dropper = QPushButton()
        self.btn_eye_dropper.setFixedSize(48, 48)
        self.btn_eye_dropper.setObjectName("toolBtn")
        self.btn_eye_dropper.setIcon(IconFactory.create_tool_icon("eyedropper"))
        self.btn_eye_dropper.setIconSize(QSize(28, 28))
        self.btn_eye_dropper.clicked.connect(self.toggle_picker_mode)
        row.addWidget(self.btn_eye_dropper)

        self.btn_pen = QPushButton()
        self.btn_pen.setFixedSize(48, 48)
        self.btn_pen.setObjectName("toolBtn")
        self.btn_pen.setIcon(IconFactory.create_tool_icon("pen"))
        self.btn_pen.setIconSize(QSize(32, 32))
        self.btn_pen.clicked.connect(self.toggle_pen_mode)
        row.addWidget(self.btn_pen)

        row.addStretch()
        layout.addLayout(row)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.btn_color_preview = QPushButton()
        self.btn_color_preview.setObjectName("colorPreviewBtn")
        self.btn_color_preview.setFixedSize(48, 48)
        self.btn_color_preview.clicked.connect(self.open_color_dialog)
        self.update_picker_button_ui()
        self.btn_trans = QPushButton(self.btn_color_preview)
        self.btn_trans.setFixedSize(18, 18)
        self.btn_trans.setObjectName("toolBtn")
        self.btn_trans.setIcon(IconFactory.create_tool_icon("cross"))
        self.btn_trans.setIconSize(QSize(12, 12))
        self.btn_trans.clicked.connect(self.reset_to_transparent)
        margin = 2
        self.btn_trans.move(
            self.btn_color_preview.width() - self.btn_trans.width() - margin, margin
        )

        row1.addStretch()
        row1.addWidget(self.btn_color_preview)
        layout.addLayout(row1)

        parent_layout.addWidget(panel)

    def _create_work_area(self, parent_layout):
        work_area = QFrame()
        work_area.setObjectName("workArea")
        layout = QVBoxLayout(work_area)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        left_container = QFrame()
        left_layout = QVBoxLayout(left_container)
        self.detect_label = QLabel(LANGUAGES[self.current_lang]["detect_title"])
        left_layout.addWidget(self.detect_label)
        self.canvas_left = PixelCanvas(parent=self)
        self.canvas_left.pixelSelected.connect(self.select_layer_by_id)
        self.canvas_left.colorPicked.connect(self.set_active_color)
        self.canvas_left.brushPainted.connect(
            lambda x, y: (
                self.handle_selection_draw(x, y)
                if self.canvas_left.selection_mode
                else self.paint_pixel(x, y)
            )
        )
        self.canvas_left.brushFinished.connect(
            lambda: (
                self.on_selection_finished()
                if self.canvas_left.selection_mode
                else self.on_brush_finished()
            )
        )
        left_layout.addWidget(self.canvas_left, 1)
        self._create_layers_panel()

        self.splitter.addWidget(left_container)
        self.splitter.addWidget(self.layers_panel)
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)
        parent_layout.addWidget(work_area)

    def _create_layers_panel(self):
        self.layers_panel = QFrame()
        self.layers_panel.setMinimumWidth(250)
        self.layers_panel.setObjectName("layersPanel")
        layout = QVBoxLayout(self.layers_panel)
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(5)
        self.layer_buttons = {}
        actions = [
            ("add", lambda: self.add_layer()),
            ("del", self.delete_layer),
            ("merge", self.merge_layers),
            ("up", lambda: self.move_layer(-1)),
            ("down", lambda: self.move_layer(1)),
        ]

        for icon_name, func in actions:
            btn = QPushButton()
            btn.setIcon(IconFactory.create_action_icon(icon_name))
            btn.setFixedSize(32, 32)
            btn.setIconSize(QSize(20, 20))
            btn.clicked.connect(func)
            tools_layout.addWidget(btn)
            self.layer_buttons[icon_name] = btn

        layout.addLayout(tools_layout)
        self.layers_list = QTreeWidget()
        self.layers_list.setHeaderLabels(
            ["", LANGUAGES[self.current_lang]["layer_title"]]
        )
        self.layers_list.setColumnWidth(0, 30)
        self.layers_list.setIndentation(0)
        self.layers_list.setIconSize(QSize(32, 32))
        self.layers_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.layers_list.setStyleSheet(LAYER_LIST_STYLE)
        self.layers_list.itemClicked.connect(self.handle_layer_click)
        layout.addWidget(self.layers_list)

    def _load_default_state(self):
        default_img = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
        self.current_img = default_img
        self.add_layer(name="Base Image", image=default_img)

    def _compute_bresenham_line(self, x1, y1, x2, y2, perfect_diag=True):
        pixels = [(x1, y1)]
        delta_x = x2 - x1
        delta_y = y2 - y1
        step_y = 1 if delta_y > 0 else -1
        delta_y = abs(delta_y)
        step_x = 1 if delta_x > 0 else -1
        delta_x = abs(delta_x)
        two_delta_y = 2 * delta_y
        two_delta_x = 2 * delta_x
        curr_x, curr_y = x1, y1

        if two_delta_x >= two_delta_y:
            error = delta_x
            error_prev = delta_x
            for _ in range(delta_x):
                curr_x += step_x
                error += two_delta_y
                if error > two_delta_x:
                    curr_y += step_y
                    error -= two_delta_x
                    if error + error_prev < two_delta_x:
                        pixels.append((curr_x, curr_y - step_y))
                    elif error + error_prev > two_delta_x:
                        pixels.append((curr_x - step_x, curr_y))
                    elif not perfect_diag:
                        pixels.append((curr_x, curr_y - step_y))
                        pixels.append((curr_x - step_x, curr_y))
                pixels.append((curr_x, curr_y))
                error_prev = error
        else:
            error = delta_y
            error_prev = delta_y
            for _ in range(delta_y):
                curr_y += step_y
                error += two_delta_x
                if error > two_delta_y:
                    curr_x += step_x
                    error -= two_delta_y
                    if error + error_prev < two_delta_y:
                        pixels.append((curr_x - step_x, curr_y))
                    elif error + error_prev > two_delta_y:
                        pixels.append((curr_x, curr_y - step_y))
                    elif not perfect_diag:
                        pixels.append((curr_x - step_x, curr_y))
                        pixels.append((curr_x, curr_y - step_y))
                pixels.append((curr_x, curr_y))
                error_prev = error
        return pixels

    def get_pixels_on_pen_line(self):
        if len(self.canvas_left.pen_points) < 2:
            return set()

        all_pixels = set()
        points = self.canvas_left.pen_points

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            all_pixels.update(self.get_line_pixels(x1, y1, x2, y2))
        return all_pixels

    def get_line_pixels(self, x1, y1, x2, y2, perfect_diag=True):
        return self._compute_bresenham_line(x1, y1, x2, y2, perfect_diag)

    def apply_pen_collision(self):
        if len(self.canvas_left.pen_points) < 2:
            return

        selected_items = self.layer_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            for i, layer in enumerate(self.pixel_layers):
                if layer["name"] == item.text(0):
                    self.active_layer_index = i
                    break

        if self.active_layer_index is None and len(self.pixel_layers) > 0:
            self.active_layer_index = 0

        if self.active_layer_index is None or self.active_layer_index >= len(
            self.pixel_layers
        ):
            return

        touched_pixels = self.get_pixels_on_pen_line()
        layer_data = self.pixel_layers[self.active_layer_index]
        img = layer_data["image"].copy()
        width, height = img.size
        color = self._get_active_color_tuple()
        modified = False

        if self.pixel_perfect_mode:
            for px, py in touched_pixels:
                if 0 <= px < width and 0 <= py < height:
                    img.putpixel((px, py), color)
                    modified = True
        else:
            pixel_matrix = np.zeros((height, width), dtype=np.uint8)
            for px, py in touched_pixels:
                if 0 <= px < width and 0 <= py < height:
                    pixel_matrix[py, px] = 1

            corrected_matrix = self.analyzer.analyze_matrix(pixel_matrix)
            rows, cols = np.where(corrected_matrix == 1)
            for x, y in zip(cols, rows):
                img.putpixel((x, y), color)
                modified = True

        if modified:
            layer_data["image"] = img
            self.canvas_left.pen_points = []
            self.compose_final_image()
            self.push_history()
            self.refresh_analysis()
            self.canvas_left.update()

    def _setup_shortcuts(self):
        shortcuts = {
            "Ctrl+Z": lambda: self._history_move(-1),
            "Ctrl+Shift+Z": lambda: self._history_move(1),
            "Ctrl+Y": lambda: self._history_move(1),
            "Ctrl+S": self.save_image,
            "Ctrl+C": self.copy_selection,
            "Ctrl+X": self.cut_selection,
            "Ctrl+V": self.paste_selection,
            "Delete": self.del_selection,
            "Ctrl+D": self.deselect_all,
            "S": self.toggle_selection_mode,
            "O": self.toggle_picker_mode,
            "P": self.toggle_brush_mode,
            "C": self.open_color_dialog,
            "D": self.reset_to_transparent,
            "L": self.apply_pen_collision,
        }
        for key, func in shortcuts.items():
            QShortcut(QKeySequence(key), self).activated.connect(func)

    def change_language(self, lang_code):
        self.current_lang = lang_code
        t = LANGUAGES[self.current_lang]
        self.title_label.setText(t["title"])
        self.btn_open.setText(t["open"])
        self.btn_save.setText(t["save"])
        self.pipette_header.setText(t["replacement_header"])
        self.pp_check.setText(t["pp_checkbox"])
        self.groups_label.setText(t["groups_header"])
        self.info_label.setText(t["info"])
        self.detect_label.setText(t["detect_title"])
        self.update_toggle_text()
        self.update_tooltips()
        if self.current_img:
            self.refresh_analysis()

    def update_tooltips(self):
        lang = LANGUAGES[self.current_lang]

        self.btn_open.setToolTip(lang["tooltip_open"])
        self.btn_save.setToolTip(lang["tooltip_save"])

        self.btn_brush.setToolTip(lang["tooltip_brush"])
        self.btn_select.setToolTip(lang["tooltip_select"])
        self.btn_eye_dropper.setToolTip(lang["tooltip_pipette"])
        self.btn_trans.setToolTip(lang["tooltip_nocolor"])

        if hasattr(self, "layer_buttons"):
            self.layer_buttons["add"].setToolTip(lang["tooltip_add"])
            self.layer_buttons["del"].setToolTip(lang["tooltip_del"])
            self.layer_buttons["merge"].setToolTip(lang["tooltip_merge"])
            self.layer_buttons["up"].setToolTip(lang["tooltip_up"])
            self.layer_buttons["down"].setToolTip(lang["tooltip_down"])

    def update_toggle_text(self):
        key = "toggle_outline_on" if self.show_only_outlines else "toggle_outline_off"
        self.btn_toggle_outline.setText(LANGUAGES[self.current_lang][key])

    def toggle_outline_view(self):
        self.show_only_outlines = not self.show_only_outlines
        self.update_toggle_text()
        self.apply_tree_filter()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            if not self.canvas_left.drag_mode:
                self.canvas_left.drag_mode = True
                self.canvas_left.setCursor(Qt.CursorShape.OpenHandCursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.canvas_left.drag_mode = False
            if not (QApplication.mouseButtons() & Qt.MouseButton.RightButton):
                self.canvas_left.setCursor(Qt.CursorShape.ArrowCursor)
        super().keyReleaseEvent(event)

    def update_layers_ui(self):
        self.layers_list.blockSignals(True)
        self.layers_list.clear()
        for i, layer_data in enumerate(self.pixel_layers):
            item = QTreeWidgetItem()
            item.setIcon(0, IconFactory.create_state_icon("eye", layer_data["visible"]))
            item.setToolTip(0, "Afficher/Masquer")
            item.setText(1, layer_data["name"])
            item.setIcon(1, IconFactory.create_thumbnail(layer_data["image"]))
            self.layers_list.addTopLevelItem(item)

        if (
            self.layers_list.topLevelItemCount() > 0
            and not self.layers_list.selectedItems()
        ):
            self.layers_list.setCurrentItem(self.layers_list.topLevelItem(0))
        self.layers_list.blockSignals(False)

    def add_layer(self, name=None, image=None):
        if not self.current_img and not image:
            return

        w, h = image.size if image else self.current_img.size
        new_img = image if image else Image.new("RGBA", (w, h), (0, 0, 0, 0))
        layer_name = name if name else f"Layer {len(self.pixel_layers) + 1}"

        layer_data = {
            "name": layer_name,
            "image": new_img,
            "visible": True,
            "locked": False,
        }
        self.pixel_layers.insert(0, layer_data)
        self.update_layers_ui()
        self.layers_list.setCurrentItem(self.layers_list.topLevelItem(0))
        self.compose_final_image()
        self.push_history()

    def delete_layer(self):
        item = self.layers_list.currentItem()
        if not item:
            return
        idx = self.layers_list.indexOfTopLevelItem(item)
        if idx != -1 and len(self.pixel_layers) > 1:
            self.pixel_layers.pop(idx)
            self.update_layers_ui()
            self.compose_final_image()
            self.push_history()

    def move_layer(self, delta):
        item = self.layers_list.currentItem()
        if not item:
            return
        current_index = self.layers_list.indexOfTopLevelItem(item)
        new_index = current_index + delta
        if 0 <= new_index < len(self.pixel_layers):
            self.pixel_layers[current_index], self.pixel_layers[new_index] = (
                self.pixel_layers[new_index],
                self.pixel_layers[current_index],
            )
            self.update_layers_ui()
            self.layers_list.setCurrentItem(self.layers_list.topLevelItem(new_index))
            self.compose_final_image()
            self.push_history()

    def merge_layers(self):
        selected = self.layers_list.selectedItems()
        if len(selected) < 2:
            return

        selected_indices = sorted(
            [self.layers_list.indexOfTopLevelItem(i) for i in selected], reverse=True
        )
        if not selected_indices:
            return

        base_index = selected_indices[0]
        base_layer = self.pixel_layers[base_index]
        merged_image = base_layer["image"].copy()
        for index_offset in range(1, len(selected_indices)):
            merged_image = Image.alpha_composite(
                merged_image, self.pixel_layers[selected_indices[index_offset]]["image"]
            )

        base_layer["image"] = merged_image
        base_layer["name"] = "Merged Layer"
        for layer_index in selected_indices[1:]:
            self.pixel_layers.pop(layer_index)

        self.update_layers_ui()
        self.compose_final_image()
        self.push_history()

    def handle_layer_click(self, item, column):
        idx = self.layers_list.indexOfTopLevelItem(item)
        if idx == -1:
            return
        if column == 0:
            self.pixel_layers[idx]["visible"] = not self.pixel_layers[idx]["visible"]
            item.setIcon(
                0,
                IconFactory.create_state_icon("eye", self.pixel_layers[idx]["visible"]),
            )
            self.compose_final_image()

    def compose_final_image(self):
        if not self.pixel_layers:
            return
        base = Image.new("RGBA", self.pixel_layers[0]["image"].size, (0, 0, 0, 0))
        for layer in reversed(self.pixel_layers):
            if layer["visible"]:
                base = Image.alpha_composite(base, layer["image"])
        self.current_img = base
        self.layer_tree.blockSignals(True)
        self.refresh_analysis()
        self.layer_tree.blockSignals(False)
        self.update_canvas_views()

    def refresh_analysis(self):
        if not self.current_img:
            return

        self.analysis_result = self.analyzer.analyze(self.current_img)
        self.rebuild_error_tree()

    def rebuild_error_tree(self):
        self.layer_tree.blockSignals(True)
        self.layer_tree.clear()

        category_names = {
            "OT": "Outlines Touching",
            "SC": "Staircase",
            "OSC": "Optional Staircase",
            "CR": "Corner",
            "CL": "Cluster",
        }

        for color_array in self.analysis_result.unique_colors:
            if color_array[3] < 10:
                continue
            color_tuple = tuple(color_array)
            layers_with_color = [
                layer
                for layer in self.analysis_result.layers
                if layer.color_key == color_tuple
            ]
            if not layers_with_color:
                continue

            color_hex = "#%02x%02x%02x" % (
                color_array[0],
                color_array[1],
                color_array[2],
            )
            color_parent_item = QTreeWidgetItem(self.layer_tree)
            color_parent_item.setText(0, f"{color_hex} ({len(layers_with_color)})")
            color_parent_item.setData(0, Qt.ItemDataRole.UserRole + 1, color_tuple)

            color_pixmap = QPixmap(16, 16)
            color_pixmap.fill(QColor(*color_array))
            color_parent_item.setIcon(0, QIcon(color_pixmap))

            for error_layer in layers_with_color:
                error_child_item = QTreeWidgetItem(color_parent_item)
                category_display_name = category_names.get(
                    error_layer.category, error_layer.category
                )
                error_child_item.setText(
                    0,
                    f"{category_display_name} {error_layer.id} ({error_layer.x}, {error_layer.y})",
                )
                error_child_item.setData(0, Qt.ItemDataRole.UserRole, error_layer.id)
                error_child_item.setFlags(
                    error_child_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
                )
                error_child_item.setCheckState(0, Qt.CheckState.Unchecked)

                category_pixmap = QPixmap(12, 12)
                category_pixmap.fill(error_layer.category_color)
                error_child_item.setIcon(0, QIcon(category_pixmap))

        self.apply_tree_filter()
        self.layer_tree.blockSignals(False)
        self.update_canvas_views()

    def apply_tree_filter(self):
        root = self.layer_tree.invisibleRootItem()
        for parent_index in range(root.childCount()):
            tree_item = root.child(parent_index)
            color_tuple = tree_item.data(0, Qt.ItemDataRole.UserRole + 1)
            if self.show_only_outlines:
                tree_item.setHidden(
                    color_tuple not in self.analysis_result.outline_colors
                )
            else:
                tree_item.setHidden(False)

    def on_item_visibility_changed(self, item, column):
        if item.parent() is not None:
            self.update_canvas_views()

    def on_selection_changed(self):
        root = self.layer_tree.invisibleRootItem()
        for parent_index in range(root.childCount()):
            parent_item = root.child(parent_index)
            has_child_selected = any(
                parent_item.child(child_index).isSelected()
                for child_index in range(parent_item.childCount())
            )
            if has_child_selected:
                parent_item.setSelected(True)
        self.update_canvas_views()

    def handle_selection_draw(self, x, y):
        if not self.current_img:
            return
        w, h = self.current_img.size
        if not hasattr(self, "selection_matrix") or self.selection_matrix.shape != (
            h,
            w,
        ):
            self.selection_matrix = np.zeros((h, w), dtype=np.uint8)

        if not (0 <= x < w and 0 <= y < h):
            return

        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.selection_matrix[y, x] = 0
        else:
            self.selection_matrix[y, x] = 1
        if self.pixel_perfect_mode and not (
            QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.selection_matrix = self.analyzer.analyze_matrix(self.selection_matrix)
        rows, cols = np.where(self.selection_matrix == 1)
        self.canvas_left.current_selection = set(zip(cols, rows))
        self.canvas_left.update()

    def _apply_selection_logic(self, x, y):
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            if (x, y) in self.canvas_left.current_selection:
                self.canvas_left.current_selection.remove((x, y))
        else:
            self.canvas_left.current_selection.add((x, y))

    def on_selection_finished(self):
        self.temp_sel_layer = None
        self.canvas_left.update()

    def update_canvas_views(self):
        if not self.current_img:
            return
        composed_image = self.pil_to_qimage(self.current_img)
        composed_pixmap = QPixmap.fromImage(composed_image)

        visible_layers, selected_layers = set(), set()
        root = self.layer_tree.invisibleRootItem()

        for parent_index in range(root.childCount()):
            parent_item = root.child(parent_index)
            is_parent_selected = parent_item.isSelected()

            for child_index in range(parent_item.childCount()):
                child_item = parent_item.child(child_index)
                layer_id = child_item.data(0, Qt.ItemDataRole.UserRole)
                if child_item.checkState(0) == Qt.CheckState.Checked:
                    visible_layers.add(layer_id)
                elif is_parent_selected:
                    visible_layers.add(layer_id)
                if child_item.isSelected():
                    selected_layers.add(layer_id)

        self.canvas_left.visible_layers = visible_layers
        self.canvas_left.selected_layers = selected_layers
        self.canvas_left.set_layers(self.analysis_result.layers)
        self.canvas_left.set_image(
            composed_pixmap, self.analysis_result.pixel_to_layers, reset_view=False
        )

    def update_picker_button_ui(self):
        button_size = 48
        button_pixmap = QPixmap(button_size, button_size)
        button_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(button_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect_size = 40
        rect_offset = (button_size - rect_size) // 2

        if self.replacement_color is None:
            painter.setBrush(QColor(240, 240, 240))
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.drawRoundedRect(
                rect_offset - 2, rect_offset, rect_size, rect_size, 8, 8
            )
            painter.setPen(QPen(Qt.GlobalColor.red, 3))
            painter.drawLine(
                rect_offset + 3,
                rect_offset + 5,
                rect_offset + rect_size - 7,
                rect_offset + rect_size - 5,
            )
        else:
            painter.setBrush(self.replacement_color)
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawRoundedRect(
                rect_offset - 2, rect_offset, rect_size, rect_size, 8, 8
            )
        painter.end()
        self.btn_color_preview.setIcon(QIcon(button_pixmap))
        self.btn_color_preview.setIconSize(QSize(button_size, button_size))

    def open_color_dialog(self):
        initial = (
            self.replacement_color if self.replacement_color else Qt.GlobalColor.white
        )
        color = QColorDialog.getColor(
            initial, self, LANGUAGES[self.current_lang]["choose_color"]
        )
        if color.isValid():
            self.set_active_color(color)

    def copy_selection(self):
        if not self.canvas_left.current_selection or not self.pixel_layers:
            return
        items = self.layers_list.selectedItems()
        idx = 0 if not items else self.layers_list.indexOfTopLevelItem(items[0])

        img = self.pixel_layers[idx]["image"]
        w, h = img.size
        self.clipboard_data = []

        for x, y in self.canvas_left.current_selection:
            if 0 <= x < w and 0 <= y < h:
                color = img.getpixel((x, y))
                self.clipboard_data.append(((x, y), color))

    def paste_selection(self):
        if not hasattr(self, "clipboard_data") or not self.clipboard_data:
            return

        selected_items = self.layers_list.selectedItems()
        if not selected_items:
            self.add_layer(name="Pasted Selection")
            target_layer_index = 0
        else:
            target_layer_index = self.layers_list.indexOfTopLevelItem(selected_items[0])

        target_layer = self.pixel_layers[target_layer_index]
        target_image = target_layer["image"]
        for (pixel_x, pixel_y), pixel_color in self.clipboard_data:
            if 0 <= pixel_x < target_image.width and 0 <= pixel_y < target_image.height:
                target_image.putpixel((pixel_x, pixel_y), pixel_color)
        self._update_thumbnail_for_index(target_layer_index)

        self.compose_final_image()
        self.push_history()
        self.refresh_analysis()
        self.canvas_left.update()

    def cut_selection(self):
        self.copy_selection()
        self.del_selection()

    def _apply_to_selected_layer(self, func):
        selected_items = self.layers_list.selectedItems()
        if not selected_items or not self.pixel_layers:
            return -1

        layer_index = self.layers_list.indexOfTopLevelItem(selected_items[0])
        layer_data = self.pixel_layers[layer_index]
        func(layer_data, layer_index)
        self._update_thumbnail_for_index(layer_index)
        return layer_index

    def _apply_to_selection_pixels(self, func):
        if not self.canvas_left.current_selection or not self.pixel_layers:
            return False

        items = self.layers_list.selectedItems()
        if not items:
            return False

        idx = self.layers_list.indexOfTopLevelItem(items[0])
        img = self.pixel_layers[idx]["image"]
        w, h = img.size
        modified = False

        for x, y in list(self.canvas_left.current_selection):
            if 0 <= x < w and 0 <= y < h:
                current_color = img.getpixel((x, y))
                new_color = func(x, y, current_color)
                if new_color is not None:
                    img.putpixel((x, y), new_color)
                    modified = True

        if modified:
            self._update_thumbnail_for_index(idx)
        return modified

    def _update_thumbnail_for_index(self, idx):
        if (
            0 <= idx < len(self.pixel_layers)
            and self.layers_list.topLevelItemCount() > idx
        ):
            item = self.layers_list.topLevelItem(idx)
            if item:
                item.setIcon(
                    1, IconFactory.create_thumbnail(self.pixel_layers[idx]["image"])
                )

    def del_selection(self):
        if not self._apply_to_selection_pixels(lambda x, y, c: (0, 0, 0, 0)):
            return
        self.compose_final_image()
        self.push_history()
        self.refresh_analysis()
        self.canvas_left.update()

    def set_active_color(self, qcolor):
        self.replacement_color = qcolor
        self._set_tool_mode(picker=False, brush=True)
        self.update_picker_button_ui()

    def reset_to_transparent(self):
        self.replacement_color = None
        self._set_tool_mode(picker=False, brush=True)
        self.update_picker_button_ui()

    def deselect_all(self):
        if hasattr(self, "selection_matrix"):
            self.selection_matrix.fill(0)
        self.canvas_left.current_selection.clear()
        self.canvas_left.update()

    def toggle_pixel_perfect(self, checked):
        self.pixel_perfect_mode = checked
        self.canvas_left.update()

    def toggle_picker_mode(self):
        self._set_tool_mode(picker=not self.canvas_left.picker_mode)

    def toggle_brush_mode(self):
        self._set_tool_mode(brush=not self.canvas_left.brush_mode)

    def toggle_selection_mode(self):
        new_state = not self.canvas_left.selection_mode
        self._set_tool_mode(selection=new_state)
        if new_state:
            modifiers = QApplication.keyboardModifiers()
            if not (
                modifiers & Qt.KeyboardModifier.ControlModifier
                or modifiers & Qt.KeyboardModifier.ShiftModifier
            ):
                self.canvas_left.current_selection.clear()
                self.canvas_left.update()

    def toggle_pen_mode(self):
        new_state = not self.canvas_left.pen_mode
        self._set_tool_mode(pen=new_state)
        if not new_state:
            self.canvas_left.pen_points = []
            self.canvas_left.update()

    def _apply_tool_button_style(self, button, is_active):
        if is_active:
            button.setStyleSheet("background-color: #444; border: 1px solid white;")
        else:
            button.setStyleSheet("")

    def _apply_tool_cursor(self, mode_name):
        if not self.canvas_left.drag_mode:
            cursor_map = {
                "picker": Qt.CursorShape.CrossCursor,
                "brush": Qt.CursorShape.PointingHandCursor,
                "selection": Qt.CursorShape.CrossCursor,
                "pen": Qt.CursorShape.CrossCursor,
            }
            cursor = cursor_map.get(mode_name, Qt.CursorShape.ArrowCursor)
            self.canvas_left.setCursor(cursor)
        self.update()

    def _set_tool_mode(self, picker=False, brush=False, selection=False, pen=False):
        self.canvas_left.picker_mode = picker
        self.canvas_left.brush_mode = brush
        self.canvas_left.selection_mode = selection
        self.canvas_left.pen_mode = pen

        self._apply_tool_button_style(self.btn_eye_dropper, picker)
        self._apply_tool_button_style(self.btn_brush, brush)
        self._apply_tool_button_style(self.btn_select, selection)
        self._apply_tool_button_style(self.btn_pen, pen)

        if picker:
            self._apply_tool_cursor("picker")
        elif brush:
            self._apply_tool_cursor("brush")
        elif selection:
            self._apply_tool_cursor("selection")
        elif pen:
            self._apply_tool_cursor("pen")
        else:
            if not self.canvas_left.drag_mode:
                self.canvas_left.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

    def _get_active_color_tuple(self):
        if not self.replacement_color:
            return (0, 0, 0, 0)
        return (
            self.replacement_color.red(),
            self.replacement_color.green(),
            self.replacement_color.blue(),
            self.replacement_color.alpha(),
        )

    def paint_pixel(self, x, y):
        items = self.layers_list.selectedItems()
        if not items or not self.pixel_layers:
            return

        idx = self.layers_list.indexOfTopLevelItem(items[0])
        target_img = self.pixel_layers[idx]["image"]
        w, h = target_img.size

        if not (0 <= x < w and 0 <= y < h):
            return

        color = self._get_active_color_tuple()

        if not self.pixel_perfect_mode:
            if target_img.getpixel((x, y)) == color:
                return
            target_img.putpixel((x, y), color)
            self.update_canvas_views_fast()
            items[0].setIcon(1, IconFactory.create_thumbnail(target_img))
        else:
            if not hasattr(self, "temp_stroke_layer") or self.temp_stroke_layer is None:
                self.temp_stroke_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))

            self.temp_stroke_layer.putpixel((x, y), color)
            analysis = self.analyzer.analyze(self.temp_stroke_layer)
            if analysis.layers:
                for layer_obj in analysis.layers:
                    self.temp_stroke_layer.putpixel(
                        (layer_obj.x, layer_obj.y), (0, 0, 0, 0)
                    )

            self.update_canvas_views_fast()
            preview_img = Image.alpha_composite(target_img, self.temp_stroke_layer)
            items[0].setIcon(1, IconFactory.create_thumbnail(preview_img))

    def on_brush_finished(self):
        if not self.pixel_layers:
            return
        if (
            self.pixel_perfect_mode
            and hasattr(self, "temp_stroke_layer")
            and self.temp_stroke_layer
        ):
            selected_items = self.layers_list.selectedItems()
            if selected_items:
                layer_index = self.layers_list.indexOfTopLevelItem(selected_items[0])
                target_image = self.pixel_layers[layer_index]["image"]
                self.pixel_layers[layer_index]["image"] = Image.alpha_composite(
                    target_image, self.temp_stroke_layer
                )
                self.temp_stroke_layer = None
                selected_items[0].setIcon(
                    1,
                    IconFactory.create_thumbnail(
                        self.pixel_layers[layer_index]["image"]
                    ),
                )

        self.compose_final_image()
        self.push_history(self.current_img)
        self.refresh_analysis()

    def update_canvas_views_fast(self):
        if not self.pixel_layers:
            return
        composed_image = Image.new(
            "RGBA", self.pixel_layers[0]["image"].size, (0, 0, 0, 0)
        )
        for layer in reversed(self.pixel_layers):
            if layer["visible"]:
                composed_image = Image.alpha_composite(composed_image, layer["image"])
        if (
            self.pixel_perfect_mode
            and hasattr(self, "temp_stroke_layer")
            and self.temp_stroke_layer
        ):
            composed_image = Image.alpha_composite(
                composed_image, self.temp_stroke_layer
            )

        self.current_img = composed_image
        qimage_data = self.pil_to_qimage(self.current_img)
        self.canvas_left.set_image(
            QPixmap.fromImage(qimage_data),
            self.analysis_result.pixel_to_layers,
            reset_view=False,
        )

    def select_layer_by_id(self, layer_id, add_to_selection=False):
        iterator = QTreeWidgetItemIterator(self.layer_tree)
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.ItemDataRole.UserRole) == layer_id:
                if not add_to_selection:
                    self.layer_tree.clearSelection()
                item.parent().setSelected(True)
                item.setSelected(True)
                self.layer_tree.scrollToItem(item)

                if self.canvas_left.brush_mode:
                    self.fix_selected_layers()
                return
            iterator += 1

    def fix_selected_layers(self):
        selected = self.layer_tree.selectedItems()
        ids = [
            i.data(0, Qt.ItemDataRole.UserRole)
            for i in selected
            if i.data(0, Qt.ItemDataRole.UserRole) is not None
        ]
        if not ids:
            return

        self._save_tree_state()
        fill_color = self._get_active_color_tuple()
        img_np = np.array(self.current_img)

        for lid in ids:
            layer = self.analysis_result.layers[lid]
            img_np[layer.y, layer.x] = fill_color

        self.push_history(Image.fromarray(img_np))
        self.refresh_analysis()
        self._restore_tree_state()

    def push_history(self, _unused_img=None):
        self.history = self.history[: self.history_index + 1]
        layers_snapshot = []
        for layer in self.pixel_layers:
            layers_snapshot.append(
                {
                    "name": layer["name"],
                    "image": layer["image"].copy(),
                    "visible": layer["visible"],
                    "locked": layer["locked"],
                }
            )

        self.history.append(layers_snapshot)
        if len(self.history) > 32:
            self.history.pop(0)
        else:
            self.history_index += 1

    def _history_move(self, direction):
        new_history_index = self.history_index + direction
        if 0 <= new_history_index < len(self.history):
            self.history_index = new_history_index
            history_snapshot = self.history[self.history_index]
            self.pixel_layers = []
            for layer_snapshot in history_snapshot:
                self.pixel_layers.append(
                    {
                        "name": layer_snapshot["name"],
                        "image": layer_snapshot["image"].copy(),
                        "visible": layer_snapshot["visible"],
                        "locked": layer_snapshot["locked"],
                    }
                )
            self.update_layers_ui()
            self.compose_final_image()

    def _save_tree_state(self):
        self._saved_tree_state = {}
        root = self.layer_tree.invisibleRootItem()
        for parent_index in range(root.childCount()):
            parent_item = root.child(parent_index)
            parent_text_key = parent_item.text(0)
            self._saved_tree_state[parent_text_key] = {
                "expanded": parent_item.isExpanded(),
                "checked": parent_item.checkState(0),
            }

    def _restore_tree_state(self):
        if not hasattr(self, "_saved_tree_state"):
            return
        self.layer_tree.blockSignals(True)
        root = self.layer_tree.invisibleRootItem()
        for parent_index in range(root.childCount()):
            parent_item = root.child(parent_index)
            parent_text_key = parent_item.text(0)
            if parent_text_key in self._saved_tree_state:
                saved_state = self._saved_tree_state[parent_text_key]
                parent_item.setExpanded(saved_state["expanded"])
                parent_item.setCheckState(0, saved_state["checked"])
        self.layer_tree.blockSignals(False)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.bmp)"
        )
        if path:
            img = Image.open(path).convert("RGBA")
            self.selection_matrix = np.zeros((img.height, img.width), dtype=np.uint8)
            self.pixel_layers = []
            self.layers_list.clear()
            self.history = []
            self.history_index = -1

            self.add_layer(name="Base Image", image=img)
            self.push_history(img)
            self.refresh_analysis()

    def save_image(self):
        if not self.current_img:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", "pixel_fix.png", "PNG (*.png)"
        )
        if path:
            self.current_img.save(path)

    def pil_to_qimage(self, pil_img):
        data = pil_img.tobytes("raw", "RGBA")
        return QImage(
            data, pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGBA8888
        )


from PyQt6.QtWidgets import QTreeWidgetItemIterator

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OutlineCheckApp()
    window.show()
    sys.exit(app.exec())
