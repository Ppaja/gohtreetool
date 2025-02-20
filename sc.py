import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem,
                             QPushButton, QVBoxLayout, QWidget, QToolTip, QDialog,
                             QLineEdit, QLabel, QHBoxLayout)
from PyQt5.QtGui import QPen, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QRectF, QPointF

CELL_WIDTH = 100
CELL_HEIGHT = 50

class EditElementDialog(QWidget):
    def __init__(self, element, tree_editor):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.element = element
        self.tree_editor = tree_editor
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(f"Edit {self.element['name']}")
        layout = QVBoxLayout()

        # Requires section
        requires_layout = QHBoxLayout()
        requires_layout.addWidget(QLabel("Requires:"))
        self.requires_edit = QLineEdit(self.element.get("requires", ""))
        self.requires_edit.textChanged.connect(self.onRequiresChanged)  # Neue Zeile
        requires_layout.addWidget(self.requires_edit)
        self.add_requires_btn = QPushButton("+")
        self.add_requires_btn.clicked.connect(self.onAddRequires)
        requires_layout.addWidget(self.add_requires_btn)
        layout.addLayout(requires_layout)

        # Costs section with save button
        costs_layout = QHBoxLayout()
        costs_layout.addWidget(QLabel("Costs:"))
        self.costs_edit = QLineEdit(str(self.element.get("costs", "")))
        costs_layout.addWidget(self.costs_edit)
        self.save_costs_btn = QPushButton("Save")
        self.save_costs_btn.clicked.connect(self.onSaveCosts)
        costs_layout.addWidget(self.save_costs_btn)
        layout.addLayout(costs_layout)

        self.setLayout(layout)

    def onSaveCosts(self):
        self.element["costs"] = self.costs_edit.text()

    def onRequiresChanged(self, text):
        self.element["requires"] = text


        
    def onAddRequires(self):
        self.tree_editor.start_requires_selection(self)

class DraggableItem(QGraphicsRectItem):
    def __init__(self, element, tree_editor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.element = element
        self.tree_editor = tree_editor
        self.setRect(0, 0, CELL_WIDTH, CELL_HEIGHT)
        self.setBrush(QBrush(QColor("lightblue")))
        self.setFlags(QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemSendsScenePositionChanges | 
                      QGraphicsItem.ItemIsSelectable)
        self.text_item = QGraphicsTextItem(self)
        self.updateText()
        self.setAcceptHoverEvents(True)

    def updateText(self):
        text = self.element["name"]
        display_text = text if len(text) <= 10 else text[:10] + "..."
        self.text_item.setPlainText(display_text)
        bounding = self.text_item.boundingRect()
        rect = self.rect()
        self.text_item.setPos((rect.width() - bounding.width()) / 2, 
                             (rect.height() - bounding.height()) / 2)

    def hoverEnterEvent(self, event):
        tooltip = f'{self.element["name"]}\nrequires: {self.element.get("requires", "")}\ncosts: {self.element.get("costs", "")}'
        QToolTip.showText(event.screenPos(), tooltip)
        super().hoverEnterEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        if not self.tree_editor.selecting_requires:
            dialog = EditElementDialog(self.element, self.tree_editor)
            # Dialog als Attribut im TreeEditor speichern
            self.tree_editor.edit_dialogs.append(dialog)
            dialog.show()
        super().mouseDoubleClickEvent(event)



    def mousePressEvent(self, event):
        if self.tree_editor.selecting_requires:
            if event.button() == Qt.LeftButton:
                self.tree_editor.finish_requires_selection(self.element["name"])
                event.accept()
                return
        super().mousePressEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            new_pos = value
            x = round(new_pos.x() / CELL_WIDTH) * CELL_WIDTH
            y = round(new_pos.y() / CELL_HEIGHT) * CELL_HEIGHT
            return QPointF(x, y)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            new_pos = self.pos()
            grid_x = int(new_pos.x() / CELL_WIDTH)
            grid_y = int(new_pos.y() / CELL_HEIGHT)
            self.element["new_x"] = grid_x
            self.element["new_y"] = grid_y
        return super().itemChange(change, value)

class TreeEditor(QMainWindow):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.selecting_requires = False
        self.active_edit_dialog = None
        self.dependency_lines = []
        self.edit_dialogs = []
        self.initUI()
        self.loadFile()

    def initUI(self):
        self.setWindowTitle("Research Tree Editor")
        self.resize(800, 600)
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.saveFile)
        layout.addWidget(self.save_button)

        self.drawGrid()

    def drawGrid(self):
        pen = QPen(QColor("gray"))
        for i in range(0, 81):
            x = i * CELL_WIDTH
            self.scene.addLine(x, 0, x, 80 * CELL_HEIGHT, pen)
        for j in range(0, 81):
            y = j * CELL_HEIGHT
            self.scene.addLine(0, y, 80 * CELL_WIDTH, y, pen)

    def start_requires_selection(self, dialog):
        self.selecting_requires = True
        self.active_edit_dialog = dialog
        self.view.setCursor(Qt.CrossCursor)

    def finish_requires_selection(self, selected_name):
        if self.active_edit_dialog:
            current_requires = self.active_edit_dialog.requires_edit.text()
            if current_requires:
                new_requires = f"{current_requires} {selected_name}"
            else:
                new_requires = selected_name
            self.active_edit_dialog.requires_edit.setText(new_requires)
            self.active_edit_dialog.element["requires"] = new_requires
        self.selecting_requires = False
        self.view.setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_V:
            self.showDependencyLines()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_V:
            self.hideDependencyLines()
        super().keyReleaseEvent(event)

    def showDependencyLines(self):
        for element in self.elements:
            requires = element.get("requires", "").split()
            source_x = element["new_x"] * CELL_WIDTH + CELL_WIDTH/2
            source_y = element["new_y"] * CELL_HEIGHT + CELL_HEIGHT/2
            
            for req in requires:
                target = next((e for e in self.elements if e["name"] == req), None)
                if target:
                    target_x = target["new_x"] * CELL_WIDTH + CELL_WIDTH/2
                    target_y = target["new_y"] * CELL_HEIGHT + CELL_HEIGHT/2
                    line = self.scene.addLine(source_x, source_y, target_x, target_y,
                                            QPen(QColor("red"), 2))
                    self.dependency_lines.append(line)

    def hideDependencyLines(self):
        for line in self.dependency_lines:
            self.scene.removeItem(line)
        self.dependency_lines.clear()

    def loadFile(self):
        with open(self.filename, "r", encoding="utf-8") as f:
            self.lines = f.readlines()
        self.elements = []  

        pattern = re.compile(r'\{\s*(?:tech\s+)?\"([^\"]+)\".*?requires\s+\"([^\"]*)\".*?costs\s+(\d+).*?position\s+(\d+)\s+(\d+)', re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            match = pattern.search(line)
            if match:
                name, requires, costs, x, y = match.groups()
                element = {
                    "name": name,
                    "requires": requires,
                    "costs": costs,
                    "x": int(x),
                    "y": int(y),
                    "new_x": int(x),
                    "new_y": int(y),
                    "line_index": idx,
                    "original_line": line
                }
                self.elements.append(element)
        self.populateScene()

    def populateScene(self):
        self.scene.clear()
        self.drawGrid()
        for element in self.elements:
            item = DraggableItem(element, self)
            item.setPos(element["x"] * CELL_WIDTH, element["y"] * CELL_HEIGHT)
            self.scene.addItem(item)

    def saveFile(self):
        for element in self.elements:
            line = element["original_line"]
            new_line = line

            # Update position using format string instead of regex groups
            pos_pattern = r'position\s+\d+\s+\d+'
            new_pos = f'position {element["new_x"]} {element["new_y"]}'
            new_line = re.sub(pos_pattern, new_pos, new_line)

            # Update requires
            if "requires" in element:
                req_pattern = r'requires\s+"[^"]*"'
                new_req = f'requires "{element["requires"]}"'
                new_line = re.sub(req_pattern, new_req, new_line)

            # Update costs
            if "costs" in element:
                cost_pattern = r'costs\s+\d+'
                new_cost = f'costs {element["costs"]}'
                new_line = re.sub(cost_pattern, new_cost, new_line)

            self.lines[element["line_index"]] = new_line
            element["original_line"] = new_line

        with open(self.filename, "w", encoding="utf-8") as f:
            f.writelines(self.lines)
        print("File saved successfully!")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TreeEditor("unit_research_ger.set")
    editor.show()
    sys.exit(app.exec_())
