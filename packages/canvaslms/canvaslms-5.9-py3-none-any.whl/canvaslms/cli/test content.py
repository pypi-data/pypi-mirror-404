"""Tests for content editing and rendering utilities."""

import pytest
import tempfile
import os

import canvaslms.cli.content as content


class TestParseYamlFrontMatter:
    """Tests for parse_yaml_front_matter function."""

    def test_empty_content_returns_empty_dict(self):
        """Empty content returns empty attributes."""
        attrs, result = content.parse_yaml_front_matter("")
        assert attrs == {}
        assert result == ""

    def test_no_frontmatter_returns_content_unchanged(self):
        """Content without front matter passes through unchanged."""
        original = "Just some content\nwith multiple lines"
        attrs, result = content.parse_yaml_front_matter(original)
        assert attrs == {}
        assert result == original

    def test_valid_frontmatter_parsed_correctly(self):
        """Valid YAML front matter is parsed into attributes."""
        text = """---
title: Test Title
published: true
---
Content here"""
        attrs, result = content.parse_yaml_front_matter(text)
        assert attrs == {"title": "Test Title", "published": True}
        assert result == "Content here"

    def test_frontmatter_with_null_values(self):
        """Null values in YAML are preserved."""
        text = """---
title: Test
delayed_post_at: null
---
Content"""
        attrs, _ = content.parse_yaml_front_matter(text)
        assert attrs["delayed_post_at"] is None


class TestFormatYamlFrontMatter:
    """Tests for format_yaml_front_matter function."""

    def test_empty_attributes_returns_content_only(self):
        """Empty attributes dict returns just the content."""
        result = content.format_yaml_front_matter({}, "Content here")
        assert result == "Content here"

    def test_formats_attributes_correctly(self):
        """Attributes are formatted as YAML front matter."""
        attrs = {"title": "Test", "published": True}
        result = content.format_yaml_front_matter(attrs, "Content")
        assert result.startswith("---\n")
        assert "title: Test" in result
        assert result.endswith("---\nContent")


class TestSchemaFunctions:
    """Tests for schema manipulation functions."""

    def test_create_template_with_defaults(self):
        """Template contains all schema attributes with defaults."""
        schema = {
            "title": {"default": "", "required": True, "canvas_attr": "title"},
            "published": {
                "default": True,
                "required": False,
                "canvas_attr": "published",
            },
        }
        template = content.create_schema_template(schema)
        assert template == {"title": "", "published": True}

    def test_extract_attributes_from_object(self):
        """Attributes are extracted from object using canvas_attr mapping."""

        class MockAnnouncement:
            title = "Test Title"
            published = True
            delayed_post_at = None

        schema = {
            "title": {"default": "", "required": True, "canvas_attr": "title"},
            "published": {
                "default": True,
                "required": False,
                "canvas_attr": "published",
            },
            "delayed_post_at": {
                "default": None,
                "required": False,
                "canvas_attr": "delayed_post_at",
            },
        }
        attrs = content.extract_attributes_from_object(MockAnnouncement(), schema)
        assert attrs["title"] == "Test Title"
        assert attrs["published"] is True
        assert attrs["delayed_post_at"] is None

    def test_validate_missing_required_attribute(self):
        """Validation fails when required attribute is missing."""
        schema = {
            "title": {"default": "", "required": True, "canvas_attr": "title"},
        }
        errors = content.validate_attributes({}, schema)
        assert len(errors) == 1
        assert "title" in errors[0]

    def test_validate_empty_required_attribute(self):
        """Validation fails when required attribute is empty string."""
        schema = {
            "title": {"default": "", "required": True, "canvas_attr": "title"},
        }
        errors = content.validate_attributes({"title": ""}, schema)
        assert len(errors) == 1

    def test_validate_passes_with_all_required(self):
        """Validation passes when all required attributes present."""
        schema = {
            "title": {"default": "", "required": True, "canvas_attr": "title"},
            "published": {
                "default": True,
                "required": False,
                "canvas_attr": "published",
            },
        }
        errors = content.validate_attributes({"title": "Test"}, schema)
        assert errors == []


class TestRenderToMarkdown:
    """Tests for render_to_markdown function."""

    def test_renders_object_with_attributes(self):
        """Canvas object is rendered with YAML front matter."""

        class MockAnnouncement:
            title = "Test Announcement"
            published = True
            message = "<p>Hello <strong>world</strong></p>"

        schema = {
            "title": {"default": "", "required": True, "canvas_attr": "title"},
            "published": {
                "default": True,
                "required": False,
                "canvas_attr": "published",
            },
        }
        result = content.render_to_markdown(MockAnnouncement(), schema, "message")
        assert result.startswith("---\n")
        assert "title: Test Announcement" in result
        assert "published: true" in result

    def test_handles_empty_content(self):
        """Empty content attribute produces empty body."""

        class MockAnnouncement:
            title = "Empty"
            published = True
            message = ""

        schema = {
            "title": {"default": "", "required": True, "canvas_attr": "title"},
        }
        result = content.render_to_markdown(MockAnnouncement(), schema, "message")
        assert "title: Empty" in result

    def test_includes_extra_attributes(self):
        """Extra attributes are included in YAML front matter."""

        class MockPage:
            title = "Test Page"
            body = "<p>Content</p>"

        schema = {
            "title": {"default": "", "required": True, "canvas_attr": "title"},
        }
        extra = {"modules": ["Week 1", "Week 2"]}
        result = content.render_to_markdown(
            MockPage(), schema, "body", extra_attributes=extra
        )
        assert "title: Test Page" in result
        assert "modules:" in result
        assert "- Week 1" in result
        assert "- Week 2" in result


class TestReadContentFromFile:
    """Tests for read_content_from_file function."""

    def test_reads_valid_file(self):
        """Valid file with front matter is parsed correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                """---
title: Test File
published: true
---
File content here"""
            )
            f.flush()
            temp_path = f.name

        try:
            attrs, markdown = content.read_content_from_file(temp_path)
            assert attrs["title"] == "Test File"
            assert attrs["published"] is True
            assert "File content here" in markdown
        finally:
            os.unlink(temp_path)

    def test_raises_on_missing_file(self):
        """FileNotFoundError raised for missing file."""
        with pytest.raises(FileNotFoundError):
            content.read_content_from_file("/nonexistent/path/file.md")

    def test_handles_file_without_frontmatter(self):
        """File without front matter returns empty attributes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Just plain content")
            f.flush()
            temp_path = f.name

        try:
            attrs, markdown = content.read_content_from_file(temp_path)
            assert attrs == {}
            assert "Just plain content" in markdown
        finally:
            os.unlink(temp_path)
