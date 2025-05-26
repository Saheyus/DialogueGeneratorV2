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

def handle_uncheck_all(panel):
    """
    Slot pour le bouton "Tout Décocher".
    Décocher tous les éléments dans le LeftSelectionPanel.
    """
    from constants import UIText
    if hasattr(panel.main_window_ref, 'left_panel') and hasattr(panel.main_window_ref.left_panel, 'uncheck_all_items'):
        panel.main_window_ref.left_panel.uncheck_all_items()
        logger.info("Tous les éléments ont été décochés dans LeftSelectionPanel.")
        panel.main_window_ref.statusBar().showMessage(UIText.ERROR_PREFIX + "Impossible de tout décocher.", 3000)
    else:
        logger.warning("Impossible de tout décocher: left_panel ou méthode uncheck_all_items non trouvée.")
        panel.main_window_ref.statusBar().showMessage(UIText.ERROR_PREFIX + "Impossible de tout décocher.", 3000)

def handle_system_prompt_changed(panel):
    """
    Slot pour la modification du prompt système (InstructionsWidget).
    Met à jour le prompt système dans le PromptEngine et déclenche la sauvegarde + estimation des tokens.
    """
    new_system_prompt = panel.instructions_widget.get_system_prompt_text()
    if panel.prompt_engine.system_prompt_template != new_system_prompt:
        panel.prompt_engine.system_prompt_template = new_system_prompt
        logger.info("PromptEngine system_prompt_template mis à jour.")
    panel._schedule_settings_save_and_token_update()

def handle_restore_default_system_prompt(panel):
    """
    Slot pour le bouton "Restaurer Défaut" du prompt système.
    Restaure le prompt système par défaut dans le PromptEngine, met à jour l'UI et relance l'estimation des tokens.
    """
    default_prompt = panel.prompt_engine._get_default_system_prompt()
    panel.instructions_widget.set_system_prompt_text(default_prompt)
    if panel.prompt_engine.system_prompt_template != default_prompt:
        panel.prompt_engine.system_prompt_template = default_prompt
        logger.info("PromptEngine system_prompt_template restauré par défaut.")
    panel.update_token_estimation_signal.emit()
    from PySide6.QtWidgets import QMessageBox
    QMessageBox.information(panel, "Prompt Restauré", "Le prompt système par défaut a été restauré.")

def handle_max_context_tokens_changed(panel, new_value):
    """
    Slot pour le changement de la valeur du spinbox max_context_tokens.
    Met à jour la limite de tokens pour le contexte et déclenche la sauvegarde + estimation des tokens.
    """
    tokens_value = int(new_value * 1000)
    logger.info(f"Limite de tokens pour le contexte mise à jour: {tokens_value}")
    panel._schedule_settings_save_and_token_update()

def handle_k_variants_changed(panel, value):
    """
    Slot pour le changement du nombre de variantes à générer (k_variants).
    Déclenche la sauvegarde des paramètres.
    """
    logger.info(f"Nombre de variantes à générer mis à jour: {value}")
    panel._schedule_settings_save()

def handle_structure_changed(panel):
    """
    Slot pour la modification de la structure de dialogue (DialogueStructureWidget).
    Déclenche la sauvegarde des paramètres et la mise à jour de l'estimation des tokens.
    """
    logger.info("Structure de dialogue modifiée.")
    panel._schedule_settings_save_and_token_update()

def handle_user_instructions_changed(panel):
    """
    Slot pour la modification des instructions utilisateur (InstructionsWidget).
    Déclenche la sauvegarde des paramètres et la mise à jour de l'estimation des tokens.
    """
    logger.info("Instructions utilisateur modifiées.")
    panel._schedule_settings_save_and_token_update()

def handle_refresh_token(panel):
    """
    Slot pour le bouton de rafraîchissement de l'estimation des tokens.
    Rafraîchit l'estimation du prompt et le nombre de tokens affichés.
    """
    logger.info("Rafraîchissement manuel de l'estimation des tokens demandé.")
    panel.update_token_estimation_ui()

def handle_generate_dialogue(panel):
    """
    Slot pour le bouton de génération de dialogue.
    Déclenche la génération de dialogue via le handler asynchrone.
    """
    logger.info("Lancement de la génération de dialogue (via handler extrait).")
    panel._launch_dialogue_generation()

def handle_validate_interaction_requested_from_tabs(panel, tab_name, interaction):
    """
    Slot pour la validation d'une interaction générée depuis les tabs.
    Sauvegarde l'interaction et met à jour l'UI.
    """
    logger.info(f"[VALIDATE] Demande de validation depuis l'onglet '{tab_name}' pour l'interaction ID={interaction.interaction_id}")
    try:
        panel.interaction_service.save(interaction)
        title_display = interaction.title if getattr(interaction, 'title', None) else str(interaction.interaction_id)[:8]
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(panel, "Interaction Validée", f"L'interaction '{title_display}' a été sauvegardée.")
        try:
            panel.interactions_tab_content_widget.interaction_selected_in_tab.disconnect(panel._on_interaction_selected)
        except Exception:
            pass
        panel.interactions_tab_content_widget.refresh_sequence_list(select_id=str(interaction.interaction_id))
        panel.interactions_tab_content_widget.display_interaction_in_editor(interaction)
        try:
            panel.interactions_tab_content_widget.interaction_selected_in_tab.connect(panel._on_interaction_selected)
        except Exception:
            pass
        if hasattr(panel.main_window_ref, 'statusBar'):
            panel.main_window_ref.statusBar().showMessage(f"Interaction '{title_display}' sauvegardée.", 3000)
    except Exception as e:
        logger.exception("Erreur lors de la validation/sauvegarde de l'interaction.")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(panel, "Erreur", f"Impossible de sauvegarder l'interaction : {e}")

def handle_interaction_selected(panel, interaction_id):
    """
    Slot pour la sélection d'une interaction dans la liste.
    Met à jour l'éditeur et la barre de statut.
    """
    if interaction_id:
        logger.info(f"Interaction sélectionnée : {interaction_id}")
        interaction = panel.interaction_service.get_by_id(str(interaction_id))
        if interaction:
            title_display = getattr(interaction, 'title', str(interaction_id)[:8])
            panel.main_window_ref.statusBar().showMessage(f"Interaction '{title_display}' sélectionnée.", 3000)
        else:
            logger.warning(f"Interaction {interaction_id} non trouvée par le service.")
            from constants import UIText
            panel.main_window_ref.statusBar().showMessage(UIText.ERROR_PREFIX + f"Interaction {interaction_id} non trouvée.", 3000)
            panel.interactions_tab_content_widget.display_interaction_in_editor(interaction)
        title_display = getattr(interaction, 'title', str(interaction_id)[:8])
        panel.main_window_ref.statusBar().showMessage(f"Édition de l'interaction '{title_display}'", 3000)
    else:
        logger.info("Aucune interaction sélectionnée.")
        from constants import UIText
        panel.main_window_ref.statusBar().showMessage(UIText.NO_INTERACTION_FOUND, 3000)
        panel.interactions_tab_content_widget.display_interaction_in_editor(None)

def handle_sequence_changed(panel):
    """
    Slot pour le changement dans la séquence d'interactions (ajout, suppression, réorganisation).
    Met à jour la barre de statut.
    """
    logger.info("La séquence d'interactions a changé (ajout, suppression, réorganisation).")
    panel.main_window_ref.statusBar().showMessage("Séquence d'interactions modifiée.", 3000)

def handle_edit_interaction_requested(panel, interaction_id):
    """
    Slot pour la demande d'édition d'une interaction.
    Affiche l'interaction dans l'éditeur et sélectionne l'onglet si besoin.
    """
    logger.info(f"Demande d'édition pour l'interaction : {interaction_id}")
    interaction = panel.interaction_service.get_by_id(str(interaction_id))
    from PySide6.QtWidgets import QTabWidget, QMessageBox
    if interaction:
        tabs = panel.findChild(QTabWidget)
        if tabs:
            interactions_tab_index = tabs.indexOf(panel.interactions_tab_content_widget.parent())
            if interactions_tab_index >= 0 and tabs.currentIndex() != interactions_tab_index:
                tabs.setCurrentIndex(interactions_tab_index)
        panel.interactions_tab_content_widget.display_interaction_in_editor(interaction)
        title_display = getattr(interaction, 'title', str(interaction_id)[:8])
        panel.main_window_ref.statusBar().showMessage(f"Édition de l'interaction '{title_display}'", 3000)
    else:
        QMessageBox.warning(panel, "Erreur", f"Impossible de trouver l'interaction {str(interaction_id)} pour l'édition.") 

def handle_interaction_changed(panel, interaction):
    """
    Slot pour le changement d'une interaction après édition.
    Met à jour la barre de statut.
    """
    logger.info(f"Interaction modifiée : {interaction.interaction_id}")
    title_display = getattr(interaction, 'title', str(interaction.interaction_id)[:8])
    panel.main_window_ref.statusBar().showMessage(f"Interaction '{title_display}' mise à jour.", 3000) 

def get_generation_panel_settings(panel):
    """
    Récupère les paramètres actuels du GenerationPanel pour la sauvegarde.
    """
    scene_settings = panel.scene_selection_widget.get_selected_scene_info()
    settings = {
        "character_a": scene_settings.get("character_a"),
        "character_b": scene_settings.get("character_b"),
        "scene_region": scene_settings.get("scene_region"),
        "scene_sub_location": scene_settings.get("scene_sub_location"),
        "k_variants": panel.k_variants_combo.currentText(),
        "user_instructions": panel.instructions_widget.get_user_instructions_text(),
        "llm_model": panel.llm_model_combo.currentData(),
        "system_prompt": panel.instructions_widget.get_system_prompt_text(),
        "max_context_tokens": panel.max_context_tokens_spinbox.value(),
        "dialogue_structure": panel.dialogue_structure_widget.get_structure()
    }
    logger.debug(f"Récupération des paramètres du GenerationPanel: {settings}")
    return settings 

def load_generation_panel_settings(panel, settings):
    """
    Charge les paramètres dans le GenerationPanel à partir d'un dictionnaire.
    """
    logger.debug(f"Chargement des paramètres dans GenerationPanel: {settings}")
    panel._is_loading_settings = True
    scene_info_to_load = {
        "character_a": settings.get("character_a"),
        "character_b": settings.get("character_b"),
        "scene_region": settings.get("scene_region"),
        "scene_sub_location": settings.get("scene_sub_location")
    }
    panel.scene_selection_widget.load_selection(scene_info_to_load)
    panel.k_variants_combo.setCurrentText(settings.get("k_variants", "3"))
    instruction_settings_to_load = {
        "user_instructions": settings.get("user_instructions", ""),
        "system_prompt": settings.get("system_prompt")
    }
    default_system_prompt_for_iw = panel.prompt_engine._get_default_system_prompt() if panel.prompt_engine else ""
    panel.instructions_widget.load_settings(
        instruction_settings_to_load,
        default_user_instructions="",
        default_system_prompt=default_system_prompt_for_iw
    )
    model_identifier = settings.get("llm_model")
    if model_identifier:
        if hasattr(panel, 'generation_params_widget') and panel.generation_params_widget:
            panel.generation_params_widget.select_model_in_combo(model_identifier)
    else:
        if hasattr(panel, 'generation_params_widget') and panel.generation_params_widget and panel.generation_params_widget.llm_model_combo.count() > 0:
            panel.generation_params_widget.llm_model_combo.setCurrentIndex(0)
    if "dialogue_structure" in settings:
        panel.dialogue_structure_widget.set_structure(settings["dialogue_structure"])
    if "max_context_tokens" in settings:
        panel.max_context_tokens_spinbox.setValue(settings["max_context_tokens"])
    panel._is_loading_settings = False
    panel.update_token_estimation_signal.emit()
    logger.info("Paramètres du GenerationPanel chargés.") 

def handle_update_structured_output_checkbox_state(panel):
    """
    Slot pour la mise à jour de l'état de la checkbox structured_output (même si la logique est vide).
    """
    pass 

def handle_generation_task_started(panel):
    """
    Slot appelé quand la tâche de génération démarre (signal du handler).
    Met à jour l'UI pour indiquer que la génération est en cours.
    """
    import PySide6.QtWidgets as QtWidgets
    panel.generation_progress_bar.setRange(0, 0) # Indeterminate
    panel.generation_progress_bar.setVisible(True)
    panel.generate_dialogue_button.setEnabled(False)
    QtWidgets.QApplication.processEvents() 

def handle_generation_task_succeeded(panel, processed_variants, full_prompt, estimated_tokens):
    """
    Slot appelé quand la génération de dialogue réussit.
    Met à jour l'UI avec les variantes générées et le prompt.
    """
    import PySide6.QtWidgets as QtWidgets
    from constants import UIText
    logger.info(f"GenerationPanel: Tâche de génération réussie. {len(processed_variants)} variantes traitées reçues.")
    if full_prompt:
        estimated_tokens_k = estimated_tokens / 1000 if estimated_tokens else 0
        panel.token_estimation_label.setText(f"Tokens prompt final: {estimated_tokens_k:.1f}k")
        panel._display_prompt_in_tab(full_prompt)
    else:
        panel.token_estimation_label.setText("Tokens prompt final: Erreur")
        panel._display_prompt_in_tab("Erreur: Le prompt n'a pas pu être construit par le service/handler.")
    panel.variants_display_widget.blockSignals(True)
    num_tabs_to_keep = 0
    if panel.variants_display_widget.count() > 0 and panel.variants_display_widget.tabText(0) == "Prompt Estimé":
        num_tabs_to_keep = 1
    while panel.variants_display_widget.count() > num_tabs_to_keep:
        panel.variants_display_widget.removeTab(num_tabs_to_keep)
    if processed_variants:
        for i, interaction_obj in enumerate(processed_variants):
            if interaction_obj.interaction_id.startswith("error_"):
                error_text = interaction_obj.elements[0].get('text', 'Erreur inconnue dans la variante') if interaction_obj.elements else 'Erreur inconnue'
                text_edit = QtWidgets.QTextEdit(f"// {interaction_obj.title}\n{error_text}")
                text_edit.setReadOnly(True)
                panel.variants_display_widget.addTab(text_edit, f"Variante {i+1} (Erreur)")
            else:
                panel.variants_display_widget.add_interaction_tab(f"Variante {i+1}", interaction_obj)
                logger.info(f"[GP] Variante {i+1} (Interaction) ajoutée via add_interaction_tab. ID: {interaction_obj.interaction_id}")
        logger.info(f"{len(processed_variants)} variantes affichées depuis le handler.")
    else:
        logger.warning("Aucune variante valide reçue du handler (liste vide).")
        error_tab = QtWidgets.QTextEdit(UIText.NO_VARIANT + " (via Handler)")
        panel.variants_display_widget.addTab(error_tab, "Aucune Variante (Handler)")
    panel.variants_display_widget.blockSignals(False)
    panel.generation_finished.emit(True if processed_variants else False)
    panel._finalize_generation_ui_state()

def handle_generation_task_failed(panel, error_message, full_prompt):
    """
    Slot appelé quand la génération de dialogue échoue.
    Met à jour l'UI avec le message d'erreur et le prompt si disponible.
    """
    import PySide6.QtWidgets as QtWidgets
    from constants import UIText
    logger.error(f"GenerationPanel: Tâche de génération échouée: {error_message}")
    if full_prompt and full_prompt != "Erreur: Le prompt n'a pas pu être construit.":
        panel._display_prompt_in_tab(full_prompt)
    else:
        panel._display_prompt_in_tab(f"Erreur critique avant ou pendant la construction du prompt: {error_message}")
    panel.variants_display_widget.blockSignals(True)
    num_tabs_to_keep_err = 0
    if panel.variants_display_widget.count() > 0 and panel.variants_display_widget.tabText(0) == "Prompt Estimé":
        num_tabs_to_keep_err = 1
    while panel.variants_display_widget.count() > num_tabs_to_keep_err:
        panel.variants_display_widget.removeTab(num_tabs_to_keep_err)
    error_tab_content = QtWidgets.QTextEdit()
    error_tab_content.setPlainText(f"Une erreur majeure est survenue lors de la génération (via Handler):\n\n{error_message}")
    error_tab_content.setReadOnly(True)
    panel.variants_display_widget.addTab(error_tab_content, "Erreur Critique (Handler)")
    panel.variants_display_widget.blockSignals(False)
    panel.generation_finished.emit(False)
    panel._finalize_generation_ui_state() 

def handle_prompt_preview_ready_for_display(panel, prompt_text, estimated_tokens):
    """
    Slot appelé quand la prévisualisation du prompt est prête.
    Met à jour l'UI avec le prompt et l'estimation des tokens.
    """
    logger.debug(f"GenerationPanel: Prévisualisation du prompt prête (via Handler). Tokens: {estimated_tokens}")
    if prompt_text:
        estimated_tokens_k = estimated_tokens / 1000 if estimated_tokens else 0
        panel.token_estimation_label.setText(f"Tokens prompt (en cours): {estimated_tokens_k:.1f}k")
        panel._display_prompt_in_tab(prompt_text)
    else:
        panel.token_estimation_label.setText("Tokens prompt (en cours): Erreur")
        panel._display_prompt_in_tab("Erreur: Le prompt n'a pas pu être construit par le service/handler pour la prévisualisation.") 