# Testing Guide for Job Application AI Agent

This guide will help you test the Job Application AI Agent, particularly the batch CV generation functionality that creates multiple tailored CVs based on different job listings.

## Setup

1. **Install the application**:
   ```bash
   # On Unix-based systems (macOS, Linux)
   ./install.sh
   
   # On Windows
   install.bat
   ```

2. **Activate the virtual environment**:
   ```bash
   # On Unix-based systems (macOS, Linux)
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate.bat
   ```

## Testing Batch CV Generation

### Method 1: Using the Test Script (Quickest method)

We've included a test script that automates the entire process:

```bash
./test_batch_processing.py --cv path/to/your/cv_template.docx
```

This script will:
1. Scrape job listings for "Software Engineer" in "Berlin" (default)
2. Fetch job descriptions for each job
3. Save the jobs to an Excel file
4. Generate tailored CVs for each job
5. Save the CVs to the output directory

You can customize the script with these options:
- `--keyword "Data Scientist"` - Change the job title to search for
- `--location "Remote"` - Change the location to search in
- `--max-jobs 10` - Change the maximum number of jobs to scrape
- `--output-dir "/custom/path"` - Specify a custom output directory

### Method 2: Using the Web Interface (Recommended for beginners)

1. **Start the web interface**:
   ```bash
   job-apply-ai web
   ```

2. **Open the web application**:
   - Open your browser and go to: http://localhost:5000

3. **Upload your CV template**:
   - Click on "Upload CV" button
   - Select your CV template file (must be a .docx file)
   - Click "Upload"

4. **Search for jobs**:
   - Enter a job title (e.g., "Software Engineer")
   - Enter a location (e.g., "Berlin" or "Remote")
   - Set the maximum number of jobs (e.g., 5)
   - Click "Search"

5. **Generate CVs for all jobs**:
   - On the search results page, click "Tailor CV for All Jobs"
   - Wait for the process to complete
   - You'll see a list of all generated CVs
   - Click "Download All CVs (ZIP)" to download all tailored CVs as a zip file

6. **Check the generated CVs**:
   - Extract the downloaded zip file
   - Open each CV to verify that the skills section has been tailored for each job
   - Note that each CV filename includes the date, company name, and job title

### Method 3: Using the Command Line

1. **Scrape job listings**:
   ```bash
   job-apply-ai scrape --keyword "Software Engineer" --location "Berlin" --max-jobs 5
   ```
   This will save job listings to the `job_apply_ai/outputs/jobs` directory.

2. **Generate tailored CVs for all jobs**:
   ```bash
   job-apply-ai batch --cv path/to/your/cv_template.docx --jobs-file job_apply_ai/outputs/jobs/linkedin_jobs_YYYY-MM-DD.xlsx
   ```
   Replace `path/to/your/cv_template.docx` with the path to your CV template and `YYYY-MM-DD` with the current date.

3. **Check the generated CVs**:
   - Go to the `job_apply_ai/outputs/cvs` directory
   - You'll find multiple CV files, each named with the date, company name, and job title
   - Open each CV to verify that the skills section has been tailored for each job

## Testing Individual CV Generation

If you want to test generating a CV for a single job:

1. **View job details**:
   - In the web interface, click on "View Details" for a specific job
   - Review the job description

2. **Generate a CV for that job**:
   - Click "Tailor CV for This Job"
   - Wait for the process to complete
   - Click "Download Tailored CV" to download the CV

## Folder Structure

The application uses the following folder structure for outputs:

- `job_apply_ai/outputs/jobs`: Contains Excel files with job listings
- `job_apply_ai/outputs/cvs`: Contains generated CV files

Each CV is named using the format: `CV_YYYY-MM-DD_CompanyName_JobTitle.docx`

## Troubleshooting

If you encounter any issues:

1. **Check the console output** for error messages
2. **Verify that your CV template has a skills section** (the application looks for headings like "skills", "technical skills", "core competencies", or "expertise")
3. **Make sure job descriptions are being fetched** correctly (view job details in the web interface)
4. **Check file permissions** if you're having trouble saving files

## Advanced Testing

For advanced testing, you can modify the skills categories in `job_apply_ai/cv_modifier/cv_analyzer.py` to match your specific skills and expertise.

You can also test with different CV templates to see how the application handles different formats. 