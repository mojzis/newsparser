"""Tests for query builders."""
import pytest

from src.bluesky.query_builders import (
    LuceneQueryBuilder,
    NativeQueryBuilder,
    QueryBuilder,
    QueryBuilderFactory,
)
from src.config.searches import SearchDefinition


class TestNativeQueryBuilder:
    def test_simple_include_terms(self):
        """Test building query with simple include terms."""
        builder = NativeQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["#mcp", "tools"],
        )
        
        query = builder.build_query(search_def)
        assert query == "#mcp tools"
    
    def test_hashtag_exclusions(self):
        """Test building query with hashtag exclusions."""
        builder = NativeQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["#mcp"],
            exclude_terms=["#marvel", "#minipainting"],
        )
        
        query = builder.build_query(search_def)
        assert query == "#mcp -#marvel -#minipainting"
    
    def test_keyword_exclusions(self):
        """Test building query with keyword exclusions."""
        builder = NativeQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["mcp"],
            exclude_terms=["minecraft", "medical"],
        )
        
        query = builder.build_query(search_def)
        assert query == 'mcp -"minecraft" -"medical"'
    
    def test_mixed_inclusions_exclusions(self):
        """Test building query with mixed terms."""
        builder = NativeQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["#mcp", "protocol"],
            exclude_terms=["#marvel", "minecraft"],
        )
        
        query = builder.build_query(search_def)
        assert query == '#mcp protocol -#marvel -"minecraft"'
    
    def test_complex_exclude_term_skipped(self):
        """Test that complex boolean expressions are skipped."""
        builder = NativeQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["#mcp"],
            exclude_terms=["#mcp AND (medical OR healthcare)"],
        )
        
        query = builder.build_query(search_def)
        # Complex term should be skipped
        assert query == "#mcp"
    
    def test_empty_exclude_terms(self):
        """Test building query with no exclude terms."""
        builder = NativeQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["#mcp", "tools"],
            exclude_terms=[],
        )
        
        query = builder.build_query(search_def)
        assert query == "#mcp tools"
    
    def test_validate_valid_query(self):
        """Test validating a valid query."""
        builder = NativeQueryBuilder()
        
        valid_queries = [
            "#mcp",
            "#mcp -#marvel",
            'mcp tools -"minecraft"',
            "#mcp #tools -#marvel -#minipainting",
        ]
        
        for query in valid_queries:
            is_valid, error = builder.validate_query(query)
            assert is_valid is True
            assert error == ""
    
    def test_validate_invalid_query(self):
        """Test validating invalid queries."""
        builder = NativeQueryBuilder()
        
        # Empty query
        is_valid, error = builder.validate_query("")
        assert is_valid is False
        assert "empty" in error.lower()
        
        # Unmatched quotes
        is_valid, error = builder.validate_query('#mcp -"unmatched')
        assert is_valid is False
        assert "quotes" in error.lower()


class TestLuceneQueryBuilder:
    def test_simple_include_terms(self):
        """Test building Lucene query with simple include terms."""
        builder = LuceneQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["mcp", "tools"],
        )
        
        query = builder.build_query(search_def)
        assert query == "(mcp OR tools)"
    
    def test_exclude_terms(self):
        """Test building Lucene query with exclude terms."""
        builder = LuceneQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["mcp"],
            exclude_terms=["minecraft", "medical"],
        )
        
        query = builder.build_query(search_def)
        assert query == "((mcp)) AND (NOT minecraft AND NOT medical)"
    
    def test_hashtag_preservation(self):
        """Test that hashtags are preserved in Lucene queries."""
        builder = LuceneQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["#mcp"],
            exclude_terms=["#marvel"],
        )
        
        query = builder.build_query(search_def)
        assert query == "((#mcp)) AND (NOT (#marvel))"
    
    def test_complex_expressions(self):
        """Test building with complex boolean expressions."""
        builder = LuceneQueryBuilder()
        search_def = SearchDefinition(
            name="Test",
            description="Test search",
            include_terms=["mcp"],
            exclude_terms=["#mcp AND (medical OR healthcare)"],
        )
        
        query = builder.build_query(search_def)
        assert "NOT (#mcp AND (medical OR healthcare))" in query
    
    def test_validate_valid_query(self):
        """Test validating valid Lucene queries."""
        builder = LuceneQueryBuilder()
        
        valid_queries = [
            "(mcp)",
            "(mcp OR tools)",
            "((mcp)) AND (NOT minecraft)",
            "(#mcp) AND (NOT (#marvel OR #minipainting))",
        ]
        
        for query in valid_queries:
            is_valid, error = builder.validate_query(query)
            assert is_valid is True
            assert error == ""
    
    def test_validate_invalid_query(self):
        """Test validating invalid Lucene queries."""
        builder = LuceneQueryBuilder()
        
        # Unbalanced parentheses
        is_valid, error = builder.validate_query("(mcp")
        assert is_valid is False
        assert "parentheses" in error.lower()
        
        # Empty groups
        is_valid, error = builder.validate_query("() AND mcp")
        assert is_valid is False
        assert "empty" in error.lower()


class TestQueryBuilderFactory:
    def test_create_native_builder(self):
        """Test creating native query builder."""
        builder = QueryBuilderFactory.create("native")
        assert isinstance(builder, NativeQueryBuilder)
    
    def test_create_lucene_builder(self):
        """Test creating Lucene query builder."""
        builder = QueryBuilderFactory.create("lucene")
        assert isinstance(builder, LuceneQueryBuilder)
    
    def test_default_is_native(self):
        """Test that default is native builder."""
        builder = QueryBuilderFactory.create()
        assert isinstance(builder, NativeQueryBuilder)
    
    def test_invalid_syntax_type(self):
        """Test error on invalid syntax type."""
        with pytest.raises(ValueError, match="Unknown query syntax"):
            QueryBuilderFactory.create("invalid")
    
    def test_available_syntaxes(self):
        """Test getting available syntax types."""
        syntaxes = QueryBuilderFactory.available_syntaxes()
        assert "native" in syntaxes
        assert "lucene" in syntaxes
        assert len(syntaxes) == 2