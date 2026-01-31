"""Workflow execution engine for chaining AI operations."""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

import yaml
from rich.console import Console


@dataclass
class StepResult:
    """Result from executing a workflow step."""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    """Context passed between workflow steps."""
    variables: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, StepResult] = field(default_factory=dict)


class WorkflowEngine:
    """Execute workflow definitions with step chaining."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def load_workflow(self, path: Path) -> Dict[str, Any]:
        """Load workflow from YAML file."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def execute(
        self,
        workflow: Union[Dict[str, Any], Path],
        initial_vars: Optional[Dict[str, Any]] = None
    ) -> WorkflowContext:
        """Execute a workflow definition."""
        # Load from file if path provided
        if isinstance(workflow, Path):
            workflow = self.load_workflow(workflow)
        
        # Initialize context
        context = WorkflowContext(variables=initial_vars or {})
        
        # Extract workflow metadata
        name = workflow.get('name', 'Unnamed Workflow')
        description = workflow.get('description', '')
        steps = workflow.get('steps', [])
        
        self.console.print(f"\n[bold cyan]Running workflow:[/bold cyan] {name}")
        if description:
            self.console.print(f"[dim]{description}[/dim]")
        
        # Execute steps
        for i, step in enumerate(steps, 1):
            step_name = step.get('name', f'step-{i}')
            
            # Check conditional
            if 'if' in step:
                condition = self._evaluate_condition(step['if'], context)
                if not condition:
                    self.console.print(f"[yellow]↷[/yellow] Skipping step {i}: {step_name} (condition false)")
                    continue
            
            self.console.print(f"\n[bold]Step {i}:[/bold] {step_name}")
            
            # Check for approval gate
            if step.get('approval_required', False):
                if not self._request_approval(step_name):
                    self.console.print("[yellow]Workflow stopped by user[/yellow]")
                    break
            
            # Execute step
            try:
                result = self._execute_step(step, context)
                context.step_results[step_name] = result
                
                if result.success:
                    self.console.print(f"[green]✓[/green] {step_name} completed")
                else:
                    self.console.print(f"[red]✗[/red] {step_name} failed: {result.error}")
                    
                    # Check if workflow should continue on error
                    if not step.get('continue_on_error', False):
                        self.console.print("[red]Workflow stopped due to error[/red]")
                        break
            
            except Exception as e:
                self.console.print(f"[red]Error in step {step_name}: {e}[/red]")
                if not step.get('continue_on_error', False):
                    break
        
        self.console.print("\n[bold green]Workflow completed[/bold green]")
        return context
    
    def _execute_step(self, step: Dict[str, Any], context: WorkflowContext) -> StepResult:
        """Execute a single workflow step."""
        # Determine step type
        if 'command' in step:
            return self._execute_command_step(step, context)
        elif 'shell' in step:
            return self._execute_shell_step(step, context)
        elif 'set' in step:
            return self._execute_set_step(step, context)
        else:
            return StepResult(
                success=False,
                output="",
                error="Unknown step type"
            )
    
    def _execute_command_step(self, step: Dict[str, Any], context: WorkflowContext) -> StepResult:
        """Execute a cdc command step."""
        command = step['command']
        args = step.get('args', {})
        
        # Interpolate variables in args
        interpolated_args = self._interpolate_variables(args, context)
        
        # Import here to avoid circular dependency
        from claude_dev_cli.commands import (
            generate_tests, code_review, debug_code, 
            generate_docs, refactor_code, git_commit_message
        )
        from claude_dev_cli.core import ClaudeClient
        
        # Map commands to functions
        command_map = {
            'generate tests': generate_tests,
            'review': code_review,
            'debug': debug_code,
            'generate docs': generate_docs,
            'refactor': refactor_code,
            'git commit': git_commit_message,
        }
        
        # Handle special commands that need different execution
        if command == 'ask':
            return self._execute_ask_command(interpolated_args)
        elif command in ['generate code', 'generate feature']:
            # These are CLI-only commands that would need file generation logic
            # For now, redirect to shell equivalent
            return StepResult(
                success=False,
                output="",
                error=f"Command '{command}' not yet supported in workflows. Use shell step with 'cdc {command}' instead."
            )
        
        if command not in command_map:
            return StepResult(
                success=False,
                output="",
                error=f"Unknown command: {command}. Supported: {', '.join(command_map.keys())}, ask"
            )
        
        try:
            func = command_map[command]
            
            # Build function arguments
            func_args = {}
            if 'file' in interpolated_args:
                func_args['file_path'] = interpolated_args['file']
            if 'error' in interpolated_args:
                func_args['error_message'] = interpolated_args['error']
            if 'api' in interpolated_args:
                func_args['api_config_name'] = interpolated_args['api']
            if 'model' in interpolated_args:
                func_args['model'] = interpolated_args['model']
            
            # Execute
            result = func(**func_args)
            
            # Store output in context for next steps
            if 'output_var' in step:
                context.variables[step['output_var']] = result
            
            return StepResult(
                success=True,
                output=result,
                metadata={'command': command}
            )
        
        except Exception as e:
            return StepResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def _execute_ask_command(self, args: Dict[str, Any]) -> StepResult:
        """Execute an ask command step."""
        try:
            from claude_dev_cli.core import ClaudeClient
            
            prompt = args.get('prompt', args.get('question', ''))
            if not prompt:
                return StepResult(
                    success=False,
                    output="",
                    error="ask command requires 'prompt' or 'question' argument"
                )
            
            api = args.get('api')
            model = args.get('model')
            system = args.get('system')
            
            client = ClaudeClient(api_config_name=api)
            result = client.call(prompt, system_prompt=system, model=model)
            
            return StepResult(
                success=True,
                output=result,
                metadata={'command': 'ask'}
            )
        
        except Exception as e:
            return StepResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def _execute_shell_step(self, step: Dict[str, Any], context: WorkflowContext) -> StepResult:
        """Execute a shell command step."""
        command = step['shell']
        
        # Interpolate variables
        command = self._interpolate_string(command, context)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )
            
            success = result.returncode == 0
            output = result.stdout or result.stderr
            
            # Store output in context
            if 'output_var' in step:
                context.variables[step['output_var']] = output.strip()
            
            return StepResult(
                success=success,
                output=output,
                error=result.stderr if not success else None,
                metadata={'returncode': result.returncode}
            )
        
        except Exception as e:
            return StepResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def _execute_set_step(self, step: Dict[str, Any], context: WorkflowContext) -> StepResult:
        """Execute a variable assignment step."""
        var_name = step['set']
        value = step.get('value', '')
        
        # Interpolate value
        value = self._interpolate_value(value, context)
        
        context.variables[var_name] = value
        
        return StepResult(
            success=True,
            output=str(value),
            metadata={'variable': var_name}
        )
    
    def _interpolate_variables(
        self,
        data: Union[Dict, List, str, Any],
        context: WorkflowContext
    ) -> Any:
        """Recursively interpolate variables in data structures."""
        if isinstance(data, dict):
            return {k: self._interpolate_variables(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._interpolate_variables(item, context) for item in data]
        elif isinstance(data, str):
            return self._interpolate_string(data, context)
        else:
            return data
    
    def _interpolate_string(self, text: str, context: WorkflowContext) -> str:
        """Interpolate {{variable}} placeholders in string."""
        def replace(match: re.Match) -> str:
            var_path = match.group(1)
            return str(self._resolve_variable(var_path, context))
        
        return re.sub(r'\{\{([^}]+)\}\}', replace, text)
    
    def _interpolate_value(self, value: Any, context: WorkflowContext) -> Any:
        """Interpolate a single value."""
        if isinstance(value, str):
            return self._interpolate_string(value, context)
        return value
    
    def _resolve_variable(self, var_path: str, context: WorkflowContext) -> Any:
        """Resolve a variable path like 'step1.output' or 'vars.filename'."""
        parts = var_path.strip().split('.')
        
        # Check step results first
        if len(parts) >= 2 and parts[0] in context.step_results:
            step_result = context.step_results[parts[0]]
            if parts[1] == 'output':
                return step_result.output
            elif parts[1] == 'success':
                return step_result.success
            elif parts[1] == 'error':
                return step_result.error or ''
        
        # Check variables
        if parts[0] in context.variables:
            value = context.variables[parts[0]]
            # Support nested access for dicts
            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(part, '')
                else:
                    return ''
            return value
        
        return f'{{{{{var_path}}}}}'  # Return placeholder if not found
    
    def _evaluate_condition(self, condition: str, context: WorkflowContext) -> bool:
        """Evaluate a simple condition expression."""
        # Interpolate variables
        evaluated = self._interpolate_string(condition, context)
        
        # Simple boolean evaluation
        if evaluated.lower() in ('true', '1', 'yes'):
            return True
        if evaluated.lower() in ('false', '0', 'no', ''):
            return False
        
        # Try to evaluate as Python expression (limited to safe operations)
        try:
            # Only allow simple comparisons
            if any(op in evaluated for op in ['==', '!=', '>', '<', '>=', '<=']):
                return eval(evaluated, {"__builtins__": {}}, {})
        except Exception:
            pass
        
        return bool(evaluated)
    
    def _request_approval(self, step_name: str) -> bool:
        """Request user approval to proceed."""
        self.console.print(f"\n[yellow]⚠ Approval required for:[/yellow] {step_name}")
        response = self.console.input("[cyan]Proceed? (y/n):[/cyan] ").strip().lower()
        return response in ('y', 'yes')


def list_workflows(workflow_dir: Path) -> List[Dict[str, str]]:
    """List available workflows in a directory."""
    if not workflow_dir.exists():
        return []
    
    workflows = []
    for file in workflow_dir.glob('*.yaml'):
        try:
            with open(file, 'r') as f:
                data = yaml.safe_load(f)
            
            workflows.append({
                'name': data.get('name', file.stem),
                'description': data.get('description', ''),
                'file': str(file),
                'steps': len(data.get('steps', []))
            })
        except Exception:
            continue
    
    return workflows
