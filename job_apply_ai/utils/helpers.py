"""
Helper Utilities

This module provides utility functions used across the application.
"""

import os
import re
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path):
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path (str): Path to the directory.
        
    Returns:
        bool: True if the directory exists or was created, False otherwise.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {str(e)}")
        return False

def generate_filename(prefix, extension, include_date=True):
    """
    Generate a filename with an optional date component.
    
    Args:
        prefix (str): Prefix for the filename.
        extension (str): File extension (without the dot).
        include_date (bool): Whether to include the date in the filename.
        
    Returns:
        str: Generated filename.
    """
    if include_date:
        today_date = datetime.today().strftime("%Y-%m-%d")
        return f"{prefix}_{today_date}.{extension}"
    return f"{prefix}.{extension}"

def sanitize_filename(filename):
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename (str): Filename to sanitize.
        
    Returns:
        str: Sanitized filename.
    """
    # Replace invalid characters with underscores
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def load_excel_file(file_path):
    """
    Load data from an Excel file into a pandas DataFrame.
    
    Args:
        file_path (str): Path to the Excel file.
        
    Returns:
        DataFrame or None: Loaded DataFrame or None if an error occurred.
    """
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"Error loading Excel file {file_path}: {str(e)}")
        return None

def save_excel_file(df, file_path):
    """
    Save a pandas DataFrame to an Excel file.
    
    Args:
        df (DataFrame): DataFrame to save.
        file_path (str): Path to save the Excel file.
        
    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    try:
        df.to_excel(file_path, index=False)
        logger.info(f"Saved Excel file to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving Excel file {file_path}: {str(e)}")
        return False

def extract_text_from_docx(file_path):
    """
    Extract text from a Word document.
    
    Args:
        file_path (str): Path to the Word document.
        
    Returns:
        str or None: Extracted text or None if an error occurred.
    """
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error extracting text from Word document {file_path}: {str(e)}")
        return None

def format_job_title(title):
    """
    Format a job title for display or filename purposes.
    
    Args:
        title (str): Job title to format.
        
    Returns:
        str: Formatted job title.
    """
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title.strip())
    
    # Capitalize first letter of each word
    title = title.title()
    
    return title

def format_company_name(company):
    """
    Format a company name for display or filename purposes.
    
    Args:
        company (str): Company name to format.
        
    Returns:
        str: Formatted company name.
    """
    # Remove extra whitespace
    company = re.sub(r'\s+', ' ', company.strip())
    
    # Replace spaces with underscores for filenames
    company = company.replace(' ', '_')
    
    return company 