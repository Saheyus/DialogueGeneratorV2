from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                               QGroupBox, QSpacerItem, QSizePolicy, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class DialogueStructureWidget(QWidget):
    """Widget pour définir la structure du dialogue à générer."""
    
    structure_changed = Signal(list)  # Émis quand la structure change, avec la liste des éléments

    def __init__(self, parent=None):
        super().__init__(parent)
        self.combo_boxes = []
        self._init_ui()
        
    def _init_ui(self):
        """Initialise l'interface utilisateur."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Groupe pour la structure de dialogue
        structure_group = QGroupBox("Structure du Dialogue")
        structure_layout = QVBoxLayout(structure_group)
        
        # Layout horizontal pour les dropdowns
        dropdowns_layout = QHBoxLayout()
        dropdowns_layout.setSpacing(10)
        
        # Options disponibles pour les dropdowns (retiré "Commande")
        options = ["", "PNJ", "PJ", "Stop"]
        
        # Créer 6 dropdowns (augmenté de 5 à 6)
        for i in range(6):
            # Label pour chaque position
            position_label = QLabel(f"Position {i+1}:")
            position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # ComboBox
            combo = QComboBox()
            combo.addItems(options)
            combo.setMinimumWidth(80)
            combo.setMaximumWidth(100)
            
            # Valeurs par défaut : PNJ, PJ, Stop, vide, vide, vide
            if i == 0:
                combo.setCurrentText("PNJ")
            elif i == 1:
                combo.setCurrentText("PJ") 
            elif i == 2:
                combo.setCurrentText("Stop")
            else:
                combo.setCurrentText("")
                
            # Connecter le signal de changement
            combo.currentTextChanged.connect(self._on_structure_changed)
            
            # Layout vertical pour label + combo
            combo_layout = QVBoxLayout()
            combo_layout.addWidget(position_label)
            combo_layout.addWidget(combo)
            combo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Wrapper widget
            combo_widget = QWidget()
            combo_widget.setLayout(combo_layout)
            
            dropdowns_layout.addWidget(combo_widget)
            self.combo_boxes.append(combo)
        
        # Bouton d'aide à droite du dernier dropdown
        help_button = QPushButton("?")
        help_button.setMaximumSize(20, 20)
        help_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #f0f0f0;
                font-weight: bold;
                color: #666;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Infobulle détaillée (mise à jour sans "Commande")
        help_text = (
            "Définissez l'ordre et le type d'éléments pour le dialogue généré :\n\n"
            "• PNJ : Le personnage B parle (dialogue direct)\n"
            "• PJ : Le personnage A fait un choix (choix multiples)\n"
            "• Stop : Fin de la séquence\n"
            "• (Vide) : Emplacement non utilisé\n\n"
            "Exemple typique : PNJ → PJ → Stop\n"
            "Structure complexe : PNJ → PJ → PNJ → PJ → Stop"
        )
        help_button.setToolTip(help_text)
        
        # Ajouter le bouton d'aide avec un petit espace
        dropdowns_layout.addSpacing(10)
        dropdowns_layout.addWidget(help_button, 0, Qt.AlignmentFlag.AlignBottom)
        
        # Spacer pour pousser tout vers la gauche
        dropdowns_layout.addStretch()
        
        structure_layout.addLayout(dropdowns_layout)
        main_layout.addWidget(structure_group)
        
        # Spacer vertical
        main_layout.addStretch()
        
    def _on_structure_changed(self):
        """Appelé quand un dropdown change de valeur."""
        structure = self.get_structure()
        logger.debug(f"Structure de dialogue modifiée: {structure}")
        self.structure_changed.emit(structure)
        
    def get_structure(self) -> List[str]:
        """Retourne la structure actuelle sous forme de liste."""
        return [combo.currentText() for combo in self.combo_boxes]
        
    def set_structure(self, structure: List[str]):
        """Définit la structure des dropdowns.
        
        Args:
            structure: Liste de strings ("PNJ", "PJ", "Commande", "Stop", ou "")
        """
        for i, value in enumerate(structure):
            if i < len(self.combo_boxes):
                self.combo_boxes[i].setCurrentText(value)
                
    def get_structure_description(self) -> str:
        """Retourne une description textuelle de la structure pour inclusion dans le prompt."""
        structure = self.get_structure()
        
        # Filtrer les éléments vides et s'arrêter au premier "Stop"
        filtered_structure = []
        for element in structure:
            if element == "Stop":
                filtered_structure.append(element)
                break
            elif element != "":
                filtered_structure.append(element)
                
        if not filtered_structure:
            return "Structure libre (pas de contrainte spécifique)"
            
        descriptions = {
            "PNJ": "le personnage B parle directement",
            "PJ": "le personnage A (joueur) fait un choix parmi plusieurs options",
            "Stop": "fin de l'interaction"
        }
        
        parts = []
        for i, element in enumerate(filtered_structure):
            if element in descriptions:
                parts.append(f"{i+1}. {descriptions[element]}")
                
        return "Structure requise:\n" + "\n".join(parts)
        
    def reset_to_default(self):
        """Remet la structure par défaut : PNJ, PJ, Stop, vide, vide, vide."""
        default_structure = ["PNJ", "PJ", "Stop", "", "", ""]  # Ajouté un 6ème élément vide
        self.set_structure(default_structure) 