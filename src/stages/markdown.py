"""Utilities for working with Markdown files with frontmatter."""

import yaml
from pathlib import Path
from typing import Any, Dict, Tuple
from datetime import datetime


class MarkdownFile:
    """Represents a Markdown file with YAML frontmatter."""
    
    def __init__(self, frontmatter: Dict[str, Any], content: str):
        self.frontmatter = frontmatter
        self.content = content
    
    @classmethod
    def load(cls, file_path: Path) -> "MarkdownFile":
        """Load a Markdown file with frontmatter."""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return cls.from_string(text)
    
    @classmethod
    def from_string(cls, text: str) -> "MarkdownFile":
        """Parse a Markdown string with frontmatter."""
        frontmatter, content = parse_frontmatter(text)
        return cls(frontmatter, content)
    
    def save(self, file_path: Path) -> None:
        """Save the Markdown file with frontmatter."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_string())
    
    def to_string(self) -> str:
        """Convert to string format with frontmatter."""
        yaml_str = yaml.dump(self.frontmatter, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_str}---\n\n{self.content}"
    
    def update_frontmatter(self, updates: Dict[str, Any]) -> None:
        """Update frontmatter with new values."""
        self.frontmatter.update(updates)
    
    def get_frontmatter_value(self, key: str, default: Any = None) -> Any:
        """Get a value from frontmatter."""
        return self.frontmatter.get(key, default)
    
    def set_stage(self, stage_name: str) -> None:
        """Set the current stage in frontmatter."""
        self.frontmatter['stage'] = stage_name
        self.frontmatter['updated_at'] = datetime.utcnow().isoformat() + 'Z'


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown text.
    
    Returns:
        Tuple of (frontmatter_dict, content)
    """
    if not text.startswith('---'):
        return {}, text
    
    try:
        # Find the end of frontmatter
        parts = text.split('---', 2)
        if len(parts) < 3:
            return {}, text
        
        # Parse YAML frontmatter
        yaml_content = parts[1].strip()
        frontmatter = yaml.safe_load(yaml_content) or {}
        
        # Get the content (remove leading newlines)
        content = parts[2].lstrip('\n')
        
        return frontmatter, content
        
    except yaml.YAMLError:
        # If YAML parsing fails, treat as regular markdown
        return {}, text


def create_markdown_file(frontmatter: Dict[str, Any], content: str) -> MarkdownFile:
    """Create a new MarkdownFile with the given frontmatter and content."""
    return MarkdownFile(frontmatter, content)


def generate_file_id(base_string: str, length: int = 8) -> str:
    """Generate a short hash-based ID from a string."""
    import hashlib
    
    hash_obj = hashlib.sha256(base_string.encode('utf-8'))
    return hash_obj.hexdigest()[:length]


def safe_filename(name: str, max_length: int = 50) -> str:
    """Convert a string to a safe filename."""
    import re
    
    # Replace problematic characters
    safe = re.sub(r'[^\w\-_.]', '_', name)
    
    # Remove multiple underscores
    safe = re.sub(r'_+', '_', safe)
    
    # Trim length
    if len(safe) > max_length:
        safe = safe[:max_length].rstrip('_')
    
    return safe