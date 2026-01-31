"""Warp terminal integration for enhanced output formatting."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def format_as_warp_block(
    content: str,
    title: Optional[str] = None,
    language: Optional[str] = None,
    actions: Optional[List[Dict[str, str]]] = None
) -> str:
    """Format content as a Warp block with optional actions.
    
    Warp blocks support special formatting and click-to-run actions.
    """
    block_parts = []
    
    if title:
        block_parts.append(f"### {title}")
        block_parts.append("")
    
    # Add content with language if code block
    if language:
        block_parts.append(f"```{language}")
        block_parts.append(content)
        block_parts.append("```")
    else:
        block_parts.append(content)
    
    # Add actions if provided
    if actions:
        block_parts.append("")
        block_parts.append("**Actions:**")
        for action in actions:
            label = action.get('label', 'Run')
            command = action.get('command', '')
            block_parts.append(f"- [{label}](`{command}`)")
    
    return "\n".join(block_parts)


def generate_warp_workflow(
    workflow_name: str,
    commands: List[Dict[str, str]],
    output_path: Optional[Path] = None
) -> str:
    """Generate a Warp workflow file from command list.
    
    Warp workflows allow users to execute predefined command sequences.
    """
    workflow = {
        "name": workflow_name,
        "command": "://" + workflow_name.lower().replace(" ", "-"),
        "tags": ["claude-dev-cli"],
        "description": f"Generated from claude-dev-cli",
        "arguments": [],
        "source_specs": [
            {
                "type": "command",
                "command": cmd.get('command', ''),
                "description": cmd.get('description', '')
            }
            for cmd in commands
        ]
    }
    
    workflow_yaml = yaml.dump(workflow, default_flow_style=False, sort_keys=False)
    
    if output_path:
        output_path.write_text(workflow_yaml)
    
    return workflow_yaml


def export_builtin_workflows(output_dir: Path) -> List[Path]:
    """Export built-in Warp workflows for common claude-dev-cli tasks."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    workflows = [
        {
            "name": "Code Review Workflow",
            "commands": [
                {
                    "command": "cdc review {{file}}",
                    "description": "Review code for issues"
                },
                {
                    "command": "cdc review {{file}} --interactive",
                    "description": "Review with follow-up questions"
                }
            ]
        },
        {
            "name": "Test Generation Workflow",
            "commands": [
                {
                    "command": "cdc generate tests {{file}} -o tests/test_{{file}}",
                    "description": "Generate tests"
                },
                {
                    "command": "pytest tests/test_{{file}}",
                    "description": "Run tests"
                }
            ]
        },
        {
            "name": "Refactor Workflow",
            "commands": [
                {
                    "command": "cdc refactor {{file}} --interactive",
                    "description": "Get refactoring suggestions"
                },
                {
                    "command": "cdc review {{file}}",
                    "description": "Review changes"
                },
                {
                    "command": "git add {{file}} && cdc git commit",
                    "description": "Commit changes"
                }
            ]
        },
        {
            "name": "Debug Workflow",
            "commands": [
                {
                    "command": "python {{file}} 2>&1 | cdc debug",
                    "description": "Run and debug errors"
                },
                {
                    "command": "cdc debug -f {{file}} -e \"{{error}}\"",
                    "description": "Debug specific error"
                }
            ]
        }
    ]
    
    created_files = []
    for workflow in workflows:
        filename = workflow['name'].lower().replace(' ', '-') + '.yaml'
        filepath = output_dir / filename
        generate_warp_workflow(
            workflow['name'],
            workflow['commands'],
            filepath
        )
        created_files.append(filepath)
    
    return created_files


def format_code_review_for_warp(review_output: str, file_path: str) -> str:
    """Format code review output as Warp block with actions."""
    actions = [
        {
            "label": "Review with follow-up",
            "command": f"cdc review {file_path} --interactive"
        },
        {
            "label": "Refactor",
            "command": f"cdc refactor {file_path} --interactive"
        }
    ]
    
    return format_as_warp_block(
        content=review_output,
        title="Code Review",
        actions=actions
    )


def format_test_generation_for_warp(test_output: str, file_path: str) -> str:
    """Format test generation output as Warp block with actions."""
    test_file = f"tests/test_{Path(file_path).name}"
    
    actions = [
        {
            "label": "Save tests",
            "command": f"cdc generate tests {file_path} -o {test_file}"
        },
        {
            "label": "Run tests",
            "command": f"pytest {test_file}"
        }
    ]
    
    return format_as_warp_block(
        content=test_output,
        title="Generated Tests",
        language="python",
        actions=actions
    )


def create_warp_launch_config(
    name: str,
    command: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a Warp launch configuration.
    
    Launch configs allow quick environment setup in Warp.
    """
    config = {
        "name": name,
        "command": command,
        "type": "terminal"
    }
    
    if cwd:
        config["cwd"] = cwd
    
    if env:
        config["env"] = env
    
    return config


def export_launch_configs(output_path: Path) -> None:
    """Export Warp launch configurations for claude-dev-cli."""
    configs = [
        create_warp_launch_config(
            name="Claude Dev CLI - Interactive",
            command="cdc interactive"
        ),
        create_warp_launch_config(
            name="Claude Dev CLI - Review Mode",
            command="cdc review"
        ),
        create_warp_launch_config(
            name="Claude Dev CLI - Test Generation",
            command="cdc generate tests"
        )
    ]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"launch_configurations": configs}, f, indent=2)
