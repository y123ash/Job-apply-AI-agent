"""
OpenAI integration module for analyzing job descriptions and tailoring CV/cover letter.
This module provides functionality to interact with OpenAI API.
"""

import os
from openai import OpenAI
from typing import Dict, List, Tuple, Any, Optional
import json
import re
import requests
from bs4 import BeautifulSoup
import time


class OpenAIIntegration:
    """Class for handling OpenAI API interactions."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI integration.
        
        Args:
            api_key: OpenAI API key (optional, can be set via environment variable)
        """
        # If API key is provided, use it; otherwise check environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def is_api_key_set(self) -> bool:
        """Check if API key is set.
        
        Returns:
            Boolean indicating if API key is set
        """
        return bool(self.api_key) and bool(self.client)
    
    def set_api_key(self, api_key: str) -> None:
        """Set the OpenAI API key.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        
    def extract_job_description_from_url(self, url: str) -> str:
        """Extract job description from LinkedIn URL.
        
        Args:
            url: LinkedIn job posting URL
            
        Returns:
            Extracted job description text
        """
        if not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL format")

        if 'linkedin.com' not in url:
            raise ValueError("URL must be from LinkedIn")

        try:
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Make the request
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job title
            job_title = ""
            title_element = soup.find('h1', class_='top-card-layout__title')
            if title_element:
                job_title = title_element.get_text(strip=True)
            
            # Extract company name
            company = ""
            company_element = soup.find('a', class_='topcard__org-name-link')
            if company_element:
                company = company_element.get_text(strip=True)
            
            # Extract job description
            description = ""
            desc_element = soup.find('div', class_='show-more-less-html__markup')
            if desc_element:
                description = desc_element.get_text(strip=True)
            
            # If we couldn't find the description in the expected place, try alternative selectors
            if not description:
                desc_element = soup.find('div', class_='description__text')
                if desc_element:
                    description = desc_element.get_text(strip=True)
            
            # Combine all information
            full_description = f"Job Title: {job_title}\nCompany: {company}\n\nJob Description:\n{description}"
            
            return full_description
            
        except requests.RequestException as e:
            raise ValueError(f"Error fetching job description: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing job description: {str(e)}")

    def analyze_job_description(self, job_description_or_url: str, cv_content: str) -> Dict[str, Any]:
        """Analyze job description and suggest CV modifications.
        
        Args:
            job_description_or_url: Text of the job description or LinkedIn URL
            cv_content: Current content of the CV
            
        Returns:
            Dictionary with suggested modifications for different CV sections
        """
        if not self.is_api_key_set():
            raise ValueError("OpenAI API key is not set. Please set it using set_api_key() method.")
        
        # Check if input is a LinkedIn URL
        if job_description_or_url.startswith(('http://', 'https://')) and 'linkedin.com' in job_description_or_url:
            try:
                job_description = self.extract_job_description_from_url(job_description_or_url)
            except Exception as e:
                raise ValueError(f"Error extracting job description from URL: {str(e)}")
        else:
            job_description = job_description_or_url

        # Prepare the prompt for GPT
        prompt = f"""
        You are an expert CV and resume tailoring assistant. Your task is to analyze a job description 
        and suggest modifications to a CV to better match the job requirements.
        
        JOB DESCRIPTION:
        {job_description}
        
        CURRENT CV CONTENT:
        {cv_content}
        
        Please analyze the job description and suggest specific modifications to the following sections of the CV:
        1. Profile/Summary: Suggest a tailored professional summary that highlights relevant skills and experience.
        2. Skills: Identify key skills from the job description that should be emphasized or added.
        3. Experience: Suggest how to reframe or emphasize certain experiences to better match the job requirements.
        
        Format your response as a JSON object with the following structure:
        {{
            "profile_summary": "Suggested profile summary text",
            "skills": ["skill1", "skill2", "skill3"],
            "experience_highlights": ["point1", "point2", "point3"],
            "keywords_to_emphasize": ["keyword1", "keyword2", "keyword3"]
        }}
        """
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better analysis
                messages=[
                    {"role": "system", "content": "You are an expert CV tailoring assistant that provides structured JSON responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Lower temperature for more focused responses
                max_tokens=1000
            )
            
            # Extract and parse the response
            result = response.choices[0].message.content
            
            try:
                # Try to parse as JSON
                return json.loads(result)
            except json.JSONDecodeError:
                # If parsing fails, return raw response
                return {"raw_response": result}
            
        except Exception as e:
            return {"error": str(e)}
    
    def tailor_cover_letter(self, job_description: str, current_cover_letter: str, cv_content: str) -> str:
        """Generate a tailored cover letter based on job description and CV.
        
        Args:
            job_description: Text of the job description
            current_cover_letter: Current content of the cover letter
            cv_content: Content of the CV for reference
            
        Returns:
            Tailored cover letter text
        """
        if not self.is_api_key_set():
            raise ValueError("OpenAI API key is not set. Please set it using set_api_key() method.")
        
        # Prepare the prompt for GPT
        prompt = f"""
        You are an expert cover letter writing assistant. Your task is to tailor a cover letter 
        to better match a specific job description, while maintaining the original structure and tone.
        
        JOB DESCRIPTION:
        {job_description}
        
        CURRENT COVER LETTER:
        {current_cover_letter}
        
        CV CONTENT (for reference):
        {cv_content}
        
        Please rewrite the body of the cover letter to:
        1. Address specific requirements mentioned in the job description
        2. Highlight relevant skills and experiences from the CV
        3. Demonstrate enthusiasm for the specific role and company
        4. Maintain a professional tone similar to the original
        5. Keep approximately the same length as the original
        
        Return only the tailored body text of the cover letter, without greeting or closing.
        """
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better writing
                messages=[
                    {"role": "system", "content": "You are an expert cover letter writing assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Slightly higher temperature for creative writing
                max_tokens=1000
            )
            
            # Extract the response
            result = response.choices[0].message.content
            return result
            
        except Exception as e:
            return f"Error generating cover letter: {str(e)}"
