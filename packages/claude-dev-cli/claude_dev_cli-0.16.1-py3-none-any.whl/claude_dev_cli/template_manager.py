"""Template management for reusable prompts."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any


class Template:
    """Represents a reusable prompt template."""
    
    def __init__(
        self,
        name: str,
        content: str,
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        category: Optional[str] = None,
        builtin: bool = False
    ):
        self.name = name
        self.content = content
        self.description = description or ""
        self.variables = variables or self._extract_variables(content)
        self.category = category or "general"
        self.builtin = builtin
    
    @staticmethod
    def _extract_variables(content: str) -> List[str]:
        """Extract {{variable}} placeholders from content."""
        return list(set(re.findall(r'\{\{(\w+)\}\}', content)))
    
    def render(self, **kwargs: str) -> str:
        """Render template with provided variables."""
        result = self.content
        for var, value in kwargs.items():
            result = result.replace(f'{{{{{var}}}}}', value)
        return result
    
    def get_missing_variables(self, **kwargs: str) -> List[str]:
        """Get list of required variables not provided."""
        return [var for var in self.variables if var not in kwargs]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "content": self.content,
            "description": self.description,
            "variables": self.variables,
            "category": self.category,
            "builtin": self.builtin
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Template":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            content=data["content"],
            description=data.get("description", ""),
            variables=data.get("variables", []),
            category=data.get("category", "general"),
            builtin=data.get("builtin", False)
        )


class TemplateManager:
    """Manages template storage and retrieval."""
    
    # Built-in templates
    BUILTIN_TEMPLATES = [
        Template(
            name="code-review",
            content="""Review this code for:
- Security vulnerabilities
- Performance issues  
- Best practices
- Potential bugs
- Code clarity

{{code}}

Focus on: {{focus}}""",
            description="Comprehensive code review with customizable focus",
            category="review",
            builtin=True
        ),
        Template(
            name="code-review-security",
            content="""Perform a security-focused code review of this code:

{{code}}

Check for:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Authentication/authorization issues
- Data validation problems
- Sensitive data exposure
- CSRF vulnerabilities""",
            description="Security-focused code review",
            category="review",
            builtin=True
        ),
        Template(
            name="test-strategy",
            content="""Generate a comprehensive test strategy for this {{language}} code:

{{code}}

Include:
- Unit tests for core functionality
- Edge cases and error handling
- Integration test scenarios
- Mock/stub suggestions
- Test data examples""",
            description="Generate testing strategy and test cases",
            category="testing",
            builtin=True
        ),
        Template(
            name="debug-error",
            content="""Help me debug this error:

Error: {{error}}

Code context:
{{code}}

Please:
1. Explain what's causing the error
2. Suggest fixes with code examples
3. Explain how to prevent similar errors""",
            description="Debug error with context",
            category="debugging",
            builtin=True
        ),
        Template(
            name="optimize-performance",
            content="""Analyze this code for performance optimization:

{{code}}

Consider:
- Time complexity improvements
- Memory usage optimization
- Algorithm efficiency
- Database query optimization (if applicable)
- Caching opportunities

Provide specific code improvements.""",
            description="Performance optimization analysis",
            category="optimization",
            builtin=True
        ),
        Template(
            name="refactor-clean",
            content="""Refactor this code to improve:
- Readability
- Maintainability
- Code organization
- Naming conventions
- {{language}} idioms

{{code}}

Provide the refactored version with explanations.""",
            description="Clean code refactoring",
            category="refactoring",
            builtin=True
        ),
        Template(
            name="explain-code",
            content="""Explain this code in detail:

{{code}}

Include:
- What it does (high-level)
- How it works (step-by-step)
- Why certain approaches were used
- Potential improvements

Audience level: {{level}}""",
            description="Detailed code explanation",
            category="documentation",
            builtin=True
        ),
        Template(
            name="api-design",
            content="""Design a {{style}} API for:

{{description}}

Include:
- Endpoint definitions
- Request/response formats
- Error handling
- Authentication approach
- Rate limiting considerations""",
            description="API design assistance",
            category="design",
            builtin=True
        ),
    ]
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.templates_file = templates_dir / "templates.json"
        
        # Check if templates_dir exists as a file (not directory)
        if self.templates_dir.exists() and not self.templates_dir.is_dir():
            raise RuntimeError(
                f"Templates directory path {self.templates_dir} exists but is not a directory. "
                f"Please remove or rename this file."
            )
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if templates_file is a directory (not file)
        if self.templates_file.exists() and self.templates_file.is_dir():
            raise RuntimeError(
                f"Templates file {self.templates_file} is a directory. "
                f"Please remove this directory."
            )
        
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load templates from disk."""
        self.templates: Dict[str, Template] = {}
        
        # Load built-in templates
        for template in self.BUILTIN_TEMPLATES:
            self.templates[template.name] = template
        
        # Load user templates
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r') as f:
                    data = json.load(f)
                for template_data in data.get("templates", []):
                    template = Template.from_dict(template_data)
                    self.templates[template.name] = template
            except Exception:
                pass
    
    def _save_templates(self) -> None:
        """Save user templates to disk."""
        # Only save non-builtin templates
        user_templates = [
            t.to_dict() for t in self.templates.values() if not t.builtin
        ]
        
        with open(self.templates_file, 'w') as f:
            json.dump({"templates": user_templates}, f, indent=2)
    
    def add_template(self, template: Template) -> None:
        """Add or update a template."""
        if template.name in self.templates and self.templates[template.name].builtin:
            raise ValueError(f"Cannot override builtin template: {template.name}")
        
        self.templates[template.name] = template
        self._save_templates()
    
    def get_template(self, name: str) -> Optional[Template]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_templates(
        self,
        category: Optional[str] = None,
        builtin_only: bool = False,
        user_only: bool = False
    ) -> List[Template]:
        """List templates with optional filters."""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if builtin_only:
            templates = [t for t in templates if t.builtin]
        elif user_only:
            templates = [t for t in templates if not t.builtin]
        
        return sorted(templates, key=lambda t: (t.category, t.name))
    
    def delete_template(self, name: str) -> bool:
        """Delete a template (cannot delete builtins)."""
        if name not in self.templates:
            return False
        
        if self.templates[name].builtin:
            raise ValueError(f"Cannot delete builtin template: {name}")
        
        del self.templates[name]
        self._save_templates()
        return True
    
    def get_categories(self) -> List[str]:
        """Get list of all template categories."""
        return sorted(set(t.category for t in self.templates.values()))
