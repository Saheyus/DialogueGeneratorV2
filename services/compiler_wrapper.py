from __future__ import annotations

import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CompilerWrapper:
    """Wraps the yarnspinner-cli compile command."""

    def __init__(self, yarn_spinner_cli_path: str = "yarnspinner-cli"):
        """
        Initializes the CompilerWrapper.

        Args:
            yarn_spinner_cli_path (str): The path or command name for yarnspinner-cli.
                                         Defaults to "yarnspinner-cli" assuming it's in PATH.
        """
        self.cli_path = yarn_spinner_cli_path

    def compile_yarn_file(self, yarn_file_path: Path) -> dict[str, bool | str]:
        """
        Compiles a .yarn file using yarnspinner-cli.

        Args:
            yarn_file_path (Path): The absolute path to the .yarn file.

        Returns:
            dict: A dictionary containing:
                'success': bool, True if compilation succeeded, False otherwise.
                'output': str, The combined stdout and stderr from the command.
                'json_output_path': str, path to the compiled .yarn.json file if successful, else empty.
                'csv_output_path': str, path to the compiled .csv file if successful, else empty.
        """
        if not yarn_file_path.exists() or not yarn_file_path.is_file():
            logger.error(f"Yarn file not found or is not a file: {yarn_file_path}")
            return {
                "success": False, 
                "output": f"Error: File not found {yarn_file_path}",
                "json_output_path": "",
                "csv_output_path": ""
            }

        # Output files will be in the same directory as the input file
        # yarnspinner-cli compile <input.yarn> -> creates <input.yarn.json> and <input.yarnc.bytes>
        # It also creates a CSV for string tags: <input_tags.csv>
        # We are primarily interested in the .yarn.json for now.
        expected_json_output = yarn_file_path.with_suffix(".yarn.json")
        # The CSV file is named based on the input file, not yarn.json
        expected_csv_output = yarn_file_path.with_name(f"{yarn_file_path.stem}_tags.csv")

        command = [self.cli_path, "compile", str(yarn_file_path)]
        logger.info(f"Executing compile command: {' '.join(command)}")

        try:
            process = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False, # We check the returncode manually
                shell=False # Important for security and correctness
            )
            
            output_log = f"Return code: {process.returncode}\n"
            output_log += f"Stdout:\n{process.stdout}\n"
            output_log += f"Stderr:\n{process.stderr}\n"
            logger.debug(f"Compilation process output for {yarn_file_path}:\n{output_log}")

            if process.returncode == 0:
                # Check if the primary output file (.yarn.json) was created
                if expected_json_output.exists():
                    logger.info(f"Compilation successful for {yarn_file_path}. Output: {expected_json_output}")
                    return {
                        "success": True, 
                        "output": process.stdout if process.stdout else "Compilation successful.",
                        "json_output_path": str(expected_json_output),
                        "csv_output_path": str(expected_csv_output) if expected_csv_output.exists() else ""
                    }
                else:
                    logger.error(f"Compilation command returned 0 but output file {expected_json_output} not found.")
                    return {
                        "success": False, 
                        "output": f"Compilation seemed successful but output file {expected_json_output} not found.\n{process.stdout}\n{process.stderr}",
                        "json_output_path": "",
                        "csv_output_path": ""
                    }
            else:
                logger.warning(f"Compilation failed for {yarn_file_path}. Return code: {process.returncode}")
                return {
                    "success": False, 
                    "output": f"Compilation failed.\nStdout: {process.stdout}\nStderr: {process.stderr}",
                    "json_output_path": "",
                    "csv_output_path": ""
                }

        except FileNotFoundError:
            logger.error(f"'{self.cli_path}' command not found. Please ensure yarnspinner-cli is installed and in PATH.")
            return {
                "success": False, 
                "output": f"Error: '{self.cli_path}' command not found. Is yarnspinner-cli installed and in PATH?",
                "json_output_path": "",
                "csv_output_path": ""
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred during compilation of {yarn_file_path}: {e}", exc_info=True)
            return {
                "success": False, 
                "output": f"An unexpected error occurred: {str(e)}",
                "json_output_path": "",
                "csv_output_path": ""
            }

if __name__ == '__main__':
    # Basic test - ensure you have a test.yarn file in the same directory or adjust path
    logging.basicConfig(level=logging.DEBUG)
    test_file_dir = Path(__file__).parent
    test_yarn_file = test_file_dir / "test.yarn" 
    
    # Create a dummy test.yarn if it doesn't exist
    if not test_yarn_file.exists():
        print(f"Creating dummy {test_yarn_file} for testing...")
        test_yarn_file.write_text(
            "title: TestNode\n---\nPlayer: This is a test line.\n===", 
            encoding='utf-8'
        )

    print(f"Attempting to compile: {test_yarn_file}")
    wrapper = CompilerWrapper()
    result = wrapper.compile_yarn_file(test_yarn_file)
    print("Compilation Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    # Clean up dummy files if created by this test script
    # yarnspinner-cli might create .yarn.json, .yarnc.bytes, and _tags.csv
    if test_yarn_file.name == "test.yarn": # Only delete if it's the dummy
        json_out = test_yarn_file.with_suffix(".yarn.json")
        bytes_out = test_yarn_file.with_suffix(".yarnc.bytes")
        csv_out = test_yarn_file.with_name(f"{test_yarn_file.stem}_tags.csv")
        
        if json_out.exists(): json_out.unlink()
        if bytes_out.exists(): bytes_out.unlink()
        if csv_out.exists(): csv_out.unlink()
        if test_yarn_file.exists() and test_yarn_file.read_text(encoding='utf-8').startswith("title: TestNode"): 
             # only delete if it's the dummy we created
            # test_yarn_file.unlink() # Option to delete the test.yarn itself
            pass 
    print("Basic test complete.") 