from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class YarnNode:
    """Represents a single node in a Yarn Spinner dialogue file."""
    title: str = ""
    tags: List[str] = field(default_factory=list)
    body: str = ""
    header_lines: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = []
        parts.append(f"title: {self.title}")
        if self.tags:
            parts.append(f"tags: {' '.join(self.tags)}")
        if self.header_lines:
            parts.extend(self.header_lines) # header_lines are already strings
        parts.append("---")
        parts.append(self.body.strip()) # Add body, ensuring it ends with a newline if not empty
        parts.append("===")
        return "\n".join(parts) + "\n" # Ensure a final newline for standalone node representation

def parse_yarn_file(file_path: Path) -> List[YarnNode]:
    """Parses a .yarn file and returns a list of YarnNode objects.

    Args:
        file_path: The Path object pointing to the .yarn file.

    Returns:
        A list of YarnNode objects found in the file.
        Returns an empty list if the file cannot be read or is empty.
    """
    nodes: List[YarnNode] = []
    if not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        return nodes

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return nodes

    current_node: Optional[YarnNode] = None
    in_header = True
    current_body_lines: List[str] = []

    for line_num, raw_line in enumerate(lines):
        line = raw_line.rstrip('\r\n') # Keep internal newlines, remove trailing only

        if line.startswith("title:"):
            if current_node:
                current_node.body = "\n".join(current_body_lines)
                nodes.append(current_node)
                logger.debug(f"Completed node: {current_node.title}, Body lines: {len(current_body_lines)}")
            
            current_node = YarnNode(title=line.replace("title:", "", 1).strip())
            current_body_lines = []
            in_header = True
            logger.debug(f"Started new node: {current_node.title}")
        
        elif current_node and line.startswith("tags:") and in_header:
            current_node.tags = [tag.strip() for tag in line.replace("tags:", "", 1).strip().split(' ') if tag.strip()]
            logger.debug(f"  Node '{current_node.title}' tags: {current_node.tags}")
        
        elif current_node and line == "---" and in_header:
            in_header = False
            logger.debug(f"  Node '{current_node.title}' header ended.")

        elif current_node and line == "===":
            current_node.body = "\n".join(current_body_lines)
            nodes.append(current_node)
            logger.debug(f"Completed node: {current_node.title} with '===', Body lines: {len(current_body_lines)}")
            current_node = None
            current_body_lines = []
            in_header = True
        
        elif current_node:
            if in_header:
                current_node.header_lines.append(line) # Store stripped line for header
                logger.debug(f"  Node '{current_node.title}' header line: {line}")
            else: # In body
                current_body_lines.append(raw_line.rstrip('\r\n')) # Append raw_line (maintaining internal newlines) to body lines
                # logger.debug(f"  Node '{current_node.title}' body line added: {raw_line.strip()}")

    if current_node: # Add the last node if file doesn't end with === or if it's the only node
        current_node.body = "\n".join(current_body_lines)
        nodes.append(current_node)
        logger.debug(f"Completed last node (EOF): {current_node.title}, Body lines: {len(current_body_lines)}")
        
    logger.info(f"Parsed {len(nodes)} nodes from {file_path.name}")
    return nodes

if __name__ == '__main__':
    dummy_yarn_content = (
        "title: Node1\n"
        "tags: tagA tagB\n"
        "character: Alice\n"
        "position: 10,20\n"
        "---\n"
        "Hello, this is Alice.\n"
        "This is another line for Alice.\n"
        "===\n"
        "title: Node2\n"
        "---\n"
        "This is a node with no tags or explicit character.\n"
        "It has multiple lines.\n"
        "    Indented line here.\n"
        "===\n"
        "title: Node3\n"
        "tags: tagC\n"
        "---\n"
        "This node only has a title and tags.\n"
        "===\n"
        "title: EmptyNodeBody\n"
        "---\n"
        "===\n"
        "title: NodeWithOnlyTitleAndBody\n"
        "---\n"
        "Body directly after '---'.\n"
        "===\n"
        "title: NodeEndingEOF\n"
        "tags: final\n"
        "character: Bob\n"
        "---\n"
        "This is Bob, and this node might not have a ===\n"
        "And another line for Bob."
    )
    test_file_path = Path("__test_parser.yarn")
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(dummy_yarn_content)

    logging.basicConfig(level=logging.DEBUG)
    logger.info("Testing Yarn Parser...")
    
    parsed_nodes = parse_yarn_file(test_file_path)
    
    if not parsed_nodes:
        logger.error("Parser returned no nodes for the test file.")
    else:
        logger.info(f"Successfully parsed {len(parsed_nodes)} nodes:")
        for i, node in enumerate(parsed_nodes):
            logger.info(f"--- Node {i+1} --- DUMP ---")
            logger.info(f"Title: '{node.title}'")
            logger.info(f"Tags: {node.tags}")
            logger.info(f"Header Lines: {node.header_lines}")
            body_preview = node.body.replace('\n', ' ')[:70]
            logger.info(f"Body (preview): '{body_preview}...' (length: {len(node.body)})")
            # logger.info(f"Reconstructed node {i+1}:\n{str(node)}") # __str__ might need refinement
            logger.info("-------------------------")

    logger.info("\nTesting with a non-existent file:")
    parse_yarn_file(Path("non_existent_file.yarn"))

    logger.info("\nTesting with an empty file:")
    empty_file_path = Path("__empty_test.yarn")
    open(empty_file_path, 'w').close()
    parse_yarn_file(empty_file_path)
    
    logger.info("\nTest finished. Check logs. Consider deleting test files: __test_parser.yarn, __empty_test.yarn") 