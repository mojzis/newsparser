import re
from typing import Any

from src.config.searches import SearchDefinition
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LuceneQueryBuilder:
    """Builds Lucene queries from search definitions."""
    
    @staticmethod
    def escape_special_chars(term: str) -> str:
        """
        Escape special Lucene characters in search terms.
        
        Special characters: + - = && || > < ! ( ) { } [ ] ^ " ~ * ? : \ /
        """
        # Characters that need escaping in Lucene
        special_chars = ['+', '-', '=', '&&', '||', '>', '<', '!', '(', ')', 
                        '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '\\', '/']
        
        escaped_term = term
        for char in special_chars:
            if char in ['&&', '||']:
                # These are operators, handle them specially
                continue
            escaped_term = escaped_term.replace(char, f'\\{char}')
        
        return escaped_term
    
    @staticmethod
    def is_complex_query(term: str) -> bool:
        """
        Check if a term contains Lucene operators and should not be escaped.
        
        Complex queries contain operators like AND, OR, NOT, parentheses, etc.
        """
        # Look for Lucene operators and syntax
        operators = ['AND', 'OR', 'NOT', '&&', '||']
        has_operators = any(op in term.upper() for op in operators)
        has_parens = '(' in term and ')' in term
        has_quotes = '"' in term
        
        return has_operators or has_parens or has_quotes
    
    @classmethod
    def build_include_query(cls, include_terms: list[str]) -> str:
        """
        Build the include portion of the query.
        
        Args:
            include_terms: List of terms that must be present
            
        Returns:
            Lucene query string for include terms
        """
        if not include_terms:
            return ""
        
        processed_terms = []
        
        for term in include_terms:
            term = term.strip()
            if not term:
                continue
                
            if cls.is_complex_query(term):
                # Complex query with operators, use as-is but wrap in parentheses
                processed_terms.append(f"({term})")
            else:
                # Simple term, escape special characters and quote if contains spaces
                escaped_term = cls.escape_special_chars(term)
                if ' ' in escaped_term:
                    processed_terms.append(f'"{escaped_term}"')
                else:
                    processed_terms.append(escaped_term)
        
        if len(processed_terms) == 1:
            return processed_terms[0]
        else:
            # Multiple terms, combine with OR
            return f"({' OR '.join(processed_terms)})"
    
    @classmethod
    def build_exclude_query(cls, exclude_terms: list[str]) -> str:
        """
        Build the exclude portion of the query.
        
        Args:
            exclude_terms: List of terms to exclude
            
        Returns:
            Lucene query string for exclude terms
        """
        if not exclude_terms:
            return ""
        
        processed_terms = []
        
        for term in exclude_terms:
            term = term.strip()
            if not term:
                continue
                
            if cls.is_complex_query(term):
                # Complex query with operators, wrap in parentheses and negate
                processed_terms.append(f"NOT ({term})")
            else:
                # Simple term, escape and quote if needed, then negate
                escaped_term = cls.escape_special_chars(term)
                if ' ' in escaped_term:
                    processed_terms.append(f'NOT "{escaped_term}"')
                else:
                    processed_terms.append(f"NOT {escaped_term}")
        
        return ' AND '.join(processed_terms)
    
    @classmethod
    def build_query(cls, search_definition: SearchDefinition) -> str:
        """
        Build a complete Lucene query from a search definition.
        
        Args:
            search_definition: SearchDefinition to convert to query
            
        Returns:
            Complete Lucene query string
        """
        include_query = cls.build_include_query(search_definition.include_terms)
        exclude_query = cls.build_exclude_query(search_definition.exclude_terms)
        
        if not include_query:
            raise ValueError("Cannot build query without include terms")
        
        if exclude_query:
            # Combine include and exclude with AND
            full_query = f"({include_query}) AND ({exclude_query})"
        else:
            full_query = include_query
        
        logger.debug(f"Built query for '{search_definition.name}': {full_query}")
        return full_query
    
    @classmethod
    def validate_query(cls, query: str) -> tuple[bool, str]:
        """
        Validate a Lucene query for basic syntax errors.
        
        Args:
            query: Query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check for balanced parentheses
            if query.count('(') != query.count(')'):
                return False, "Unbalanced parentheses in query"
            
            # Check for balanced quotes
            if query.count('"') % 2 != 0:
                return False, "Unmatched quotes in query"
            
            # Check for empty parentheses
            if '()' in query:
                return False, "Empty parentheses not allowed"
            
            # Check for invalid operator sequences
            invalid_sequences = ['AND AND', 'OR OR', 'NOT NOT']
            for seq in invalid_sequences:
                if seq in query.upper():
                    return False, f"Invalid operator sequence: {seq}"
            
            # Check for operators at the beginning/end
            query_stripped = query.strip()
            if query_stripped.upper().startswith(('AND ', 'OR ')):
                return False, "Query cannot start with AND/OR operator"
            
            if query_stripped.upper().endswith((' AND', ' OR')):
                return False, "Query cannot end with AND/OR operator"
            
            return True, ""
            
        except Exception as e:
            return False, f"Query validation error: {e}"
    
    @classmethod
    def build_and_validate(cls, search_definition: SearchDefinition) -> str:
        """
        Build and validate a query from search definition.
        
        Args:
            search_definition: SearchDefinition to convert
            
        Returns:
            Validated Lucene query string
            
        Raises:
            ValueError: If query building or validation fails
        """
        try:
            query = cls.build_query(search_definition)
            is_valid, error_msg = cls.validate_query(query)
            
            if not is_valid:
                raise ValueError(f"Invalid query generated: {error_msg}")
            
            return query
            
        except Exception as e:
            logger.error(f"Failed to build query for '{search_definition.name}': {e}")
            raise ValueError(f"Query building failed: {e}") from e