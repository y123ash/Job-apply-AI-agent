"""
LinkedIn Job Scraper Module

This module provides functionality to scrape job listings from LinkedIn,
including job titles, company names, links, and full job descriptions.
"""

import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInScraper:
    """
    A class to scrape job listings from LinkedIn.
    """
    
    def __init__(self, headless=True):
        """
        Initialize the LinkedIn scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode.
        """
        self.headless = headless
        
    def _configure_driver(self):
        """
        Configure and return a Chrome WebDriver.
        
        Returns:
            WebDriver: Configured Chrome WebDriver instance.
        """
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Add user agent to avoid detection
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        driver = uc.Chrome(options=options)
        return driver
    
    def scrape_job_listings(self, keyword, location, max_jobs=10, max_days_old=14):
        """
        Scrape job listings from LinkedIn based on keyword and location.
        
        Args:
            keyword (str): Job title or keyword to search for.
            location (str): Location to search in.
            max_jobs (int): Maximum number of jobs to scrape.
            max_days_old (int): Maximum age of job postings in days.
            
        Returns:
            list: List of dictionaries containing job details.
        """
        logger.info(f"Scraping LinkedIn jobs for '{keyword}' in '{location}'")
        
        driver = self._configure_driver()
        search_url = f"https://www.linkedin.com/jobs/search?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        
        try:
            driver.get(search_url)
            
            # Scroll to load more jobs
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(2)
            
            # Wait for job listings to appear
            wait = WebDriverWait(driver, 15)
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "base-card")))
            except TimeoutException:
                logger.warning("No job listings found")
                driver.quit()
                return []
            
            jobs = []
            today = datetime.today()
            job_elements = driver.find_elements(By.CLASS_NAME, "base-card")
            
            for job in job_elements[:max_jobs]:
                try:
                    title = job.find_element(By.CSS_SELECTOR, "h3").text.strip()
                    company = job.find_element(By.CSS_SELECTOR, "h4").text.strip()
                    link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    # Check job posting date
                    try:
                        date_element = job.find_element(By.CSS_SELECTOR, "time")
                        posted_time = date_element.get_attribute("datetime")
                        if posted_time:
                            posted_date = datetime.strptime(posted_time[:10], "%Y-%m-%d")
                            days_ago = (today - posted_date).days
                            if days_ago > max_days_old:
                                logger.info(f"Skipping job: {title} (Posted {days_ago} days ago)")
                                continue
                        else:
                            days_ago = "Unknown"
                    except NoSuchElementException:
                        logger.warning(f"Could not find post time for: {title}, assuming it's recent")
                        days_ago = "Unknown"
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "link": link,
                        "source": "LinkedIn",
                        "posted_days_ago": days_ago
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing job listing: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} job listings")
            return jobs
            
        except Exception as e:
            logger.error(f"Error during job scraping: {str(e)}")
            return []
            
        finally:
            driver.quit()
    
    def fetch_job_description(self, job_url):
        """
        Fetch the full job description from a LinkedIn job URL.
        
        Args:
            job_url (str): URL of the LinkedIn job posting.
            
        Returns:
            tuple: (job_title, company_name, job_description)
        """
        logger.info(f"Fetching job description from {job_url}")
        
        driver = self._configure_driver()
        
        try:
            driver.get(job_url)
            wait = WebDriverWait(driver, 15)
            
            # Job Title
            try:
                title_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.topcard__title")))
                job_title = title_elem.text.strip()
            except TimeoutException:
                logger.warning("Could not find job title")
                job_title = ""
            
            # Company Name
            try:
                company_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.topcard__org-name-link")))
                company_name = company_elem.text.strip()
            except TimeoutException:
                logger.warning("Could not find company name")
                company_name = ""
            
            # Job Description
            try:
                desc_elem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "description__text")))
                job_description = desc_elem.text.strip()
            except TimeoutException:
                logger.warning("Could not find job description")
                job_description = ""
            
            return job_title, company_name, job_description
            
        except Exception as e:
            logger.error(f"Error fetching job description: {str(e)}")
            return "", "", ""
            
        finally:
            driver.quit()
    
    def save_jobs_to_excel(self, jobs, filename=None):
        """
        Save scraped jobs to an Excel file.
        
        Args:
            jobs (list): List of job dictionaries.
            filename (str, optional): Output filename. If None, generates a filename with today's date.
            
        Returns:
            str: Path to the saved Excel file.
        """
        if not jobs:
            logger.warning("No jobs to save")
            return None
        
        df = pd.DataFrame(jobs)
        
        if filename is None:
            today_date = datetime.today().strftime("%Y-%m-%d")
            filename = f"linkedin_jobs_{today_date}.xlsx"
        
        df.to_excel(filename, index=False)
        logger.info(f"Saved {len(jobs)} jobs to {filename}")
        
        return filename


def main():
    """
    Main function to demonstrate the LinkedIn scraper.
    """
    keyword = input("Enter job title (e.g., Software Engineer): ")
    location = input("Enter location (e.g., Remote, New York, Berlin): ")
    
    scraper = LinkedInScraper(headless=True)
    jobs = scraper.scrape_job_listings(keyword, location)
    
    if jobs:
        # Fetch full job descriptions
        for i, job in enumerate(jobs):
            logger.info(f"Fetching description for job {i+1}/{len(jobs)}: {job['title']}")
            title, company, description = scraper.fetch_job_description(job['link'])
            jobs[i]['description'] = description
        
        # Save to Excel
        filename = scraper.save_jobs_to_excel(jobs)
        print(f"\n✅ Jobs saved to {filename}")
    else:
        print("\n❌ No LinkedIn jobs found.")


if __name__ == "__main__":
    main() 