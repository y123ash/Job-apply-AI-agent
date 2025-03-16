"""
Main entry point for the Job Application AI Agent.

This module provides a command-line interface to run different components
of the Job Application AI Agent.
"""

import argparse
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Job Application AI Agent')
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Web UI command
    web_parser = subparsers.add_parser('web', help='Start the web interface')
    web_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    web_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    web_parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    # Scraper command
    scraper_parser = subparsers.add_parser('scrape', help='Scrape job listings')
    scraper_parser.add_argument('--keyword', required=True, help='Job title or keyword to search for')
    scraper_parser.add_argument('--location', required=True, help='Location to search in')
    scraper_parser.add_argument('--output', help='Output file path (Excel)')
    scraper_parser.add_argument('--max-jobs', type=int, default=10, help='Maximum number of jobs to scrape')
    
    # CV modifier command
    cv_parser = subparsers.add_parser('tailor', help='Tailor CV for a job')
    cv_parser.add_argument('--cv', required=True, help='Path to CV template (.docx)')
    cv_parser.add_argument('--job', help='Path to job description file (text)')
    cv_parser.add_argument('--jobs-file', help='Path to Excel file with multiple job listings')
    cv_parser.add_argument('--output-dir', help='Directory to save the tailored CVs')
    cv_parser.add_argument('--output', help='Output file path for single job (.docx)')
    
    # Batch processing command
    batch_parser = subparsers.add_parser('batch', help='Process multiple jobs and generate CVs')
    batch_parser.add_argument('--cv', required=True, help='Path to CV template (.docx)')
    batch_parser.add_argument('--jobs-file', required=True, help='Path to Excel file with job listings')
    batch_parser.add_argument('--output-dir', help='Directory to save the tailored CVs')
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == 'web':
        # Import here to avoid circular imports
        from job_apply_ai.ui.app import app
        app.run(host=args.host, port=args.port, debug=args.debug)
        
    elif args.command == 'scrape':
        from job_apply_ai.scraper.linkedin import LinkedInScraper
        
        scraper = LinkedInScraper(headless=True)
        jobs = scraper.scrape_job_listings(args.keyword, args.location, max_jobs=args.max_jobs)
        
        if jobs:
            output_file = args.output
            if not output_file:
                # Save to the jobs output directory
                output_dir = os.path.join(os.getcwd(), "job_apply_ai", "outputs", "jobs")
                os.makedirs(output_dir, exist_ok=True)
                
                today_date = datetime.today().strftime("%Y-%m-%d")
                output_file = os.path.join(output_dir, f"linkedin_jobs_{today_date}.xlsx")
            
            filename = scraper.save_jobs_to_excel(jobs, output_file)
            logger.info(f"Jobs saved to {filename}")
            
            # Fetch job descriptions
            logger.info("Fetching job descriptions...")
            for i, job in enumerate(jobs):
                logger.info(f"Fetching description for job {i+1}/{len(jobs)}: {job['title']}")
                title, company, description = scraper.fetch_job_description(job['link'])
                jobs[i]['description'] = description
            
            # Save updated jobs with descriptions
            scraper.save_jobs_to_excel(jobs, output_file)
            logger.info(f"Updated jobs with descriptions saved to {filename}")
        else:
            logger.warning("No jobs found")
            
    elif args.command == 'tailor':
        from job_apply_ai.cv_modifier.cv_analyzer import CVAnalyzer, CVModifier, batch_process_jobs
        
        # Check if we're processing a single job or multiple jobs
        if args.jobs_file:
            # Process multiple jobs
            output_dir = args.output_dir or os.path.join(os.getcwd(), "job_apply_ai", "outputs", "cvs")
            generated_cvs = batch_process_jobs(args.jobs_file, args.cv, output_dir)
            
            if generated_cvs:
                logger.info(f"Generated {len(generated_cvs)} tailored CVs:")
                for cv_path in generated_cvs:
                    logger.info(f"  - {cv_path}")
            else:
                logger.warning("Failed to generate any CVs")
        
        elif args.job:
            # Process a single job
            # Read job description
            try:
                with open(args.job, 'r') as f:
                    job_description = f.read()
            except Exception as e:
                logger.error(f"Error reading job description: {str(e)}")
                sys.exit(1)
            
            # Analyze job description
            analyzer = CVAnalyzer()
            matched_skills, matched_requirements, matched_categories = analyzer.extract_skills_from_description(job_description)
            
            logger.info(f"Found {len(matched_skills)} matching skills")
            for category, skills in matched_categories.items():
                logger.info(f"{category}: {', '.join(skills)}")
            
            # Modify CV
            try:
                modifier = CVModifier(args.cv)
                
                if modifier.update_skills_section(matched_categories):
                    # Determine output path
                    if args.output:
                        output_path = args.output
                    else:
                        output_dir = args.output_dir or os.path.join(os.getcwd(), "job_apply_ai", "outputs", "cvs")
                        os.makedirs(output_dir, exist_ok=True)
                        today_date = datetime.today().strftime("%Y-%m-%d")
                        output_path = os.path.join(output_dir, f"Tailored_CV_{today_date}.docx")
                    
                    if modifier.save_modified_cv(output_path):
                        logger.info(f"Tailored CV saved to {output_path}")
                    else:
                        logger.error("Failed to save tailored CV")
                else:
                    logger.error("Failed to update skills section")
            except Exception as e:
                logger.error(f"Error tailoring CV: {str(e)}")
                sys.exit(1)
        
        else:
            logger.error("Either --job or --jobs-file must be specified")
            sys.exit(1)
    
    elif args.command == 'batch':
        from job_apply_ai.cv_modifier.cv_analyzer import batch_process_jobs
        
        output_dir = args.output_dir or os.path.join(os.getcwd(), "job_apply_ai", "outputs", "cvs")
        generated_cvs = batch_process_jobs(args.jobs_file, args.cv, output_dir)
        
        if generated_cvs:
            logger.info(f"Generated {len(generated_cvs)} tailored CVs:")
            for cv_path in generated_cvs:
                logger.info(f"  - {cv_path}")
        else:
            logger.warning("Failed to generate any CVs")
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main() 