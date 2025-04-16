# How to Update the CV System to Use LinkedIn URLs

Follow these steps to update your notebook to support both LinkedIn URLs and job descriptions.

## Step 1: Install Required Dependencies

Run this in your terminal:

```bash
pip install requests beautifulsoup4
```

## Step 2: Replace the Job Description Input Cell

In `notebooks/cv_system.ipynb`, find this cell:

```python
# Input area for job description
job_description = """

"""

# Display the job description for confirmation
print("Job Description Preview (first 300 characters):")
print(job_description[:300] + "..." if len(job_description) > 300 else job_description)
print(f"\nTotal length: {len(job_description)} characters")
```

Replace it with this new version:

```python
# Choose input method
print("Choose input method:")
print("1. LinkedIn Job URL")
print("2. Job Description Text")
input_method = input("Enter 1 or 2: ")

# Input area for job description or LinkedIn URL
if input_method == "1":
    linkedin_url = input("Paste LinkedIn job URL: ")
    print("LinkedIn URL detected. Extracting job description...")
    try:
        job_description = openai_integration.extract_job_description_from_url(linkedin_url.strip())
        print("✓ Successfully extracted job description from LinkedIn")
    except Exception as e:
        print(f"Error extracting job description from URL: {str(e)}")
        job_description = input("Please paste the job description text directly instead: ")
else:
    print("Enter job description (paste below):")
    job_description = input()

# Display the job description for confirmation
print("\nJob Description Preview (first 300 characters):")
print(job_description[:300] + "..." if len(job_description) > 300 else job_description)
print(f"\nTotal length: {len(job_description)} characters")
```

## Step 3: How to Use

1. **Using a LinkedIn URL:**
   - Run the cell
   - Enter 1 when prompted
   - Paste the LinkedIn job URL (e.g., https://www.linkedin.com/jobs/view/your-job-id)
   - The system will automatically extract the job description

2. **Using a Job Description:**
   - Run the cell
   - Enter 2 when prompted
   - Paste the job description text
   - Continue with the rest of the notebook

## Example LinkedIn URL Format

LinkedIn job URLs typically look like:
```
https://www.linkedin.com/jobs/view/working-student-at-company-name-3824699765
```

## Troubleshooting

If you encounter errors with LinkedIn URL extraction:
- Make sure the URL is correct and publicly accessible
- Some LinkedIn job postings might require authentication
- As a fallback, you can always copy and paste the job description text directly 