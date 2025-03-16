#!/usr/bin/env python3
"""
Test script for batch processing of CVs.

This script demonstrates how to use the batch processing functionality
to generate multiple tailored CVs for different jobs.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to test batch processing."""
    parser = argparse.ArgumentParser(description='Test batch processing of CVs')
    parser.add_argument('--cv', required=True, help='Path to CV template (.docx)')
    parser.add_argument('--keyword', default='Software Engineer', help='Job title or keyword to search for')
    parser.add_argument('--location', default='Berlin', help='Location to search in')
    parser.add_argument('--max-jobs', type=int, default=5, help='Maximum number of jobs to scrape')
    parser.add_argument('--output-dir', help='Directory to save the tailored CVs')
    
    args = parser.parse_args()
    
    # Check if CV template exists
    if not os.path.exists(args.cv):
        logger.error(f"CV template not found: {args.cv}")
        sys.exit(1)
    
    # Import modules
    try:
        from job_apply_ai.scraper.linkedin import LinkedInScraper
        from job_apply_ai.cv_modifier.cv_analyzer import batch_process_jobs
        from job_apply_ai.utils.helpers import ensure_directory_exists
    except ImportError:
        logger.error("Failed to import required modules. Make sure the package is installed.")
        logger.error("Run: pip install -e .")
        sys.exit(1)
    
    # Step 1: Scrape job listings
    logger.info(f"Scraping job listings for '{args.keyword}' in '{args.location}'...")
    scraper = LinkedInScraper(headless=True)
    jobs = scraper.scrape_job_listings(args.keyword, args.location, max_jobs=args.max_jobs)
    
    if not jobs:
        logger.error("No jobs found. Try different search terms.")
        sys.exit(1)
    
    logger.info(f"Found {len(jobs)} jobs")
    
    # Step 2: Fetch job descriptions
    logger.info("Fetching job descriptions...")
    for i, job in enumerate(jobs):
        logger.info(f"Fetching description for job {i+1}/{len(jobs)}: {job['title']} at {job['company']}")
        title, company, description = scraper.fetch_job_description(job['link'])
        jobs[i]['description'] = description
    
    # Step 3: Save jobs to Excel
    jobs_output_dir = os.path.join(os.getcwd(), "job_apply_ai", "outputs", "jobs")
    ensure_directory_exists(jobs_output_dir)
    
    today_date = datetime.today().strftime("%Y-%m-%d")
    jobs_file = os.path.join(jobs_output_dir, f"linkedin_jobs_{today_date}.xlsx")
    
    scraper.save_jobs_to_excel(jobs, jobs_file)
    logger.info(f"Saved jobs to {jobs_file}")
    
    # Step 4: Generate tailored CVs
    cv_output_dir = args.output_dir or os.path.join(os.getcwd(), "job_apply_ai", "outputs", "cvs")
    ensure_directory_exists(cv_output_dir)
    
    logger.info("Generating tailored CVs...")
    generated_cvs = batch_process_jobs(jobs_file, args.cv, cv_output_dir)
    
    if generated_cvs:
        logger.info(f"Successfully generated {len(generated_cvs)} tailored CVs:")
        for cv_path in generated_cvs:
            logger.info(f"  - {cv_path}")
    else:
        logger.warning("Failed to generate any CVs")
    
    logger.info("Test completed")

if __name__ == "__main__":
    main() 