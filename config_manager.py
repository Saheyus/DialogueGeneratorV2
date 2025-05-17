import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

UI_SETTINGS_FILE = Path(__file__).parent / "ui_settings.json"

def load_ui_settings() -> Dict[str, Any]:
    """
    Loads UI settings from the ui_settings.json file.

    Returns:
        Dict[str, Any]: The loaded settings, or default settings if the file doesn't exist or is invalid.
    """
    if UI_SETTINGS_FILE.exists():
        try:
            with open(UI_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Error decoding {UI_SETTINGS_FILE}. Returning default settings.")
            return {} 
    return {}

def save_ui_settings(settings: Dict[str, Any]) -> None:
    """
    Saves UI settings to the ui_settings.json file.

    Args:
        settings (Dict[str, Any]): The settings to save.
    """
    try:
        with open(UI_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except IOError:
        print(f"Error: Could not write to {UI_SETTINGS_FILE}.")

def get_unity_dialogues_path() -> Optional[Path]:
    """
    Retrieves the Unity dialogues path from UI settings.

    Validates if the path exists and is a directory and is writable.

    Returns:
        Optional[Path]: The path to Unity dialogues, or None if not configured or invalid.
    """
    settings = load_ui_settings()
    path_str = settings.get("unity_dialogues_path")

    if not path_str:
        print("Error: 'unity_dialogues_path' not found in UI settings. Please configure it.")
        return None

    dialogues_path = Path(path_str)

    if not dialogues_path.exists():
        print(f"Error: The configured Unity dialogues path does not exist: {dialogues_path}. Please check the path in {UI_SETTINGS_FILE.name} or use set_unity_dialogues_path.")
        return None
    
    if not dialogues_path.is_dir():
        print(f"Error: The configured Unity dialogues path is not a directory: {dialogues_path}.")
        return None
    
    if not os.access(dialogues_path, os.W_OK):
        print(f"Error: The configured Unity dialogues path is not writable: {dialogues_path}.")
        return None
    
    if not os.access(dialogues_path, os.R_OK):
        print(f"Error: The configured Unity dialogues path is not readable: {dialogues_path}.")
        return None

    return dialogues_path

def set_unity_dialogues_path(new_path_str: str) -> bool:
    """
    Sets and saves the new Unity dialogues path in UI settings.

    Args:
        new_path_str (str): The new path string.

    Returns:
        bool: True if the path was updated and saved successfully, False otherwise.
    """
    settings = load_ui_settings()
    
    test_path = Path(new_path_str)
    if not test_path.is_dir():
        print(f"Warning: The provided path '{new_path_str}' is not currently a valid directory. ")
        print(f"Please ensure it exists and is a directory before the application attempts to use it.")

    settings["unity_dialogues_path"] = new_path_str
    save_ui_settings(settings)
    print(f"Info: Unity dialogues path configuration updated to: {new_path_str}")
    return True

def list_yarn_files(dialogues_base_path: Path, recursive: bool = False) -> List[Path]:
    """
    Lists .yarn files in the specified Unity dialogues path.

    Args:
        dialogues_base_path (Path): The base path to search for .yarn files.
        recursive (bool): If True, searches recursively in subdirectories.
                          Defaults to False (searches only in the root of dialogues_base_path).

    Returns:
        List[Path]: A list of Path objects for each .yarn file found.
    """
    if not dialogues_base_path or not dialogues_base_path.is_dir():
        print(f"Error: Cannot list .yarn files, path is invalid or not a directory: {dialogues_base_path}")
        return []

    pattern = "*.yarn"
    if recursive:
        pattern = "**/*.yarn" # Search in all subdirectories
    
    try:
        yarn_files = list(dialogues_base_path.glob(pattern))
        # Filter out files that might be in '.git' or other hidden/system directories if necessary,
        # though glob usually handles this well by default depending on OS and settings.
        # Example filter: yarn_files = [f for f in yarn_files if not any(part.startswith('.') for part in f.parts)]
        return yarn_files
    except Exception as e:
        print(f"Error listing .yarn files in {dialogues_base_path}: {e}")
        return []

def read_yarn_file_content(file_path: Path) -> Optional[str]:
    """
    Reads the content of a specified .yarn file.

    Args:
        file_path (Path): The Path object pointing to the .yarn file.

    Returns:
        Optional[str]: The content of the file as a string, or None if an error occurs.
    """
    if not file_path or not file_path.is_file():
        print(f"Error: Cannot read file, path is invalid or not a file: {file_path}")
        return None
    
    try:
        content = file_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

if __name__ == "__main__":
    print(f"Config manager for {UI_SETTINGS_FILE.resolve()}")

    settings = load_ui_settings()
    base_path_str = settings.get("unity_dialogues_path")

    if not base_path_str:
        print(f"Error: 'unity_dialogues_path' not found in {UI_SETTINGS_FILE.name}.")
    else:
        base_dialogues_path_obj = Path(base_path_str)
        try:
            base_dialogues_path_obj.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error creating base directory {base_dialogues_path_obj}: {e}")
            # Exit or handle more gracefully if base dir creation is critical before proceeding
        
        current_validated_path = get_unity_dialogues_path() # This also ensures writability/readability
        
        if current_validated_path:
            print(f"Current valid Unity Dialogues Path: {current_validated_path}")
            
            generated_dir = current_validated_path / "generated"
            try:
                generated_dir.mkdir(parents=True, exist_ok=True)
                print(f"Ensured 'generated' subdirectory exists at: {generated_dir}")
            except OSError as e:
                print(f"Error creating or accessing 'generated' subdirectory: {e}")

            print("\n--- Testing list_yarn_files (non-recursive) ---")
            yarn_files_in_root = list_yarn_files(current_validated_path, recursive=False)
            if yarn_files_in_root:
                print(f"Found {len(yarn_files_in_root)} .yarn file(s) in {current_validated_path}:")
                for yarn_file in yarn_files_in_root:
                    print(f"  - {yarn_file.name} (path: {yarn_file})")
            else:
                print(f"No .yarn files found directly in {current_validated_path}.")

            print("\n--- Testing list_yarn_files (recursive) ---")
            all_yarn_files = list_yarn_files(current_validated_path, recursive=True)
            if all_yarn_files:
                print(f"Found {len(all_yarn_files)} .yarn file(s) recursively in {current_validated_path}:")
                for yarn_file in all_yarn_files:
                    print(f"  - {yarn_file.relative_to(current_validated_path)} (path: {yarn_file})")
            else:
                print(f"No .yarn files found recursively in {current_validated_path}.")

            print("\n--- Testing read_yarn_file_content ---")
            # Try to read the sample file we expect to be in the 'generated' folder based on previous output
            sample_file_path_in_generated = current_validated_path / "generated" / "sample_dialogue_to_import.yarn"
            
            # First, let's check if there's one at the root, as originally intended for testing import
            sample_file_path_at_root = current_validated_path / "sample_dialogue_to_import.yarn"

            target_sample_file_to_read = None

            if sample_file_path_at_root.exists() and sample_file_path_at_root.is_file():
                print(f"Found sample file at root: {sample_file_path_at_root}")
                target_sample_file_to_read = sample_file_path_at_root
            elif sample_file_path_in_generated.exists() and sample_file_path_in_generated.is_file():
                print(f"Found sample file in generated/: {sample_file_path_in_generated}")
                target_sample_file_to_read = sample_file_path_in_generated
            else:
                print(f"Sample file 'sample_dialogue_to_import.yarn' not found at root ({sample_file_path_at_root}) or in generated/ ({sample_file_path_in_generated}).")
                print("Please create it in one of these locations for this test.")

            if target_sample_file_to_read:
                print(f"Attempting to read: {target_sample_file_to_read}")
                content = read_yarn_file_content(target_sample_file_to_read)
                if content:
                    print(f"Successfully read content from {target_sample_file_to_read.name}:")
                    print("-" * 30)
                    print(content[:300] + "..." if len(content) > 300 else content) # Print first 300 chars
                    print("-" * 30)
                else:
                    print(f"Failed to read content from {target_sample_file_to_read.name}.")

        else:
            print("Unity Dialogues Path is not configured or is currently invalid.")
            print(f"Please check 'unity_dialogues_path' in {UI_SETTINGS_FILE.name} and directory permissions.")

    # 2. Example of setting/updating the path (remains commented for manual testing)
    # print("\nTesting set_unity_dialogues_path...")
    # new_test_path = "F:/Unity/Alteir/Alteir_Cursor/Assets/Dialogue_New_Test_Dir" # Make sure this dir exists or adjust logic
    # if set_unity_dialogues_path(new_test_path):
    #     print(f"Path set to {new_test_path}. Verifying...")
    #     verified_path = get_unity_dialogues_path()
    #     if verified_path:
    #         print(f"Verified path: {verified_path}")
    #     else:
    #         print(f"Path {new_test_path} is not valid after setting. Ensure it exists and is a directory.")
    # else:
    #      print(f"Failed to set path to {new_test_path} using set_unity_dialogues_path.")

    # Restore original path if you were testing changes:
    # original_path = "F:/Unity/Alteir/Alteir_Cursor/Assets/Dialogue"
    # if str(get_unity_dialogues_path()) != original_path:
    #     print(f"\nRestoring original path to {original_path}...")
    #     set_unity_dialogues_path(original_path)
    #     verified_path = get_unity_dialogues_path()
    #     if verified_path:
    #         print(f"Path restored and verified: {verified_path}")
    #     else:
    #         print("Failed to restore or verify original path.") 