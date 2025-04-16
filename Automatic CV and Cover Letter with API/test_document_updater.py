"""
Test script for the document updater module.
This is a mock test since we don't want to make actual API calls during testing.
"""

import os
import sys
import docx
from unittest import mock

# Add the project root to the path
sys.path.append('/home/ubuntu/cv_tailoring_project')

from src.updaters.document_updater import DocumentUpdater
from src.utils.openai_integration import OpenAIIntegration

def test_document_updater():
    """Test the document updater module with mock responses."""
    print("Testing document updater module...")
    
    # Paths to test documents
    cv_path = '/home/ubuntu/cv_tailoring_project/data/Imon Hosen - Resume_Template_ATS.docx'
    cover_letter_path = '/home/ubuntu/cv_tailoring_project/data/Cover Letter_Imon .docx'
    
    # Create a mock OpenAI integration
    mock_openai = mock.MagicMock(spec=OpenAIIntegration)
    
    # Set up mock responses
    mock_openai.analyze_job_description.return_value = {
        "raw_response": """
        {
            "profile_summary": "Information Engineering student at HAW Hamburg with experience in data analysis and project coordination, seeking a part-time working student role in IT Project Management.",
            "skills": ["Project coordination", "MS Office", "Data analysis", "Documentation"],
            "experience_highlights": ["Assisted in project tracking", "Created documentation", "Analyzed data"],
            "keywords_to_emphasize": ["project management", "coordination", "documentation"]
        }
        """
    }
    
    mock_openai.tailor_cover_letter.return_value = "This is a tailored cover letter body text for testing purposes."
    
    # Initialize document updater with mock OpenAI integration
    document_updater = DocumentUpdater(cv_path, cover_letter_path, mock_openai)
    
    # Test analyze_job_description method
    job_description = "This is a test job description for an IT Project Management position."
    analysis = document_updater.analyze_job_description(job_description)
    
    assert "raw_response" in analysis
    print("✓ analyze_job_description method works correctly")
    
    # Test output paths
    output_cv_path = '/home/ubuntu/cv_tailoring_project/output/test_cv.docx'
    output_cl_path = '/home/ubuntu/cv_tailoring_project/output/test_cover_letter.docx'
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_cv_path), exist_ok=True)
    
    # Test update_cv method
    cv_result = document_updater.update_cv(job_description, output_cv_path)
    assert os.path.exists(cv_result)
    print(f"✓ update_cv method works correctly, file created at {cv_result}")
    
    # Test update_cover_letter method
    cl_result = document_updater.update_cover_letter(job_description, output_cl_path)
    assert os.path.exists(cl_result)
    print(f"✓ update_cover_letter method works correctly, file created at {cl_result}")
    
    print("\nDocument updater module tests completed successfully!")
    return True

if __name__ == "__main__":
    # Use patch to mock the OpenAI integration
    with mock.patch('src.utils.openai_integration.OpenAIIntegration') as MockOpenAI:
        test_document_updater()
