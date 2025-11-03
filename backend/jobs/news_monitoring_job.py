"""Background job for monitoring news articles"""

import asyncio
from celery import shared_task
from typing import Dict, Any
from datetime import datetime

from backend.services.news_monitoring_service import get_news_monitoring_service
from backend.database import get_db_session, Evidence, Investigation
from backend.utils.logging import get_logger

logger = get_logger(__name__)


@shared_task(name="monitor_news_articles")
def monitor_news_articles(days: int = 7, limit: int = 50) -> Dict[str, Any]:
    """
    Monitor news articles for tiger trafficking keywords
    
    Args:
        days: Number of days to search back
        limit: Maximum number of articles to process
        
    Returns:
        Monitoring results
    """
    logger.info(f"Starting news monitoring for last {days} days")
    
    # Run async function
    return asyncio.run(_monitor_news_async(days, limit))


async def _monitor_news_async(days: int, limit: int) -> Dict[str, Any]:
    """Async implementation of news monitoring"""
    news_service = get_news_monitoring_service()
    
    try:
        # Search for news articles
        news_results = await news_service.search_news(days=days, limit=limit)
        
        articles = news_results.get("articles", [])
        logger.info(f"Found {len(articles)} news articles")
        
        # Monitor reference facilities
        facility_news = await news_service.monitor_reference_facilities(
            days=days,
            limit_per_facility=5
        )
        
        # Create evidence and investigations for significant findings
        created_evidence = 0
        created_investigations = 0
        
        with get_db_session() as session:
            # Process regular news articles
            for article in articles[:20]:  # Limit processing
                try:
                    # Create evidence record
                    evidence = Evidence(
                        investigation_id=None,  # Will be linked when investigation created
                        source_type="web_search",
                        source_url=article.get("url", ""),
                        content={
                            "title": article.get("title", ""),
                            "snippet": article.get("snippet", ""),
                            "source": article.get("source", ""),
                            "date": article.get("date"),
                            "type": "news_article"
                        },
                        extracted_text=article.get("snippet", ""),
                        relevance_score=0.7
                    )
                    session.add(evidence)
                    created_evidence += 1
                
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
            
            # Process facility-specific news
            facility_news_data = facility_news.get("facility_news", {})
            for facility_name, news_data in facility_news_data.items():
                articles_for_facility = news_data.get("articles", [])
                
                if articles_for_facility:
                    # Higher priority for reference facilities
                    priority = "high"
                    
                    for article in articles_for_facility[:5]:
                        try:
                            evidence = Evidence(
                                investigation_id=None,
                                source_type="web_search",
                                source_url=article.get("url", ""),
                                content={
                                    "title": article.get("title", ""),
                                    "snippet": article.get("snippet", ""),
                                    "source": article.get("source", ""),
                                    "facility_name": facility_name,
                                    "facility_id": news_data.get("facility_id"),
                                    "date": article.get("date"),
                                    "type": "facility_news"
                                },
                                extracted_text=article.get("snippet", ""),
                                relevance_score=0.9  # Higher score for reference facilities
                            )
                            session.add(evidence)
                            created_evidence += 1
                        except Exception as e:
                            logger.error(f"Error processing facility article: {e}")
            
            session.commit()
        
        # Note: Investigation triggering would be handled by a separate service
        # when InvestigationTriggerService is implemented
        
        return {
            "articles_found": len(articles),
            "facilities_with_news": facility_news.get("facilities_with_news", 0),
            "evidence_created": created_evidence,
            "investigations_created": created_investigations,
            "status": "completed"
        }
    
    except Exception as e:
        logger.error(f"News monitoring failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}

