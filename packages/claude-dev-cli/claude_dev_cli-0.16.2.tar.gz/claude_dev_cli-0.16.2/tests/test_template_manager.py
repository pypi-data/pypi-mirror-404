"""Tests for template manager."""

import json
import pytest
from pathlib import Path
from claude_dev_cli.template_manager import Template, TemplateManager


class TestTemplate:
    """Test Template class."""
    
    def test_template_creation(self):
        """Test creating a basic template."""
        tmpl = Template(
            name="test",
            content="Hello {{name}}",
            description="Test template",
            category="test"
        )
        
        assert tmpl.name == "test"
        assert tmpl.content == "Hello {{name}}"
        assert tmpl.description == "Test template"
        assert tmpl.category == "test"
        assert tmpl.builtin is False
    
    def test_extract_variables(self):
        """Test variable extraction from content."""
        tmpl = Template(
            name="test",
            content="Hello {{name}}, you are {{age}} years old. {{name}} is cool."
        )
        
        # Should extract unique variables
        assert set(tmpl.variables) == {"name", "age"}
    
    def test_render_template(self):
        """Test rendering template with variables."""
        tmpl = Template(
            name="test",
            content="Hello {{name}}, you are {{age}} years old."
        )
        
        result = tmpl.render(name="Alice", age="30")
        assert result == "Hello Alice, you are 30 years old."
    
    def test_render_partial(self):
        """Test rendering with missing variables."""
        tmpl = Template(
            name="test",
            content="Hello {{name}}, you are {{age}} years old."
        )
        
        result = tmpl.render(name="Bob")
        # Missing variables remain as placeholders
        assert result == "Hello Bob, you are {{age}} years old."
    
    def test_get_missing_variables(self):
        """Test checking for missing variables."""
        tmpl = Template(
            name="test",
            content="Hello {{name}}, you are {{age}} years old."
        )
        
        assert tmpl.get_missing_variables(name="Alice") == ["age"]
        assert tmpl.get_missing_variables(name="Alice", age="30") == []
    
    def test_to_dict(self):
        """Test serialization to dict."""
        tmpl = Template(
            name="test",
            content="Hello {{name}}",
            description="Test template",
            category="test",
            builtin=True
        )
        
        data = tmpl.to_dict()
        assert data["name"] == "test"
        assert data["content"] == "Hello {{name}}"
        assert data["description"] == "Test template"
        assert data["category"] == "test"
        assert data["builtin"] is True
        assert "name" in data["variables"]
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "name": "test",
            "content": "Hello {{name}}",
            "description": "Test template",
            "category": "test",
            "builtin": True,
            "variables": ["name"]
        }
        
        tmpl = Template.from_dict(data)
        assert tmpl.name == "test"
        assert tmpl.content == "Hello {{name}}"
        assert tmpl.description == "Test template"
        assert tmpl.category == "test"
        assert tmpl.builtin is True
        assert tmpl.variables == ["name"]


class TestTemplateManager:
    """Test TemplateManager class."""
    
    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory for tests."""
        return tmp_path / "templates"
    
    @pytest.fixture
    def manager(self, temp_dir: Path) -> TemplateManager:
        """Create template manager with temp directory."""
        return TemplateManager(temp_dir)
    
    def test_manager_creation(self, temp_dir: Path, manager: TemplateManager):
        """Test manager creates directory structure."""
        assert temp_dir.exists()
        assert manager.templates_file == temp_dir / "templates.json"
    
    def test_builtin_templates_loaded(self, manager: TemplateManager):
        """Test built-in templates are loaded."""
        # Should have 8 built-in templates
        builtins = [t for t in manager.templates.values() if t.builtin]
        assert len(builtins) == 8
        
        # Check specific templates exist
        assert "code-review" in manager.templates
        assert "test-strategy" in manager.templates
        assert "debug-error" in manager.templates
    
    def test_add_user_template(self, manager: TemplateManager):
        """Test adding a user template."""
        tmpl = Template(
            name="my-template",
            content="Custom content {{var}}",
            description="My template"
        )
        
        manager.add_template(tmpl)
        
        # Should be in memory
        assert "my-template" in manager.templates
        
        # Should be saved to disk
        assert manager.templates_file.exists()
        with open(manager.templates_file) as f:
            data = json.load(f)
        
        assert len(data["templates"]) == 1
        assert data["templates"][0]["name"] == "my-template"
    
    def test_cannot_override_builtin(self, manager: TemplateManager):
        """Test cannot override built-in templates."""
        tmpl = Template(
            name="code-review",
            content="Override attempt"
        )
        
        with pytest.raises(ValueError, match="Cannot override builtin"):
            manager.add_template(tmpl)
    
    def test_get_template(self, manager: TemplateManager):
        """Test getting template by name."""
        # Get built-in
        tmpl = manager.get_template("code-review")
        assert tmpl is not None
        assert tmpl.name == "code-review"
        
        # Get non-existent
        assert manager.get_template("nonexistent") is None
    
    def test_list_templates_all(self, manager: TemplateManager):
        """Test listing all templates."""
        templates = manager.list_templates()
        
        # Should have 8 built-ins
        assert len(templates) >= 8
        
        # Should be sorted by category then name
        categories = [t.category for t in templates]
        assert categories == sorted(categories)
    
    def test_list_templates_by_category(self, manager: TemplateManager):
        """Test filtering templates by category."""
        review_templates = manager.list_templates(category="review")
        
        assert len(review_templates) >= 2  # code-review and code-review-security
        assert all(t.category == "review" for t in review_templates)
    
    def test_list_templates_builtin_only(self, manager: TemplateManager):
        """Test listing only built-in templates."""
        # Add a user template
        manager.add_template(Template(name="user-tmpl", content="test"))
        
        builtins = manager.list_templates(builtin_only=True)
        assert len(builtins) == 8
        assert all(t.builtin for t in builtins)
    
    def test_list_templates_user_only(self, manager: TemplateManager):
        """Test listing only user templates."""
        # Add user templates
        manager.add_template(Template(name="user-1", content="test1"))
        manager.add_template(Template(name="user-2", content="test2"))
        
        user_templates = manager.list_templates(user_only=True)
        assert len(user_templates) == 2
        assert all(not t.builtin for t in user_templates)
    
    def test_delete_user_template(self, manager: TemplateManager):
        """Test deleting user template."""
        # Add template
        manager.add_template(Template(name="to-delete", content="test"))
        assert "to-delete" in manager.templates
        
        # Delete it
        result = manager.delete_template("to-delete")
        assert result is True
        assert "to-delete" not in manager.templates
        
        # Should be removed from disk
        with open(manager.templates_file) as f:
            data = json.load(f)
        
        assert not any(t["name"] == "to-delete" for t in data["templates"])
    
    def test_cannot_delete_builtin(self, manager: TemplateManager):
        """Test cannot delete built-in templates."""
        with pytest.raises(ValueError, match="Cannot delete builtin"):
            manager.delete_template("code-review")
    
    def test_delete_nonexistent(self, manager: TemplateManager):
        """Test deleting non-existent template."""
        result = manager.delete_template("nonexistent")
        assert result is False
    
    def test_get_categories(self, manager: TemplateManager):
        """Test getting list of categories."""
        categories = manager.get_categories()
        
        # Should include all built-in categories
        assert "review" in categories
        assert "testing" in categories
        assert "debugging" in categories
        assert "optimization" in categories
        assert "refactoring" in categories
        assert "documentation" in categories
        assert "design" in categories
        
        # Should be sorted
        assert categories == sorted(categories)
    
    def test_persistence(self, temp_dir: Path):
        """Test templates persist across manager instances."""
        # Create manager and add template
        manager1 = TemplateManager(temp_dir)
        manager1.add_template(Template(
            name="persistent",
            content="test {{var}}",
            description="Test persistence"
        ))
        
        # Create new manager instance
        manager2 = TemplateManager(temp_dir)
        
        # Should load the saved template
        tmpl = manager2.get_template("persistent")
        assert tmpl is not None
        assert tmpl.name == "persistent"
        assert tmpl.content == "test {{var}}"
    
    def test_update_template(self, manager: TemplateManager):
        """Test updating an existing user template."""
        # Add initial template
        manager.add_template(Template(
            name="update-test",
            content="Original {{var}}",
            description="Original"
        ))
        
        # Update it
        manager.add_template(Template(
            name="update-test",
            content="Updated {{var}}",
            description="Updated"
        ))
        
        # Should be updated
        tmpl = manager.get_template("update-test")
        assert tmpl.content == "Updated {{var}}"
        assert tmpl.description == "Updated"
    
    def test_multiple_categories(self, manager: TemplateManager):
        """Test templates with different categories."""
        manager.add_template(Template(
            name="cat1",
            content="test",
            category="category1"
        ))
        manager.add_template(Template(
            name="cat2",
            content="test",
            category="category2"
        ))
        
        # Filter by each category
        cat1_templates = manager.list_templates(category="category1")
        cat2_templates = manager.list_templates(category="category2")
        
        assert len(cat1_templates) == 1
        assert len(cat2_templates) == 1
        assert cat1_templates[0].name == "cat1"
        assert cat2_templates[0].name == "cat2"
    
    def test_template_with_no_variables(self, manager: TemplateManager):
        """Test template with no variables."""
        tmpl = Template(
            name="no-vars",
            content="Static content with no variables"
        )
        
        assert tmpl.variables == []
        result = tmpl.render()
        assert result == "Static content with no variables"
