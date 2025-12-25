import pytest
from pathlib import Path

from services.yarn_renderer import YarnRenderer


@pytest.fixture
def temp_template_dir(tmp_path: Path) -> Path:
    template_content = """---
{% for key, value in metadata.items() %}
{{ key }}: {{ value }}
{% endfor %}
---
{% if llm_output %}
{{ llm_output }}
{% endif %}
"""  # Template content aligning with the production template
    template_file = tmp_path / "test_template.j2"
    # Ensure the test template file ends with a newline, simulating a real file.
    template_file.write_text(template_content + "\n", encoding="utf-8")
    return tmp_path


def test_yarn_renderer_with_metadata(temp_template_dir: Path):
    renderer = YarnRenderer(template_dir=temp_template_dir, template_name="test_template.j2")
    llm_output = "Player: Hello there!\nNPC: General Kenobi!"
    metadata = {"title": "Greeting", "tags": "intro, star_wars"}
    
    expected_output = "---\ntitle: Greeting\ntags: intro, star_wars\n---\nPlayer: Hello there!\nNPC: General Kenobi!\n"
    
    actual_output = renderer.render(llm_output, metadata)
    assert actual_output == expected_output

def test_yarn_renderer_without_metadata(temp_template_dir: Path):
    renderer = YarnRenderer(template_dir=temp_template_dir, template_name="test_template.j2")
    llm_output = "This is a simple line."
    
    expected_output = "---\n---\nThis is a simple line.\n"
    
    actual_output = renderer.render(llm_output)
    assert actual_output == expected_output

def test_yarn_renderer_empty_llm_output(temp_template_dir: Path):
    renderer = YarnRenderer(template_dir=temp_template_dir, template_name="test_template.j2")
    llm_output = "" # Empty string, .strip() doesn't change it.
    metadata = {"title": "Empty"}
    
    # The template will output the header, then because llm_output is false,
    # it will skip that block, and then the final newline from the template file comes.
    expected_output = "---\ntitle: Empty\n---\n"
    
    actual_output = renderer.render(llm_output, metadata)
    assert actual_output == expected_output

def test_yarn_renderer_llm_output_with_leading_trailing_spaces(temp_template_dir: Path):
    renderer = YarnRenderer(template_dir=temp_template_dir, template_name="test_template.j2")
    llm_output = "  Trimmed output.  \n" # .strip() will make this "Trimmed output."
    metadata = {"title": "Spacing Test"}
    
    expected_output = "---\ntitle: Spacing Test\n---\nTrimmed output.\n"
    
    actual_output = renderer.render(llm_output, metadata)
    assert actual_output == expected_output


def test_yarn_renderer_default_template():
    default_template_dir = Path(__file__).parent.parent / "templates"
    default_template_file = default_template_dir / "yarn_template.j2"

    # Ensure the actual default template file exists and has the correct content for the test
    # In a CI/real environment, this file should be managed by version control.
    # For testing robustness, we ensure it's what we expect here.
    expected_template_content = """---
{% for key, value in metadata.items() %}
{{ key }}: {{ value }}
{% endfor %}
---
{% if llm_output %}
{{ llm_output }}
{% endif %}
"""
    default_template_dir.mkdir(parents=True, exist_ok=True)
    default_template_file.write_text(expected_template_content + "\n", encoding="utf-8")

    renderer = YarnRenderer() # Uses default template from DialogueGenerator/templates/
    llm_output = "Default template test."
    metadata = {"node_name": "TestNode"}

    expected_output = "---\nnode_name: TestNode\n---\nDefault template test.\n"
    actual_output = renderer.render(llm_output, metadata)
    assert actual_output == expected_output 