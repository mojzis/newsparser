"""Tests for report generator."""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from src.models.report import ArchiveLink, HomepageData, ReportArticle, ReportDay
from src.reports.generator import ReportGenerator


class TestReportGenerator:
    @pytest.fixture
    def generator(self):
        """Create generator with temp output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ReportGenerator(output_dir=Path(temp_dir))
    
    @pytest.fixture
    def sample_articles(self):
        """Create sample articles for testing."""
        return [
            ReportArticle(
                url="https://example.com/article1",
                title="Test Article 1",
                perex="A witty summary of the first article",
                bluesky_url="https://bsky.app/profile/user1/post/1",
                author="user1.bsky.social",
                timestamp="1:00 PM",
                relevance_score=0.9,
                domain="example.com",
                content_type="article",
                language="en"
            ),
            ReportArticle(
                url="https://example.com/article2",
                title="Test Article 2",
                perex="Another witty summary",
                bluesky_url="https://bsky.app/profile/user2/post/2",
                author="user2.bsky.social",
                timestamp="2:00 PM",
                relevance_score=0.8,
                domain="example.com",
                content_type="blog post",
                language="en"
            )
        ]
    
    def test_generate_daily_report(self, generator, sample_articles):
        """Test generating daily report."""
        report_day = ReportDay.create(
            report_date=date(2024, 12, 6),
            articles=sample_articles
        )
        
        report_path = generator.generate_daily_report(report_day)
        
        # Check file was created
        assert report_path.exists()
        assert report_path.name == "report.html"
        assert "2024-12-06" in str(report_path)
        
        # Check content contains expected elements
        content = report_path.read_text()
        assert "MCP Monitor" in content
        assert "December 6, 2024" in content
        assert "Test Article 1" in content
        assert "A witty summary of the first article" in content
        assert "user1.bsky.social" in content
    
    def test_generate_homepage(self, generator, sample_articles):
        """Test generating homepage."""
        archive_links = [
            ArchiveLink.create(date(2024, 12, 5), 10),
            ArchiveLink.create(date(2024, 12, 4), 8)
        ]
        
        homepage_data = HomepageData.create(
            today_articles=sample_articles,
            archive_dates=archive_links
        )
        
        homepage_path = generator.generate_homepage(homepage_data)
        
        # Check file was created
        assert homepage_path.exists()
        assert homepage_path.name == "index.html"
        
        # Check content contains expected elements
        content = homepage_path.read_text()
        assert "MCP Monitor" in content
        assert "Daily digest of Model Context Protocol" in content
        assert "Test Article 1" in content
        assert "Previous Days" in content
    
    def test_preview_template(self, generator):
        """Test template preview functionality."""
        context = {
            "date_formatted": "December 6, 2024",
            "articles": []
        }
        
        html = generator.preview_template("daily", context)
        
        assert "MCP Monitor" in html
        assert "December 6, 2024" in html
        assert "No MCP-related resources found" in html
    
    def test_empty_articles(self, generator):
        """Test report generation with no articles."""
        report_day = ReportDay.create(
            report_date=date(2024, 12, 6),
            articles=[]
        )
        
        report_path = generator.generate_daily_report(report_day)
        content = report_path.read_text()
        
        assert "No MCP-related resources found" in content