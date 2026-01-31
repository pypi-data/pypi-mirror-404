from PySide6.QtWidgets import QTextEdit, QStyle
from PySide6.QtGui import QAction, QIcon

class QTextEditWithClear(QTextEdit):
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()

        menu.addSeparator()

        clear_action = QAction("Clear", self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)
        clear_action.setIcon(icon)

        clear_action.triggered.connect(self.clear)

        menu.addAction(clear_action)
        menu.exec(event.globalPos())
