import logging
logger = logging.getLogger(__name__)

def handle_select_linked_elements(panel):
    """
    Slot pour le bouton "Lier Éléments Connexes".
    Récupère les personnages A/B et la scène, puis demande au LeftSelectionPanel
    de cocher tous les éléments du GDD qui leur sont liés.
    """
    scene_info = panel.scene_selection_widget.get_selected_scene_info()
    char_a_raw = scene_info.get("character_a")
    char_b_raw = scene_info.get("character_b")
    scene_region_raw = scene_info.get("scene_region")
    scene_sub_location_raw = scene_info.get("scene_sub_location")

    from constants import UIText  # Import local pour éviter les cycles
    placeholders = [UIText.NONE, UIText.NONE_FEM, UIText.ALL, UIText.NONE_SUBLOCATION, UIText.NO_SELECTION]

    char_a = None if char_a_raw in placeholders or not char_a_raw.strip() else char_a_raw
    char_b = None if char_b_raw in placeholders or not char_b_raw.strip() else char_b_raw
    scene_region = None if scene_region_raw in placeholders or not scene_region_raw.strip() else scene_region_raw
    scene_sub_location = None if scene_sub_location_raw in placeholders or not scene_sub_location_raw.strip() else scene_sub_location_raw

    # Utilise la méthode existante du LinkedSelectorService
    elements_to_select_set = panel.linked_selector.get_elements_to_select(
        char_a, char_b, scene_region, scene_sub_location
    )
    elements_to_select_list = list(elements_to_select_set)

    if hasattr(panel.main_window_ref, 'left_panel'):
        if elements_to_select_list:
            current_checked_items = panel.main_window_ref.left_panel.get_all_selected_item_names()
            combined_items_to_check = list(set(current_checked_items + elements_to_select_list))
            panel.main_window_ref.left_panel.set_checked_items_by_name(combined_items_to_check)
            logger.info(f"Éléments liés ({len(elements_to_select_list)}) ajoutés à la sélection existante. Total coché: {len(combined_items_to_check)}")
            panel.main_window_ref.statusBar().showMessage(f"{len(elements_to_select_list)} éléments liés ajoutés à la sélection.", 3000)
        else:
            logger.info("Aucun élément supplémentaire à lier trouvé pour le contexte principal.")
            panel.main_window_ref.statusBar().showMessage("Aucun nouvel élément lié trouvé.", 3000)
    else:
        logger.warning("Référence à left_panel non trouvée dans main_window_ref.")

def handle_unlink_unrelated(panel):
    """
    Slot pour le bouton "Décocher Non-Connexes".
    Récupère les personnages A/B et la scène, puis demande au LeftSelectionPanel
    de ne garder cochés QUE les éléments du GDD qui leur sont liés.
    """
    scene_info = panel.scene_selection_widget.get_selected_scene_info()
    char_a_raw = scene_info.get("character_a")
    char_b_raw = scene_info.get("character_b")
    scene_region_raw = scene_info.get("scene_region")
    scene_sub_location_raw = scene_info.get("scene_sub_location")

    from constants import UIText  # Import local pour éviter les cycles
    placeholders = [UIText.NONE, UIText.NONE_FEM, UIText.ALL, UIText.NONE_SUBLOCATION, UIText.NO_SELECTION]

    char_a = None if char_a_raw in placeholders or not char_a_raw.strip() else char_a_raw
    char_b = None if char_b_raw in placeholders or not char_b_raw.strip() else char_b_raw
    scene_region = None if scene_region_raw in placeholders or not scene_region_raw.strip() else scene_region_raw
    scene_sub_location = None if scene_sub_location_raw in placeholders or not scene_sub_location_raw.strip() else scene_sub_location_raw

    currently_checked_set = set()
    if hasattr(panel.main_window_ref, 'left_panel'):
        currently_checked_list = panel.main_window_ref.left_panel.get_all_selected_item_names()
        currently_checked_set = set(currently_checked_list)
    else:
        logger.warning("Référence à left_panel non trouvée lors de la récupération des items cochés.")

    items_to_keep_checked = panel.linked_selector.compute_items_to_keep_checked(
        currently_checked_set,
        char_a, 
        char_b, 
        scene_region, 
        scene_sub_location
    )

    if hasattr(panel.main_window_ref, 'left_panel'):
        panel.main_window_ref.left_panel.set_checked_items_by_name(items_to_keep_checked)
        logger.info(f"Conservation des éléments liés : {items_to_keep_checked}, autres décochés.")
        if items_to_keep_checked:
            panel.main_window_ref.statusBar().showMessage(f"Seuls les {len(items_to_keep_checked)} éléments liés sont conservés.", 3000)
        else:
            panel.main_window_ref.statusBar().showMessage("Aucun élément lié à conserver. Tous les éléments secondaires ont été décochés.", 3000)
    else:
        logger.warning("Référence à left_panel non trouvée pour mettre à jour les coches.") 