from PySide6.QtWidgets import QWidget, QGroupBox, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal
from ..utils import get_icon_path

class ContextActionsWidget(QWidget):
    select_linked_clicked = Signal()
    unlink_unrelated_clicked = Signal()
    uncheck_all_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.group_box = QGroupBox("Actions sur le Contexte Secondaire", self)
        self.layout = QHBoxLayout(self.group_box)

        self.select_linked_button = QPushButton("Lier Éléments Connexes")
        self.select_linked_button.setIcon(get_icon_path("link.png"))
        self.select_linked_button.setToolTip(
            "Coche automatiquement dans le panneau de gauche les éléments (personnages, lieux) liés aux personnages A/B et à la scène sélectionnés ici."
        )
        self.select_linked_button.clicked.connect(self.select_linked_clicked.emit)
        self.layout.addWidget(self.select_linked_button)

        self.unlink_unrelated_button = QPushButton("Décocher Non-Connexes")
        self.unlink_unrelated_button.setIcon(get_icon_path("link_off.png"))
        self.unlink_unrelated_button.setToolTip(
            "Décoche dans le panneau de gauche les éléments qui ne sont PAS liés aux personnages A/B et à la scène sélectionnés ici."
        )
        self.unlink_unrelated_button.clicked.connect(self.unlink_unrelated_clicked.emit)
        self.layout.addWidget(self.unlink_unrelated_button)

        self.uncheck_all_button = QPushButton("Tout Décocher")
        self.uncheck_all_button.setIcon(get_icon_path("clear_all.png"))
        self.uncheck_all_button.setToolTip(
            "Décoche tous les éléments dans toutes les listes du panneau de gauche."
        )
        self.uncheck_all_button.clicked.connect(self.uncheck_all_clicked.emit)
        self.layout.addWidget(self.uncheck_all_button)

        self.setLayout(self.layout) 