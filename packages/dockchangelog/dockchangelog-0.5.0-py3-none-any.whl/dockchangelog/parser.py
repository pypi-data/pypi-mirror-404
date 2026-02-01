"""
Parse and format release notes for display.
"""

import re
from typing import Dict, List, Optional


class ParsedNotes:
    """Structured release notes."""
    
    def __init__(self):
        self.features: List[str] = []
        self.fixes: List[str] = []
        self.breaking: List[str] = []
        self.security: List[str] = []
        self.dependencies: List[str] = []
        self.other: List[str] = []
    
    def is_empty(self) -> bool:
        """Check if no notes were parsed."""
        return not any([
            self.features, self.fixes, self.breaking,
            self.security, self.dependencies, self.other
        ])


class ReleaseNotesParser:
    """Parse release notes into structured format."""
    
    def __init__(self, max_items_per_section: int = 5):
        """
        Initialize parser.
        
        Args:
            max_items_per_section: Maximum items to show per section
        """
        self.max_items = max_items_per_section
    
    def parse(self, markdown: str) -> ParsedNotes:
        """
        Parse markdown release notes.
        
        Args:
            markdown: Release notes in markdown format
        
        Returns:
            ParsedNotes object with categorized items
        """
        notes = ParsedNotes()
        
        if not markdown:
            return notes
        
        # Try structured parsing first
        if self._parse_structured(markdown, notes):
            return notes
        
        # Fall back to heuristic parsing
        self._parse_heuristic(markdown, notes)
        
        return notes
    
    def _parse_structured(self, text: str, notes: ParsedNotes) -> bool:
        """
        Parse structured release notes with headings.
        
        Returns True if structure was found.
        """
        found_structure = False
        current_section = None
        
        for line in text.split("\n"):
            line = line.strip()
            
            # Check for section headings
            heading = self._detect_section_heading(line)
            if heading:
                current_section = heading
                found_structure = True
                continue
            
            # Extract list items
            if current_section and (line.startswith("-") or line.startswith("*")):
                item = line[1:].strip()
                if item:
                    self._add_to_section(notes, current_section, item)
        
        return found_structure
    
    def _detect_section_heading(self, line: str) -> Optional[str]:
        """
        Detect which section a heading belongs to.
        
        Returns section name or None.
        """
        # Must start with # or ** to be a heading
        if not (line.startswith("#") or line.startswith("**")):
            return None
        
        line_lower = line.lower()
        
        # Remove markdown heading markers
        clean_line = re.sub(r"^#+\s*", "", line_lower)
        clean_line = re.sub(r"^[\*_]+\s*", "", clean_line)
        clean_line = re.sub(r"[\*_:]+\s*$", "", clean_line)
        
        # Check for feature keywords
        if any(word in clean_line for word in ["feature", "added", "new", "✨"]):
            return "features"
        
        # Check for fix keywords
        if any(word in clean_line for word in ["fix", "bug", "resolved", "🐛"]):
            return "fixes"
        
        # Check for breaking keywords
        if any(word in clean_line for word in ["breaking", "⚠️", "migration"]):
            return "breaking"
        
        # Check for security keywords
        if any(word in clean_line for word in ["security", "🔒", "vulnerabilit"]):
            return "security"
        
        # Check for dependency keywords
        if any(word in clean_line for word in ["dependen", "updated", "upgraded", "📦"]):
            return "dependencies"
        
        return None
    
    def _parse_heuristic(self, text: str, notes: ParsedNotes):
        """Parse using heuristics when no clear structure."""
        for line in text.split("\n"):
            line = line.strip()
            
            # Look for list items
            if line.startswith("-") or line.startswith("*"):
                item = line[1:].strip()
                if item:
                    # Categorize by keywords in the item
                    section = self._categorize_item(item)
                    self._add_to_section(notes, section, item)
    
    def _categorize_item(self, item: str) -> str:
        """Categorize an item based on its content."""
        item_lower = item.lower()
        
        # Check for breaking changes
        if any(word in item_lower for word in ["breaking", "removed", "deprecated"]):
            return "breaking"
        
        # Check for security
        if any(word in item_lower for word in ["security", "cve", "vulnerability"]):
            return "security"
        
        # Check for features
        if any(word in item_lower for word in ["add", "new", "feature", "implement"]):
            return "features"
        
        # Check for fixes
        if any(word in item_lower for word in ["fix", "bug", "resolve", "patch"]):
            return "fixes"
        
        # Check for dependencies
        if any(word in item_lower for word in ["update", "upgrade", "bump", "dependency"]):
            return "dependencies"
        
        # Default to other
        return "other"
    
    def _add_to_section(self, notes: ParsedNotes, section: str, item: str):
        """Add item to appropriate section."""
        # Limit section size
        section_map = {
            "features": notes.features,
            "fixes": notes.fixes,
            "breaking": notes.breaking,
            "security": notes.security,
            "dependencies": notes.dependencies,
            "other": notes.other,
        }
        
        if section in section_map:
            items = section_map[section]
            if len(items) < self.max_items:
                items.append(item)
