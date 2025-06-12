"""Query builders for different search syntax types."""
import re
from abc import ABC, abstractmethod
from typing import Any

from src.config.searches import SearchDefinition
from src.utils.logging import get_logger

logger = get_logger(__name__)


class QueryBuilder(ABC):
    """Abstract base class for query builders."""
    
    @abstractmethod
    def build_query(self, search_definition: SearchDefinition) -> str:
        """Build a query string from a search definition."""
        pass
    
    @abstractmethod
    def validate_query(self, query: str) -> tuple[bool, str]:
        """Validate a query string. Returns (is_valid, error_message)."""
        pass


class NativeQueryBuilder(QueryBuilder):
    """
    Bluesky native search syntax query builder.
    
    Uses simple space-separated terms with:
    - Hashtags as-is: #mcp
    - Exclude hashtags with minus: -#marvel
    - Regular keywords without special syntax: mcp tools
    - Quoted phrases for non-hashtag exclusions: -"minecraft"
    """
    
    def build_query(self, search_definition: SearchDefinition) -> str:
        """Build a native Bluesky search query."""
        parts = []
        
        # Add include terms as-is
        for term in search_definition.include_terms:
            parts.append(term)
        
        # Add exclude terms with appropriate prefix
        for term in search_definition.exclude_terms:
            # Check for complex boolean expressions first
            if any(op in term for op in [" AND ", " OR ", " NOT "]):
                # Complex term or phrase - needs special handling
                # For native syntax, we can't easily express complex boolean logic
                # So we'll skip these or treat them as simple excludes
                logger.warning(f"Complex exclude term not supported in native syntax: {term}")
                # Skip complex boolean expressions in native mode
                continue
            elif term.startswith("#"):
                # Simple hashtag exclusion: -#tag
                parts.append(f"-{term}")
            elif " " in term:
                # Multi-word phrase exclusion
                parts.append(f'-"{term}"')
            else:
                # Simple keyword exclusion: -"keyword"
                # Quote to ensure it's treated as a single exclude term
                parts.append(f'-"{term}"')
        
        query = " ".join(parts)
        logger.debug(f"Built native query: {query}")
        return query
    
    def validate_query(self, query: str) -> tuple[bool, str]:
        """Validate native query syntax."""
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        # Basic validation - native syntax is quite permissive
        # Just check for some obviously invalid patterns
        if query.count('"') % 2 != 0:
            return False, "Unmatched quotes in query"
        
        # Check for invalid characters
        invalid_chars = ['\\', '\n', '\r', '\t']
        for char in invalid_chars:
            if char in query:
                return False, f"Invalid character in query: {repr(char)}"
        
        return True, ""


class LuceneQueryBuilder(QueryBuilder):
    """
    Lucene-style query builder (original implementation).
    
    Supports:
    - Boolean operators: AND, OR, NOT
    - Grouping with parentheses
    - Special character escaping
    """
    
    SPECIAL_CHARS = r'+-&|!(){}[]^"~*?:\/'
    
    @classmethod
    def escape_special_chars(cls, term: str) -> str:
        """Escape Lucene special characters in a search term."""
        escaped = term
        for char in cls.SPECIAL_CHARS:
            escaped = escaped.replace(char, f"\\{char}")
        return escaped
    
    @classmethod
    def build_include_query(cls, include_terms: list[str]) -> str:
        """Build the include portion of the query."""
        if not include_terms:
            return ""
        
        escaped_terms = []
        for term in include_terms:
            # Keep hashtags and complex expressions as-is
            if term.startswith("#") or "AND" in term or "OR" in term:
                escaped_terms.append(term)
            else:
                escaped_terms.append(cls.escape_special_chars(term))
        
        # Join with OR for include terms
        return "(" + " OR ".join(escaped_terms) + ")"
    
    @classmethod
    def build_exclude_query(cls, exclude_terms: list[str]) -> str:
        """Build the exclude portion of the query."""
        if not exclude_terms:
            return ""
        
        escaped_terms = []
        for term in exclude_terms:
            # Keep hashtags and complex expressions as-is
            if term.startswith("#") or "AND" in term or "OR" in term:
                escaped_terms.append(f"NOT ({term})")
            else:
                escaped_terms.append(f"NOT {cls.escape_special_chars(term)}")
        
        # Join with AND for exclude terms
        return " AND ".join(escaped_terms)
    
    def build_query(self, search_definition: SearchDefinition) -> str:
        """Build a Lucene-style query."""
        include_query = self.build_include_query(search_definition.include_terms)
        exclude_query = self.build_exclude_query(search_definition.exclude_terms)
        
        if exclude_query:
            full_query = f"({include_query}) AND ({exclude_query})"
        else:
            full_query = include_query
        
        logger.debug(f"Built Lucene query: {full_query}")
        return full_query
    
    def validate_query(self, query: str) -> tuple[bool, str]:
        """Validate Lucene query syntax."""
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        # Check for balanced parentheses
        if query.count("(") != query.count(")"):
            return False, "Unbalanced parentheses in query"
        
        # Check for empty groups
        if "()" in query:
            return False, "Empty parentheses group in query"
        
        # Check for invalid operator usage
        invalid_patterns = [
            r"\bAND\s+AND\b",
            r"\bOR\s+OR\b", 
            r"\bNOT\s+NOT\b",
            r"^\s*AND\b",
            r"^\s*OR\b",
            r"\bAND\s*$",
            r"\bOR\s*$",
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, query):
                return False, f"Invalid operator usage in query"
        
        return True, ""


class QueryBuilderFactory:
    """Factory for creating query builders based on syntax type."""
    
    _builders = {
        "native": NativeQueryBuilder,
        "lucene": LuceneQueryBuilder,
    }
    
    @classmethod
    def create(cls, syntax_type: str = "native") -> QueryBuilder:
        """
        Create a query builder for the specified syntax type.
        
        Args:
            syntax_type: Type of syntax ("native" or "lucene")
            
        Returns:
            QueryBuilder instance
            
        Raises:
            ValueError: If syntax_type is not recognized
        """
        if syntax_type not in cls._builders:
            raise ValueError(
                f"Unknown query syntax: {syntax_type}. "
                f"Available options: {list(cls._builders.keys())}"
            )
        
        return cls._builders[syntax_type]()
    
    @classmethod
    def available_syntaxes(cls) -> list[str]:
        """Get list of available syntax types."""
        return list(cls._builders.keys())