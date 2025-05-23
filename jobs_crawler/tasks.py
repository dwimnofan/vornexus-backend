import asyncio
import re
from datetime import datetime
from celery import shared_task
from django.db import transaction
from crawl4ai import AsyncWebCrawler
from .models import JobSource, JobCategory, Job
from .utils import categorize_job

@shared_task
def crawl_jobs(source_id):
    """
    Celery task to crawl jobs from a specific source
    """
    try:
        source = JobSource.objects.get(id=source_id, is_active=True)
    except JobSource.DoesNotExist:
        return f"Source with ID {source_id} does not exist or is not active"
    
    # Run the async crawler in a synchronous context
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(crawl_source(source))
    
    return f"Crawled {result} jobs from {source.name}"

async def crawl_source(source):
    """
    Crawl a job source using Crawl4AI
    """
    async with AsyncWebCrawler() as crawler:
        # Run the crawler on the source URL
        result = await crawler.arun(url=source.url)
        
        # Process the crawled data
        job_count = await process_crawled_data(result, source)
        
        return job_count

async def process_crawled_data(result, source):
    """
    Process the crawled data and save jobs to the database
    """
    # Extract job listings from the crawled data
    job_listings = extract_job_listings(result)
    
    job_count = 0
    
    # Process each job listing
    for job_data in job_listings:
        # Skip if required fields are missing
        if not job_data.get('title') or not job_data.get('url'):
            continue
        
        # Determine job category
        category_name = categorize_job(job_data.get('title', ''), job_data.get('description', ''))
        
        # Get or create the category
        with transaction.atomic():
            category, _ = JobCategory.objects.get_or_create(name=category_name)
            
            # Check if job already exists
            if not Job.objects.filter(url=job_data['url']).exists():
                # Create new job
                Job.objects.create(
                    title=job_data.get('title', ''),
                    company=job_data.get('company', 'Unknown'),
                    location=job_data.get('location'),
                    description=job_data.get('description', ''),
                    url=job_data['url'],
                    salary=job_data.get('salary'),
                    posted_date=parse_date(job_data.get('posted_date')),
                    category=category,
                    source=source
                )
                job_count += 1
    
    return job_count

def extract_job_listings(result):
    """
    Extract job listings from LinkedIn
    """
    job_listings = []
    
    content = result.html
    
    # Look for job cards
    job_cards = re.findall(r'<div class="job-card[^>]*>(.*?)</div>', content, re.DOTALL)
    
    for card in job_cards:
        job_data = {}
        
        # Extract title
        title_match = re.search(r'<h3[^>]*>(.*?)</h3>', card)
        if title_match:
            job_data['title'] = title_match.group(1).strip()
        
        # Extract company
        company_match = re.search(r'<h4[^>]*>(.*?)</h4>', card)
        if company_match:
            job_data['company'] = company_match.group(1).strip()
        
        # Extract location
        location_match = re.search(r'<span class="job-location[^>]*>(.*?)</span>', card)
        if location_match:
            job_data['location'] = location_match.group(1).strip()
        
        # Extract URL
        url_match = re.search(r'href="(/jobs/view/[^"]+)"', card)
        if url_match:
            job_data['url'] = 'https://www.linkedin.com' + url_match.group(1)
        
        if job_data.get('title') and job_data.get('url'):
            job_listings.append(job_data)
    
    return job_listings

def parse_date(date_str):
    """
    Parse date string into a datetime object
    """
    if not date_str:
        return None
    
    # Try different date formats
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%B %d, %Y',
        '%d %B %Y',
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If all formats fail, try to extract date using regex
    # This is a simplified approach
    date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
    if date_match:
        day, month, year = map(int, date_match.groups())
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day).date()
        except ValueError:
            pass
    
    return None
