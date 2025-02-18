import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem,
                             QPushButton, QVBoxLayout, QWidget, QToolTip)
from PyQt5.QtGui import QPen, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QRectF, QPointF

CELL_WIDTH = 100
CELL_HEIGHT = 50

class DraggableItem(QGraphicsRectItem):
    def __init__(self, element, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.element = element  # Dict mit "name", "x", "y", "line_index", "original_line"
        self.setRect(0, 0, CELL_WIDTH, CELL_HEIGHT)
        self.setBrush(QBrush(QColor("lightblue")))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsScenePositionChanges | QGraphicsItem.ItemIsSelectable)
        self.text_item = QGraphicsTextItem(self)
        self.updateText()
        self.setAcceptHoverEvents(True)

    def updateText(self):
        # Kürze den angezeigten Namen, falls er zu lang ist
        text = self.element["name"]
        display_text = text if len(text) <= 10 else text[:10] + "..."
        self.text_item.setPlainText(display_text)
        # Zentriere den Text im Rechteck
        bounding = self.text_item.boundingRect()
        rect = self.rect()
        self.text_item.setPos((rect.width() - bounding.width()) / 2, (rect.height() - bounding.height()) / 2)

    def hoverEnterEvent(self, event):
        # Bei Mouse-Hover wird der volle Name als Tooltip angezeigt
        QToolTip.showText(event.screenPos(), self.element["name"])
        super().hoverEnterEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Beim Verschieben: Position an Gridzellen (snappen) anpassen
            new_pos = value
            x = round(new_pos.x() / CELL_WIDTH) * CELL_WIDTH
            y = round(new_pos.y() / CELL_HEIGHT) * CELL_HEIGHT
            return QPointF(x, y)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Aktualisiere die Grid-Koordinaten in der Element-Datenstruktur
            new_pos = self.pos()
            grid_x = int(new_pos.x() / CELL_WIDTH)
            grid_y = int(new_pos.y() / CELL_HEIGHT)
            self.element["new_x"] = grid_x
            self.element["new_y"] = grid_y
        return super().itemChange(change, value)

# --- TreeEditor: Hauptfenster mit Grid, Save-Button etc. ---
class TreeEditor(QMainWindow):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.initUI()
        self.loadFile()

    def initUI(self):
        self.setWindowTitle("Research Tree Editor")
        self.resize(800, 600)
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)

        # QGraphicsView zur Darstellung des Grids
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

    def loadFile(self):
        with open(self.filename, "r", encoding="utf-8") as f:
            self.lines = f.readlines()
        self.elements = []  

        # Regex: Sucht nach dem ersten in Anführungszeichen stehenden String (Name)
        # und den Zahlen nach "position"
        pattern = re.compile(r'\{\s*(?:tech\s+)?\"([^\"]+)\".*?position\s+(\d+)\s+(\d+)', re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            match = pattern.search(line)
            if match:
                name, x, y = match.groups()
                element = {
                    "name": name,
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
        # Leere die Szene und zeichne das Grid neu
        self.scene.clear()
        self.drawGrid()
        # Erstelle für jedes Element ein verschiebbares Rechteck
        for element in self.elements:
            item = DraggableItem(element)
            item.setPos(element["x"] * CELL_WIDTH, element["y"] * CELL_HEIGHT)
            self.scene.addItem(item)

    def saveFile(self):
        # Aktualisiere in jeder betroffenen Zeile nur die Positionszahlen
        for element in self.elements:
            if "new_x" in element and "new_y" in element:
                line = element["original_line"]
                # Mit re.sub wird der Teil "position <x> <y>" ersetzt.
                def repl(match):
                    return f"{match.group(1)}{element['new_x']}{match.group(3)}{element['new_y']}"
                new_line = re.sub(r'(position\s+)(\d+)(\s+)(\d+)', repl, line)
                self.lines[element["line_index"]] = new_line
                element["original_line"] = new_line  # Update der Originalzeile
        with open(self.filename, "w", encoding="utf-8") as f:
            f.writelines(self.lines)
        print("Datei erfolgreich gespeichert!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TreeEditor("unit_research_ger.set")  # <--------- modify here
    editor.show()
    sys.exit(app.exec_())
