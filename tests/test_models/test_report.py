"""Tests for report models."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.models.report import ArchiveLink, HomepageData, ReportArticle, ReportDay


class TestReportArticle:
    def test_create_from_post_and_evaluation(self):
        """Test creating ReportArticle from post and evaluation data."""
        evaluation = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "perex": "A witty summary of the article",
            "summary": "A regular summary",
            "relevance_score": 0.85,
            "domain": "example.com"
        }
        
        article = ReportArticle.from_post_and_evaluation(
            post_id="abc123",
            author="user.bsky.social",
            created_at=datetime(2024, 12, 6, 15, 45),
            evaluation=evaluation
        )
        
        assert str(article.url) == "https://example.com/article"
        assert article.title == "Test Article"
        assert article.perex == "A witty summary of the article"
        assert str(article.bluesky_url) == "https://bsky.app/profile/user.bsky.social/post/abc123"
        assert article.author == "user.bsky.social"
        assert article.timestamp == "3:45 PM"
        assert article.relevance_score == 0.85
        assert article.domain == "example.com"
    
    def test_fallback_to_summary_when_no_perex(self):
        """Test falling back to summary when perex is not available."""
        evaluation = {
            "url": "https://example.com/article",
            "summary": "A regular summary",
            "relevance_score": 0.85,
            "domain": "example.com"
        }
        
        article = ReportArticle.from_post_and_evaluation(
            post_id="abc123",
            author="user.bsky.social",
            created_at=datetime(2024, 12, 6, 9, 30),
            evaluation=evaluation
        )
        
        assert article.perex == "A regular summary"
        assert article.title == "Untitled"
        assert article.timestamp == "9:30 AM"
    
    def test_create_from_at_protocol_uri(self):
        """Test creating ReportArticle with AT protocol URI."""
        evaluation = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "perex": "A witty summary",
            "relevance_score": 0.85,
            "domain": "example.com"
        }
        
        article = ReportArticle.from_post_and_evaluation(
            post_id="at://did:plc:cnkcdjrvp5b27gqmdsbpbn5o/app.bsky.feed.post/3lrivlab6qc2x",
            author="james.montemagno.com",
            created_at=datetime(2024, 12, 6, 15, 45),
            evaluation=evaluation
        )
        
        # Should extract just the post ID from the AT protocol URI
        assert str(article.bluesky_url) == "https://bsky.app/profile/james.montemagno.com/post/3lrivlab6qc2x"
    
    def test_validation(self):
        """Test ReportArticle validation."""
        # Valid article
        article = ReportArticle(
            url="https://example.com/article",
            title="Test",
            perex="Summary",
            bluesky_url="https://bsky.app/profile/user/post/123",
            author="user",
            timestamp="3:45 PM",
            relevance_score=0.5,
            domain="example.com"
        )
        assert article.relevance_score == 0.5
        
        # Invalid relevance score
        with pytest.raises(ValidationError):
            ReportArticle(
                url="https://example.com/article",
                title="Test",
                perex="Summary",
                bluesky_url="https://bsky.app/profile/user/post/123",
                author="user",
                timestamp="3:45 PM",
                relevance_score=1.5,  # Out of range
                domain="example.com"
            )


class TestReportDay:
    def test_create_report_day(self):
        """Test creating ReportDay with formatted date."""
        articles = [
            ReportArticle(
                url="https://example.com/1",
                title="Article 1",
                perex="Summary 1",
                bluesky_url="https://bsky.app/profile/user/post/1",
                author="user1",
                timestamp="1:00 PM",
                relevance_score=0.9,
                domain="example.com"
            ),
            ReportArticle(
                url="https://example.com/2",
                title="Article 2",
                perex="Summary 2",
                bluesky_url="https://bsky.app/profile/user/post/2",
                author="user2",
                timestamp="2:00 PM",
                relevance_score=0.8,
                domain="example.com"
            )
        ]
        
        report_day = ReportDay.create(
            report_date=date(2024, 12, 6),
            articles=articles
        )
        
        assert report_day.date == date(2024, 12, 6)
        assert report_day.date_formatted == "December 6, 2024"
        assert len(report_day.articles) == 2
        assert report_day.article_count == 2
    
    def test_empty_articles(self):
        """Test ReportDay with no articles."""
        report_day = ReportDay.create(
            report_date=date(2024, 12, 6),
            articles=[]
        )
        
        assert report_day.article_count == 0
        assert report_day.articles == []


class TestArchiveLink:
    def test_create_current_year(self):
        """Test creating archive link for current year."""
        # For this test, assume we're testing with 2024 dates
        link = ArchiveLink.create(
            report_date=date(2024, 12, 6),
            article_count=5
        )
        
        # The formatting will depend on current year, but path should be consistent
        assert link.path == "reports/2024/12/06/report.html"
        assert link.article_count == 5
    
    def test_create_previous_year(self):
        """Test creating archive link for previous year."""
        link = ArchiveLink.create(
            report_date=date(2023, 12, 6),
            article_count=3
        )
        
        assert link.formatted == "December 6, 2023"  # Include year
        assert link.path == "reports/2023/12/06/report.html"
        assert link.article_count == 3


class TestHomepageData:
    def test_create_homepage_data(self):
        """Test creating homepage data."""
        articles = [
            ReportArticle(
                url="https://example.com/1",
                title="Today's Article",
                perex="Summary",
                bluesky_url="https://bsky.app/profile/user/post/1",
                author="user1",
                timestamp="1:00 PM",
                relevance_score=0.9,
                domain="example.com"
            )
        ]
        
        archive_dates = [
            ArchiveLink.create(date(2024, 12, 5), 10),
            ArchiveLink.create(date(2024, 12, 4), 8)
        ]
        
        homepage = HomepageData.create(
            today_articles=articles,
            archive_dates=archive_dates
        )
        
        assert homepage.today  # Should be formatted date string
        assert len(homepage.today_articles) == 1
        assert len(homepage.archive_dates) == 2
        assert homepage.archive_dates[0].article_count == 10