import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from DialogueGenerator.ui.generation_panel.interaction_sequence_widget import InteractionSequenceWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - Gestionnaire de séquence d'interactions")
        self.resize(400, 300)
        self.widget = InteractionSequenceWidget(self)
        self.setCentralWidget(self.widget)
        self.widget.interaction_selected.connect(self.on_interaction_selected)
        self.widget.sequence_changed.connect(self.on_sequence_changed)

    def on_interaction_selected(self, interaction_id):
        self.setWindowTitle(f"Sélection : {interaction_id}")

    def on_sequence_changed(self):
        print("Séquence modifiée !")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec()) 