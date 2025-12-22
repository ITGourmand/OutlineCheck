import sys
import numpy as np
from PIL import Image
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QLabel, QFileDialog,
    QFrame, QSplitter, QScrollArea, QAbstractItemView, QColorDialog,
    QComboBox
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QShortcut, QKeySequence, QWheelEvent, QMouseEvent, QKeyEvent, QIcon, QPen, QBrush
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QSize, QTimer
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
        "choose_color": "Choisir une couleur",
        "toggle_outline_on": "VOIR: COULEURS CONTOUR",
        "toggle_outline_off": "VOIR: TOUTES COULEURS"
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
        "choose_color": "Pick a color",
        "toggle_outline_on": "VIEW: OUTLINE COLORS",
        "toggle_outline_off": "VIEW: ALL COLORS"
    }
}
class PixelCanvas(QWidget):
    pixelSelected = pyqtSignal(int, bool)
    colorPicked = pyqtSignal(QColor)
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
        self.space_pressed = False
        self.last_mouse_pos = QPoint()
    def set_image(self, pixmap, error_map=None, reset_view=True):
        self.original_pixmap = pixmap
        self.error_map = error_map if error_map is not None else {}
        if reset_view:
            self.offset_x = 0.0
            self.offset_y = 0.0
        self.update()
    def set_layers(self, layers):
        self.layers = layers
    def get_layer_color(self, layer_id):
        if layer_id < len(self.layers):
            layer = self.layers[layer_id]
            if layer.category_color:
                color = layer.category_color
                return QColor(color.red(), color.green(), color.blue(), 150)
        return QColor(255, 60, 100, 150)
    def paintEvent(self, event):
        if not self.original_pixmap:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        temp_pixmap = self.original_pixmap.copy()
        if self.error_map:
            temp_painter = QPainter(temp_pixmap)
            for (x, y), layer_ids in self.error_map.items():
                for lid in layer_ids:
                    if lid in self.visible_layers:
                        color = self.get_layer_color(lid)
                        if lid in self.selected_layers:
                            color = QColor(0, 200, 255, 200)
                        temp_painter.fillRect(x, y, 1, 1, color)
            temp_painter.end()
        img_width = int(temp_pixmap.width() * self.zoom)
        img_height = int(temp_pixmap.height() * self.zoom)
        screen_x = int(-self.offset_x * self.zoom)
        screen_y = int(-self.offset_y * self.zoom)
        white_bg = QColor(225, 225, 225)
        painter.fillRect(screen_x, screen_y, img_width, img_height, white_bg)
        scaled_size = temp_pixmap.size() * self.zoom
        scaled_pixmap = temp_pixmap.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        painter.drawPixmap(screen_x, screen_y, scaled_pixmap)
        painter.end()
    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        prev_zoom = self.zoom
        if delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom /= 1.1
        self.zoom = max(0.5, min(self.zoom, 100.0))
        mouse_x = event.position().x()
        mouse_y = event.position().y()
        world_x = mouse_x / prev_zoom + self.offset_x
        world_y = mouse_y / prev_zoom + self.offset_y
        self.offset_x = world_x - mouse_x / self.zoom
        self.offset_y = world_y - mouse_y / self.zoom
        self.update()
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.is_dragging = True
            self.drag_start = event.globalPosition().toPoint()
            self.drag_offset_start = (self.offset_x, self.offset_y)
            return
        if self.space_pressed:
            self.last_mouse_pos = event.globalPosition().toPoint()
            return
        x = event.position().x() / self.zoom + self.offset_x
        y = event.position().y() / self.zoom + self.offset_y
        x = int(x)
        y = int(y)
        if self.picker_mode:
            if self.original_pixmap:
                img = self.original_pixmap.toImage()
                if 0 <= x < img.width() and 0 <= y < img.height():
                    self.colorPicked.emit(img.pixelColor(x, y))
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if (x, y) in self.error_map:
                add_to_selection = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
                self.pixelSelected.emit(self.error_map[(x, y)][0], add_to_selection)
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.drag_start
            self.offset_x = self.drag_offset_start[0] - delta.x() / self.zoom
            self.offset_y = self.drag_offset_start[1] - delta.y() / self.zoom
            self.update()
            return
        if self.space_pressed and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.last_mouse_pos
            self.last_mouse_pos = event.globalPosition().toPoint()
            self.offset_x -= delta.x() / self.zoom
            self.offset_y -= delta.y() / self.zoom
            self.update()
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.is_dragging = False
class ErrorLayer:
    def __init__(self, id, x, y, color_key, category="OT", category_color=None):
        self.id = id
        self.x = x
        self.y = y
        self.color_key = color_key
        self.category = category
        self.category_color = category_color
class OutlineCheckApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = "EN"
        self.setWindowTitle("OutlineCheck - OTC Software")
        self.setWindowIcon(QIcon("OutlineCheck.ico"))
        self.resize(1400, 950)
        self.history = []
        self.history_index = -1
        self.current_img = None
        self.layers = []
        self.pixel_to_layers = {}
        self.replacement_color = None
        self.outline_colors = set()
        self.show_only_outlines = True
        self.init_ui()
        self.setup_shortcuts()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("mainCanvas")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(10)
        header_row = QHBoxLayout()
        self.title_label = QLabel(LANGUAGES[self.current_lang]["title"])
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 900; color: #FC7D2B; letter-spacing: 2px;")
        header_row.addWidget(self.title_label)
        header_row.addStretch()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["EN","FR"])
        self.lang_combo.setFixedWidth(60)
        self.lang_combo.setObjectName("langCombo")
        self.lang_combo.currentTextChanged.connect(self.change_language)
        header_row.addWidget(self.lang_combo)
        sidebar_layout.addLayout(header_row)
        self.btn_open = QPushButton(LANGUAGES[self.current_lang]["open"])
        self.btn_open.clicked.connect(self.open_image)
        self.btn_save = QPushButton(LANGUAGES[self.current_lang]["save"])
        self.btn_save.clicked.connect(self.save_image)
        sidebar_layout.addWidget(self.btn_open)
        sidebar_layout.addWidget(self.btn_save)
        pipette_panel = QFrame()
        pipette_panel.setObjectName("toolPanel")
        pipette_layout = QVBoxLayout(pipette_panel)
        pipette_layout.setContentsMargins(12, 12, 12, 12)
        pipette_layout.setSpacing(10)
        self.pipette_header = QLabel(LANGUAGES[self.current_lang]["replacement_header"])
        self.pipette_header.setStyleSheet("color: #888; font-size: 10px; letter-spacing: 1px;")
        pipette_layout.addWidget(self.pipette_header)
        tool_row = QHBoxLayout()
        tool_row.setSpacing(10)
        self.btn_color_preview = QPushButton()
        self.btn_color_preview.setObjectName("colorPreviewBtn")
        self.btn_color_preview.setFixedSize(48, 48)
        self.btn_color_preview.clicked.connect(self.open_color_dialog)
        self.update_picker_button_ui()
        tool_row.addWidget(self.btn_color_preview)
        self.btn_eye_dropper = QPushButton()
        self.btn_eye_dropper.setFixedSize(48, 48)
        self.btn_eye_dropper.setObjectName("toolBtn")
        self.btn_eye_dropper.setIcon(self.create_icon_svg("eyedropper"))
        self.btn_eye_dropper.setIconSize(QSize(28, 28))
        self.btn_eye_dropper.clicked.connect(self.toggle_picker_mode)
        tool_row.addWidget(self.btn_eye_dropper)
        btn_transparent = QPushButton()
        btn_transparent.setFixedSize(48, 48)
        btn_transparent.setObjectName("toolBtn")
        btn_transparent.setIcon(self.create_icon_svg("cross"))
        btn_transparent.setIconSize(QSize(28, 28))
        btn_transparent.clicked.connect(self.reset_to_transparent)
        tool_row.addWidget(btn_transparent)
        tool_row.addStretch()
        pipette_layout.addLayout(tool_row)
        sidebar_layout.addWidget(pipette_panel)
        group_header_layout = QHBoxLayout()
        self.groups_label = QLabel(LANGUAGES[self.current_lang]["groups_header"])
        group_header_layout.addWidget(self.groups_label)
        group_header_layout.addStretch()
        sidebar_layout.addLayout(group_header_layout)
        self.btn_toggle_outline = QPushButton()
        self.btn_toggle_outline.clicked.connect(self.toggle_outline_view)
        self.btn_toggle_outline.setStyleSheet("background-color: #3A3B42; color: #FC7D2B; font-size: 10px;")
        self.update_toggle_text()
        sidebar_layout.addWidget(self.btn_toggle_outline)
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderHidden(True)
        self.layer_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.layer_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.layer_tree.itemChanged.connect(self.on_item_visibility_changed)
        sidebar_layout.addWidget(self.layer_tree)
        self.btn_fix = QPushButton(LANGUAGES[self.current_lang]["fix_btn"])
        self.btn_fix.setObjectName("fixButton")
        self.btn_fix.clicked.connect(self.fix_selected_layers)
        sidebar_layout.addWidget(self.btn_fix)
        self.info_label = QLabel(LANGUAGES[self.current_lang]["info"])
        self.info_label.setStyleSheet("color: #666; font-size: 11px;")
        sidebar_layout.addWidget(self.info_label)
        work_area = QFrame()
        work_area.setObjectName("workArea")
        work_layout = QVBoxLayout(work_area)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        container_left = QFrame()
        layout_left = QVBoxLayout(container_left)
        self.detect_label = QLabel(LANGUAGES[self.current_lang]["detect_title"])
        layout_left.addWidget(self.detect_label)
        self.canvas_left = PixelCanvas()
        self.canvas_left.pixelSelected.connect(self.select_layer_by_id)
        self.canvas_left.colorPicked.connect(self.set_active_color)
        layout_left.addWidget(self.canvas_left, 1)
        container_right = QFrame()
        layout_right = QVBoxLayout(container_right)
        self.preview_label = QLabel(LANGUAGES[self.current_lang]["preview_title"])
        layout_right.addWidget(self.preview_label)
        self.canvas_right = PixelCanvas()
        layout_right.addWidget(self.canvas_right, 1)
        self.splitter.addWidget(container_left)
        self.splitter.addWidget(container_right)
        work_layout.addWidget(self.splitter)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(work_area)
        self.setStyleSheet("""
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
            #miniBtn {
                padding: 0px; text-align: center; font-size: 10px;
                background-color: #21252b; border-color: #282c34; border-radius: 4px;
            }
            #miniBtn:hover { background-color: #2d2d33; color: #00c3ff; }
            #fixButton {
                background-color: #0062ff; color: white; border: none; text-align: center;
                margin-top: 10px; padding: 15px;
            }
            #fixButton:hover { background-color: #0052db; }
            QTreeWidget {
                background: #21252b; border: 1px solid #282c34; border-radius: 8px;
                outline: none; color: #d0d0d5;
            }
            QTreeWidget::item { padding: 6px; border-bottom: 1px solid #212126; }
            QTreeWidget::item:selected { background-color: #25252f; color: #00c3ff; }
            QScrollArea { border: 1px solid #282c34; border-radius: 12px; background: #404040; }
        """)
    def change_language(self, lang_code):
        self.current_lang = lang_code
        t = LANGUAGES[self.current_lang]
        self.title_label.setText(t["title"])
        self.btn_open.setText(t["open"])
        self.btn_save.setText(t["save"])
        self.pipette_header.setText(t["replacement_header"])
        self.groups_label.setText(t["groups_header"])
        self.btn_fix.setText(t["fix_btn"])
        self.info_label.setText(t["info"])
        self.detect_label.setText(t["detect_title"])
        self.preview_label.setText(t["preview_title"])
        self.update_toggle_text()
        if self.current_img:
            self.analyze_image()
    def create_icon_svg(self, name):
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if name == "eyedropper":
            painter.setPen(QPen(Qt.GlobalColor.white, 3))
            painter.drawLine(20, 44, 44, 20)
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.drawEllipse(40, 10, 14, 14)
            painter.setBrush(Qt.GlobalColor.white)
            path = [QPoint(14, 50), QPoint(22, 42), QPoint(14, 42)]
            painter.drawPolygon(path)
        elif name == "cross":
            painter.setPen(QPen(QColor(255, 60, 60), 5))
            margin = 16
            painter.drawLine(margin, margin, 64-margin, 64-margin)
            painter.drawLine(64-margin, margin, margin, 64-margin)
        painter.end()
        return QIcon(pix)
    def update_picker_button_ui(self):
        size = 48
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect_size = 40
        offset = (size - rect_size) // 2
        if self.replacement_color is None:
            painter.setBrush(QColor(240, 240, 240))
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.drawRoundedRect(offset, offset, rect_size, rect_size, 8, 8)
            painter.setPen(QPen(Qt.GlobalColor.red, 3))
            painter.drawLine(offset + 10, offset + 10, offset + rect_size - 10, offset + rect_size - 10)
        else:
            painter.setBrush(self.replacement_color)
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawRoundedRect(offset, offset, rect_size, rect_size, 8, 8)
        painter.end()
        self.btn_color_preview.setIcon(QIcon(pix))
        self.btn_color_preview.setIconSize(QSize(size, size))
    def batch_check(self, state):
        self.layer_tree.blockSignals(True)
        root = self.layer_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setCheckState(0, state)
            for j in range(item.childCount()):
                item.child(j).setCheckState(0, state)
        self.layer_tree.blockSignals(False)
        self.update_canvas_views()
    def open_color_dialog(self):
        initial = self.replacement_color if self.replacement_color else Qt.GlobalColor.white
        color = QColorDialog.getColor(initial, self, LANGUAGES[self.current_lang]["choose_color"])
        if color.isValid():
            self.set_active_color(color)
    def toggle_picker_mode(self):
        self.canvas_left.picker_mode = not self.canvas_left.picker_mode
        if self.canvas_left.picker_mode:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.btn_eye_dropper.setStyleSheet("background-color: #00c3ff; border: 1px solid white;")
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.btn_eye_dropper.setStyleSheet("")
    def set_active_color(self, qcolor):
        self.replacement_color = qcolor
        self.canvas_left.picker_mode = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.btn_eye_dropper.setStyleSheet("")
        self.update_picker_button_ui()
        self.update_canvas_views()
    def reset_to_transparent(self):
        self.replacement_color = None
        self.canvas_left.picker_mode = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.btn_eye_dropper.setStyleSheet("")
        self.update_picker_button_ui()
        self.update_canvas_views()
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            self.canvas_left.space_pressed = True
            self.canvas_right.space_pressed = True
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().keyPressEvent(event)
    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            self.canvas_left.space_pressed = False
            self.canvas_right.space_pressed = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().keyReleaseEvent(event)
    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(lambda: self._history_move(-1))
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self).activated.connect(lambda: self._history_move(1))
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(lambda: self._history_move(1))
    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.bmp)")
        if path:
            img = Image.open(path).convert("RGBA")
            self.history = []
            self.history_index = -1
            self.push_history(img)
            self.analyze_image()
    def save_image(self):
        if not self.current_img: return
        path, _ = QFileDialog.getSaveFileName(self, "Export", "pixel_fix.png", "PNG (*.png)")
        if path:
            self.current_img.save(path)
    def push_history(self, img):
        self.history = self.history[:self.history_index + 1]
        self.history.append(img.copy())
        self.history_index += 1
        self.current_img = img
    def _save_tree_state(self):
        color_states, expansion_states, parent_states = {}, {}, {}
        root = self.layer_tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            color_hex = parent.text(0)
            expansion_states[color_hex] = parent.isExpanded()
            parent_states[color_hex] = parent.checkState(0)
            color_states[color_hex] = {}
            for j in range(parent.childCount()):
                child = parent.child(j)
                lid = child.data(0, Qt.ItemDataRole.UserRole)
                color_states[color_hex][lid] = child.checkState(0)
        return color_states, expansion_states, parent_states
    def _restore_tree_state(self, color_states, expansion_states, parent_states):
        root = self.layer_tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            color_hex = parent.text(0)
            if color_hex in expansion_states:
                parent.setExpanded(expansion_states[color_hex])
            if color_hex in color_states:
                for j in range(parent.childCount()):
                    child = parent.child(j)
                    lid = child.data(0, Qt.ItemDataRole.UserRole)
                    if lid in color_states[color_hex]:
                        child.setCheckState(0, color_states[color_hex][lid])
            if color_hex in parent_states:
                parent.setCheckState(0, parent_states[color_hex])
            if color_hex in color_states:
                parent_state = parent_states.get(color_hex, Qt.CheckState.Checked)
                for j in range(parent.childCount()):
                    child = parent.child(j)
                    lid = child.data(0, Qt.ItemDataRole.UserRole)
                    if lid not in color_states[color_hex]:
                        child.setCheckState(0, parent_state)
    def _history_move(self, direction):
        new_index = self.history_index + direction
        if not (0 <= new_index < len(self.history)):
            return
        color_states, expansion_states, parent_states = self._save_tree_state()
        self.history_index = new_index
        self.current_img = self.history[self.history_index]
        self.layer_tree.blockSignals(True)
        self.analyze_image()
        self._restore_tree_state(color_states, expansion_states, parent_states)
        self.layer_tree.blockSignals(False)
        self.update_canvas_views()
    def check_pattern_match(self, pattern, color_mask, bad_pixel_mask):
        """0 = different color, 1 = same color, 2 = wildcard, 3 = center, 4 = same color + bad pixel"""
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
    def categorize_errors(self, img_np, bad_pixel_mask):
            h, w, _ = img_np.shape
            category_priority = {"CL": 4, "SC": 3, "OSC": 2, "CR": 1, "OT": 0}
            other_layers = [l for l in self.layers if l.category != "CL"]
            def apply_pattern(layer, pattern_type):
                if pattern_type == "SC":
                    layer.category = "SC"
                    layer.category_color = QColor(255, 10, 10)
                elif pattern_type == "OSC":
                    layer.category = "OSC"
                    layer.category_color = QColor(255, 155, 0)
                elif pattern_type == "OT":
                    layer.category = "OT"
                    layer.category_color = QColor(255, 0, 155)
                else:
                    layer.category = "CR"
                    layer.category_color = QColor(255, 255, 0)
            ot_pattern_1 = np.array([[2, 1, 0], [2, 3, 1], [0, 1, 2]])
            ot_pattern_2 = np.array([[2, 1, 0], [1, 3, 1], [0, 2, 2]])
            ot_patterns = [np.rot90(ot_pattern_1, k) for k in range(4)] + [np.rot90(ot_pattern_2, k) for k in range(4)]
            osc_pattern_1 = np.array([[2, 4, 0], [2, 3, 2], [0, 2, 2]])
            osc_pattern_2 = np.array([[2, 2, 0], [2, 3, 4], [0, 2, 2]])
            osc_rotations = [np.rot90(osc_pattern_1, k) for k in range(4)] + [np.rot90(osc_pattern_2, k) for k in range(4)]
            sc_pattern = np.array([[2, 4, 0], [2, 3, 4], [0, 2, 2]])
            sc_rotations = [np.rot90(sc_pattern, k) for k in range(4)]
            for layer in other_layers:
                x, y = layer.x, layer.y
                if y < 1 or y >= h - 1 or x < 1 or x >= w - 1:
                    apply_pattern(layer, "CR")
                    continue
                layer_color = layer.color_key
                color_mask = np.all(img_np[y-1:y+2, x-1:x+2] == layer_color, axis=-1)
                bad_mask = color_mask & bad_pixel_mask[y-1:y+2, x-1:x+2]
                if any(self.check_pattern_match(osc_rot, color_mask, bad_mask) for osc_rot in osc_rotations):
                    apply_pattern(layer, "OSC")
                    if any(self.check_pattern_match(sc_rot, color_mask, bad_mask) for sc_rot in sc_rotations):
                        apply_pattern(layer, "SC")
                elif any(self.check_pattern_match(ot_pat, color_mask, bad_mask) for ot_pat in ot_patterns):
                    apply_pattern(layer, "OT")
                else:
                    apply_pattern(layer, "CR")
            pos_to_layer = {(l.x, l.y): l for l in self.layers}
            staircase_layers = [l for l in self.layers if l.category == "SC"]
            queue = list(staircase_layers)
            while queue:
                current = queue.pop(0)
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0: continue
                        neighbor_pos = (current.x + dx, current.y + dy)
                        if neighbor_pos in pos_to_layer:
                            neighbor = pos_to_layer[neighbor_pos]
                            if neighbor.category in ["OSC", "OT", "CR"]:
                                neighbor.category = "SC"
                                neighbor.category_color = QColor(255, 10, 10)
                                queue.append(neighbor)
    def analyze_image(self):
            if not self.current_img: return
            img_np = np.array(self.current_img)
            h, w, _ = img_np.shape
            unique_colors = np.unique(img_np.reshape(-1, 4), axis=0)
            self.layers = []
            self.pixel_to_layers = {}
            self.outline_colors = set()
            self.layer_tree.blockSignals(True)
            self.layer_tree.clear()
            alpha = img_np[:, :, 3]
            is_opaque = alpha > 0
            is_trans = alpha == 0
            trans_padded = np.pad(is_trans, 1, constant_values=True)
            t_up    = trans_padded[:-2, 1:-1]
            t_down  = trans_padded[2:, 1:-1]
            t_left  = trans_padded[1:-1, :-2]
            t_right = trans_padded[1:-1, 2:]
            has_trans_neighbor = t_up | t_down | t_left | t_right
            is_outline = is_opaque & has_trans_neighbor
            outline_pixels = img_np[is_outline]
            if outline_pixels.size > 0:
                u_out_colors = np.unique(outline_pixels.reshape(-1, 4), axis=0)
                self.outline_colors = set(tuple(c) for c in u_out_colors)
            self.layer_tree.blockSignals(True)
            self.layer_tree.clear()
            cl_pat1 = np.array([[2, 1, 1], [2, 3, 1], [2, 2, 2]])
            cl_pat2 = np.array([[1, 1, 2], [1, 3, 2], [2, 2, 2]])
            cl_rotations = [np.rot90(cl_pat1, k) for k in range(4)] + [np.rot90(cl_pat2, k) for k in range(4)]
            base_pattern = np.array([[2, 1, 0], [2, 3, 1], [0, 2, 2]])
            rotations = [np.rot90(base_pattern, k) for k in range(4)]
            color_count = {}
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    color = tuple(img_np[y, x])
                    if color[3] < 10: continue
                    sub_mask = np.all(img_np[y-1:y+2, x-1:x+2] == color, axis=-1)
                    is_cl = any(self._check_pattern_match_optimized(rot, sub_mask) for rot in cl_rotations)
                    if is_cl:
                        if color not in color_count: color_count[color] = []
                        color_count[color].append((x, y, "CL"))
                    else:
                        is_pattern = any(self._check_pattern_match_optimized(rot, sub_mask) for rot in rotations)
                        if is_pattern:
                            if color not in color_count: color_count[color] = []
                            color_count[color].append((x, y, "BAD"))
            for color_tuple, pixels in color_count.items():
                color_hex = '#%02x%02x%02x' % (color_tuple[0], color_tuple[1], color_tuple[2])
                for x, y, p_type in pixels:
                    lid = len(self.layers)
                    new_layer = ErrorLayer(lid, x, y, color_tuple)
                    if p_type == "CL":
                        new_layer.category = "CL"
                        new_layer.category_color = QColor(128, 0, 128)
                    self.layers.append(new_layer)
                    if (x, y) not in self.pixel_to_layers:
                        self.pixel_to_layers[(x, y)] = []
                    self.pixel_to_layers[(x, y)].append(lid)
            bad_pixel_mask = np.zeros((h, w), dtype=bool)
            for layer in self.layers:
                bad_pixel_mask[layer.y, layer.x] = True
            self.categorize_errors(img_np, bad_pixel_mask)
            category_names = {"OT": "Outlines Touching", "SC": "Staircase", "OSC": "Optional Staircase", "CR": "Corner", "CL": "Cluster"}
            for color in unique_colors:
                if color[3] < 10: continue
                color_tuple = tuple(color)
                color_layers = [l for l in self.layers if l.color_key == color_tuple]
                if not color_layers: continue
                color_hex = '#%02x%02x%02x' % (color[0], color[1], color[2])
                parent_item = QTreeWidgetItem(self.layer_tree)
                parent_item.setText(0, f"{color_hex} ({len(color_layers)})")
                parent_item.setData(0, Qt.ItemDataRole.UserRole + 1, color_tuple)
                pix = QPixmap(16, 16)
                pix.fill(QColor(color[0], color[1], color[2], color[3]))
                parent_item.setIcon(0, QIcon(pix))
                for layer in color_layers:
                    child_item = QTreeWidgetItem(parent_item)
                    cat_name = category_names.get(layer.category, layer.category)
                    child_item.setText(0, f"{cat_name} {layer.id} ({layer.x}, {layer.y})")
                    child_item.setData(0, Qt.ItemDataRole.UserRole, layer.id)
                    child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    child_item.setCheckState(0, Qt.CheckState.Unchecked)
                    cat_pix = QPixmap(12, 12)
                    cat_pix.fill(layer.category_color)
                    child_item.setIcon(0, QIcon(cat_pix))
            self.apply_tree_filter()
            self.layer_tree.blockSignals(False)
            self.update_canvas_views()
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
    def on_item_visibility_changed(self, item, column):
        if item.parent() is not None:
            self.update_canvas_views()
    def on_selection_changed(self):
        root = self.layer_tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            has_selected_child = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.isSelected():
                    has_selected_child = True
                    break
            if has_selected_child:
                parent.setSelected(True)
        self.update_canvas_views()
    def update_toggle_text(self):
        key = "toggle_outline_on" if self.show_only_outlines else "toggle_outline_off"
        self.btn_toggle_outline.setText(LANGUAGES[self.current_lang][key])
    def toggle_outline_view(self):
        self.show_only_outlines = not self.show_only_outlines
        self.update_toggle_text()
        self.apply_tree_filter()
    def apply_tree_filter(self):
        root = self.layer_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            color_tuple = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if self.show_only_outlines:
                is_outline = color_tuple in self.outline_colors
                item.setHidden(not is_outline)
            else:
                item.setHidden(False)
    def update_canvas_views(self):
        if not self.current_img: return
        pix = QPixmap.fromImage(self.pil_to_qimage(self.current_img))
        visible, selected = set(), set()
        root = self.layer_tree.invisibleRootItem()
        selected_folders = set()
        forced_visible_layers = set()
        for i in range(root.childCount()):
            parent = root.child(i)
            is_parent_selected = parent.isSelected()
            if is_parent_selected:
                selected_folders.add(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                lid = child.data(0, Qt.ItemDataRole.UserRole)
                is_forced_visible = child.checkState(0) == Qt.CheckState.Checked
                is_parent_selected = parent.isSelected()
                if is_forced_visible:
                    visible.add(lid)
                    forced_visible_layers.add(lid)
                elif is_parent_selected:
                    visible.add(lid)
                if child.isSelected():
                    selected.add(lid)
        self.canvas_left.visible_layers = visible
        self.canvas_left.selected_layers = selected
        self.canvas_left.set_layers(self.layers)
        self.canvas_left.set_image(pix, self.pixel_to_layers, reset_view=False)
        img_preview_np = np.array(self.current_img)
        fill_color = [0, 0, 0, 0] if self.replacement_color is None else [
            self.replacement_color.red(), self.replacement_color.green(),
            self.replacement_color.blue(), self.replacement_color.alpha()
        ]
        for idx in selected:
            layer = self.layers[idx]
            img_preview_np[layer.y, layer.x] = fill_color
        self.canvas_right.set_image(QPixmap.fromImage(self.pil_to_qimage(Image.fromarray(img_preview_np))), None, reset_view=False)
    def select_layer_by_id(self, layer_id, add_to_selection=False):
        root = self.layer_tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.data(0, Qt.ItemDataRole.UserRole) == layer_id:
                    if not add_to_selection:
                        self.layer_tree.clearSelection()
                    parent.setSelected(True)
                    child.setSelected(True)
                    self.layer_tree.scrollToItem(child)
                    return
    def fix_selected_layers(self):
        selected_items = self.layer_tree.selectedItems()
        target_lids = [item.data(0, Qt.ItemDataRole.UserRole) for item in selected_items if item.data(0, Qt.ItemDataRole.UserRole) is not None]
        if not target_lids: return
        color_states, expansion_states, parent_states = self._save_tree_state()
        selection_state = set(target_lids)
        selected_parent_colors = set()
        root = self.layer_tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            if parent.isSelected():
                color_hex = parent.text(0).split(' ')[0]
                selected_parent_colors.add(color_hex)
        img_np = np.array(self.current_img)
        fill_color = [0, 0, 0, 0] if self.replacement_color is None else [
            self.replacement_color.red(), self.replacement_color.green(),
            self.replacement_color.blue(), self.replacement_color.alpha()
        ]
        for lid in target_lids:
            layer = self.layers[lid]
            img_np[layer.y, layer.x] = fill_color
        self.push_history(Image.fromarray(img_np))
        self.layer_tree.blockSignals(True)
        self.analyze_image()
        self._restore_tree_state(color_states, expansion_states, parent_states)
        root = self.layer_tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            color_hex = parent.text(0).split(' ')[0]
            if color_hex in selected_parent_colors:
                parent.setSelected(True)
            for j in range(parent.childCount()):
                child = parent.child(j)
                lid = child.data(0, Qt.ItemDataRole.UserRole)
                if lid in selection_state:
                    child.setSelected(True)
        self.layer_tree.blockSignals(False)
        self.update_canvas_views()
    def pil_to_qimage(self, pil_img):
        data = pil_img.tobytes("raw", "RGBA")
        return QImage(data, pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGBA8888)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OutlineCheckApp()
    window.show()
    sys.exit(app.exec())