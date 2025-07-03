"""
Web Interface for Job Application AI Agent

This module provides a Flask web application for the job application AI agent.
"""

import os
import logging
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
import pandas as pd
import zipfile
import io

from job_apply_ai.scraper.linkedin import LinkedInScraper
from job_apply_ai.cv_modifier.cv_analyzer import CVAnalyzer, CVModifier, batch_process_jobs
from job_apply_ai.utils.helpers import ensure_directory_exists

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'job_apply_ai')
ensure_directory_exists(app.config['UPLOAD_FOLDER'])

# Create output directories
app.config['CV_OUTPUT_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'cvs')
app.config['JOBS_OUTPUT_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'jobs')
ensure_directory_exists(app.config['CV_OUTPUT_DIR'])
ensure_directory_exists(app.config['JOBS_OUTPUT_DIR'])

# Ensure session data is saved
app.config['SESSION_TYPE'] = 'filesystem'

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search_jobs():
    """Handle job search form and display results."""
    if request.method == 'POST':
        keyword = request.form.get('keyword', '')
        location = request.form.get('location', '')
        max_jobs = int(request.form.get('max_jobs', 10))
        
        if not keyword or not location:
            flash('Please enter both job title and location', 'error')
            return redirect(url_for('index'))
        
        try:
            # Scrape jobs
            scraper = LinkedInScraper(headless=True)
            jobs = scraper.scrape_job_listings(keyword, location, max_jobs=max_jobs)
            
            if not jobs:
                flash('No jobs found. Try different search terms.', 'warning')
                return redirect(url_for('index'))
            
            # Fetch job descriptions
            for i, job in enumerate(jobs):
                logger.info(f"Fetching description for job {i+1}/{len(jobs)}: {job['title']}")
                title, company, description = scraper.fetch_job_description(job['link'])
                jobs[i]['description'] = description
            
            # Save jobs to session
            session['jobs'] = jobs
            
            # Save to Excel for reference
            today_date = datetime.today().strftime("%Y-%m-%d")
            filename = f"linkedin_jobs_{today_date}.xlsx"
            filepath = os.path.join(app.config['JOBS_OUTPUT_DIR'], filename)
            
            df = pd.DataFrame(jobs)
            df.to_excel(filepath, index=False)
            session['jobs_file'] = filepath
            session['excel_filename'] = filename
            
            # Process job descriptions to extract skills
            analyzer = CVAnalyzer()
            processed_jobs = []
            
            for job in jobs:
                if job.get('description'):
                    matched_skills, matched_requirements, matched_categories = analyzer.extract_skills_from_description(job['description'])
                    job['matched_skills'] = matched_skills
                    job['matched_categories'] = matched_categories
                    processed_jobs.append(job)
            
            session['processed_jobs'] = processed_jobs
            
            return render_template('job_list.html', 
                                  jobs=processed_jobs, 
                                  excel_file=filename,
                                  excel_path=filepath)
            
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/upload_cv', methods=['GET', 'POST'])
def upload_cv():
    """Handle CV template upload."""
    if request.method == 'POST':
        if 'cv_file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['cv_file']
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.docx'):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], 'cv_template.docx')
            file.save(filename)
            session['cv_template'] = filename
            flash('CV template uploaded successfully', 'success')
            
            # If we have jobs, redirect to job list
            if session.get('processed_jobs'):
                return redirect(url_for('job_list'))
            return redirect(url_for('index'))
        else:
            flash('Please upload a .docx file', 'error')
            return redirect(request.url)
    
    return render_template('upload_cv.html')

@app.route('/job_list')
def job_list():
    """Display the list of jobs with Make CV buttons."""
    processed_jobs = session.get('processed_jobs', [])
    excel_filename = session.get('excel_filename')
    excel_path = session.get('jobs_file')
    
    if not processed_jobs:
        flash('No jobs found. Please search for jobs first.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('job_list.html', 
                          jobs=processed_jobs, 
                          excel_file=excel_filename,
                          excel_path=excel_path)

@app.route('/download_excel')
def download_excel():
    """Download the Excel file with job listings."""
    jobs_file = session.get('jobs_file')
    
    if not jobs_file or not os.path.exists(jobs_file):
        flash('Excel file not found', 'error')
        return redirect(url_for('index'))
    
    return send_file(jobs_file, as_attachment=True)

@app.route('/make_cv/<int:job_id>')
def make_cv(job_id):
    """Generate a CV for a specific job."""
    processed_jobs = session.get('processed_jobs', [])
    cv_template = session.get('cv_template')
    
    if not processed_jobs or job_id >= len(processed_jobs):
        flash('Job not found', 'error')
        return redirect(url_for('job_list'))
    
    if not cv_template:
        flash('Please upload a CV template first', 'error')
        return redirect(url_for('upload_cv'))
    
    job = processed_jobs[job_id]
    
    try:
        # Create CV modifier
        modifier = CVModifier(cv_template)
        
        # Get matched categories
        matched_categories = job.get('matched_categories', {})
        
        if not matched_categories:
            # Try to extract skills again with the job title for context
            analyzer = CVAnalyzer()
            description = job.get('description', '')
            if description:
                # Add job title to the document's user_data for better skill extraction
                doc = analyzer.nlp(description)
                doc.user_data['job_title'] = job.get('title', '')
                matched_skills, _, matched_categories = analyzer.extract_skills_from_description(description)
                
                if not matched_skills:
                    # If still no skills, add some generic ones based on job title
                    job_title = job.get('title', '').lower()
                    logger.warning(f"No skills found for job: {job_title}")
                    
                    # Add some generic skills
                    matched_categories = {
                        "Soft Skills": ["communication", "teamwork", "problem solving", 
                                       "time management", "adaptability"]
                    }
                    
                    # Try to add some technical skills based on job title keywords
                    if any(kw in job_title for kw in ["developer", "engineer", "programmer"]):
                        matched_categories["Programming Languages"] = ["python", "javascript", "java"]
                    elif any(kw in job_title for kw in ["data", "analyst", "analytics"]):
                        matched_categories["Business & Analytics"] = ["excel", "sql", "data analysis"]
                    elif any(kw in job_title for kw in ["manager", "lead", "director"]):
                        matched_categories["Methodologies"] = ["agile", "scrum", "project management"]
                    elif any(kw in job_title for kw in ["designer", "ux", "ui"]):
                        matched_categories["Tools & Platforms"] = ["figma", "adobe", "sketch"]
                    
                    flash('No specific skills found in job description. Adding generic skills based on job title.', 'warning')
        
        # Update skills section
        if modifier.update_skills_section(matched_categories):
            # Save the modified CV
            today_date = datetime.today().strftime("%Y-%m-%d")
            safe_company = job['company'].replace(' ', '_')
            safe_title = job['title'].replace(' ', '_')
            output_filename = f"CV_{today_date}_{safe_company}_{safe_title}.docx"
            output_path = os.path.join(app.config['CV_OUTPUT_DIR'], output_filename)
            
            if modifier.save_modified_cv(output_path):
                # Store the path for download
                session['current_cv'] = output_path
                session['current_cv_filename'] = output_filename
                
                # Update the job with the matched categories if they were generated here
                job['matched_categories'] = matched_categories
                
                flash('CV generated successfully', 'success')
                return render_template('cv_success.html', 
                                      job=job, 
                                      cv_filename=output_filename,
                                      matched_categories=matched_categories)
        
        flash('Failed to generate CV. Please check if your CV template has a skills section.', 'error')
        return redirect(url_for('job_list'))
        
    except Exception as e:
        logger.error(f"Error generating CV: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('job_list'))

@app.route('/download_cv')
def download_cv():
    """Download the current CV."""
    cv_path = session.get('current_cv')
    
    if not cv_path or not os.path.exists(cv_path):
        flash('CV file not found', 'error')
        return redirect(url_for('job_list'))
    
    return send_file(cv_path, as_attachment=True)

@app.route('/make_all_cvs')
def make_all_cvs():
    """Generate CVs for all jobs."""
    processed_jobs = session.get('processed_jobs', [])
    cv_template = session.get('cv_template')
    
    if not processed_jobs:
        flash('No jobs found. Please search for jobs first.', 'error')
        return redirect(url_for('index'))
    
    if not cv_template:
        flash('Please upload a CV template first', 'error')
        return redirect(url_for('upload_cv'))
    
    try:
        # Generate CVs for all jobs
        successful_jobs = []
        failed_jobs = []
        generated_cvs = []
        
        # Create analyzer for re-extracting skills if needed
        analyzer = CVAnalyzer()
        
        for job in processed_jobs:
            matched_categories = job.get('matched_categories', {})
            
            # If no skills matched, try to extract them again
            if not matched_categories:
                description = job.get('description', '')
                if description:
                    # Add job title to the document's user_data for better skill extraction
                    doc = analyzer.nlp(description)
                    doc.user_data['job_title'] = job.get('title', '')
                    matched_skills, _, matched_categories = analyzer.extract_skills_from_description(description)
                    job['matched_categories'] = matched_categories
            
            # Create a fresh copy of the template for each job
            modifier = CVModifier(cv_template)
            
            # Update skills section
            if modifier.update_skills_section(matched_categories):
                # Save the modified CV
                today_date = datetime.today().strftime("%Y-%m-%d")
                safe_company = job['company'].replace(' ', '_')
                safe_title = job['title'].replace(' ', '_')
                output_filename = f"CV_{today_date}_{safe_company}_{safe_title}.docx"
                output_path = os.path.join(app.config['CV_OUTPUT_DIR'], output_filename)
                
                if modifier.save_modified_cv(output_path):
                    generated_cvs.append(output_path)
                    successful_jobs.append(job)
                else:
                    failed_jobs.append(job)
            else:
                failed_jobs.append(job)
        
        if generated_cvs:
            session['generated_cvs'] = generated_cvs
            session['successful_jobs'] = successful_jobs
            session['failed_jobs'] = failed_jobs
            
            flash(f'Successfully generated {len(generated_cvs)} CVs', 'success')
            if failed_jobs:
                flash(f'Failed to generate {len(failed_jobs)} CVs', 'warning')
                
            return render_template('all_cvs_success.html', 
                                  successful_jobs=successful_jobs,
                                  failed_jobs=failed_jobs)
        else:
            flash('No CVs were generated. Make sure your CV template has a skills section.', 'warning')
            return redirect(url_for('job_list'))
        
    except Exception as e:
        logger.error(f"Error generating CVs: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('job_list'))

@app.route('/download_all_cvs')
def download_all_cvs():
    """Download all generated CVs as a zip file."""
    generated_cvs = session.get('generated_cvs', [])
    
    if not generated_cvs:
        flash('No generated CVs available', 'error')
        return redirect(url_for('job_list'))
    
    # Create a zip file in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for cv_path in generated_cvs:
            if os.path.exists(cv_path):
                # Add file to zip with just the filename (not the full path)
                zf.write(cv_path, os.path.basename(cv_path))
    
    # Reset file pointer
    memory_file.seek(0)
    
    # Create a date-stamped filename for the zip
    today_date = datetime.today().strftime("%Y-%m-%d")
    zip_filename = f"All_CVs_{today_date}.zip"
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500

def main():
    """Run the Flask application."""
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    ensure_directory_exists(templates_dir)
    
    # Create basic templates if they don't exist
    create_basic_templates(templates_dir)
    ngrok.kill()
    app.config['DEBUG'] = True
    public_url = ngrok.connect(5050)
    print("🌐 PUBLIC NGROK LINK:", public_url)
    # Run the app
    serve(app, host="0.0.0.0", port=5050)
    #app.run(debug=True, host='0.0.0.0', port=5050)

def create_basic_templates(templates_dir):
    """Create basic HTML templates if they don't exist."""
    templates = {
        'index.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Job Application AI Agent</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding-top: 20px; padding-bottom: 40px; }
                .jumbotron { padding: 2rem; background-color: #f8f9fa; border-radius: 0.3rem; margin-bottom: 2rem; }
                .card { margin-bottom: 1.5rem; }
                .btn-primary { background-color: #0d6efd; }
                .btn-success { background-color: #198754; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="jumbotron">
                    <h1 class="display-4">Job Application AI Agent</h1>
                    <p class="lead">Search for jobs and generate tailored CVs</p>
                    <hr class="my-4">
                    
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-primary text-white">
                                    <h5 class="mb-0">Step 1: Upload CV Template</h5>
                                </div>
                                <div class="card-body">
                                    <p>First, upload your CV template (.docx format)</p>
                                    <a href="{{ url_for('upload_cv') }}" class="btn btn-primary">Upload CV Template</a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-primary text-white">
                                    <h5 class="mb-0">Step 2: Search for Jobs</h5>
                                </div>
                                <div class="card-body">
                                    <form action="{{ url_for('search_jobs') }}" method="post">
                                        <div class="mb-3">
                                            <label for="keyword" class="form-label">Job Title</label>
                                            <input type="text" class="form-control" id="keyword" name="keyword" placeholder="e.g., Software Engineer" required>
                                        </div>
                                        <div class="mb-3">
                                            <label for="location" class="form-label">Location</label>
                                            <input type="text" class="form-control" id="location" name="location" placeholder="e.g., Remote, Berlin" required>
                                        </div>
                                        <div class="mb-3">
                                            <label for="max_jobs" class="form-label">Number of Jobs</label>
                                            <input type="number" class="form-control" id="max_jobs" name="max_jobs" value="5" min="1" max="20">
                                        </div>
                                        <button type="submit" class="btn btn-primary">Search Jobs</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        ''',
        
        'upload_cv.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Upload CV Template</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding-top: 20px; padding-bottom: 40px; }
                .card { margin-top: 2rem; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Upload CV Template</h1>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <a href="{{ url_for('index') }}" class="btn btn-secondary mb-3">Back to Home</a>
                
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">Upload Your CV Template (.docx)</h5>
                    </div>
                    <div class="card-body">
                        <form action="{{ url_for('upload_cv') }}" method="post" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label for="cv_file" class="form-label">Select CV Template File</label>
                                <input class="form-control" type="file" id="cv_file" name="cv_file" accept=".docx" required>
                                <div class="form-text">Please upload a Microsoft Word (.docx) file.</div>
                            </div>
                            <button type="submit" class="btn btn-primary">Upload</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        ''',
        
        'job_list.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Job Listings</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding-top: 20px; padding-bottom: 40px; }
                .job-card { margin-bottom: 1.5rem; }
                .skills-badge { 
                    display: inline-block;
                    background-color: #e9ecef;
                    padding: 0.25rem 0.5rem;
                    border-radius: 0.25rem;
                    margin-right: 0.5rem;
                    margin-bottom: 0.5rem;
                    font-size: 0.875rem;
                }
                .action-buttons {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 1rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Job Listings</h1>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <div class="action-buttons mb-4">
                    <a href="{{ url_for('index') }}" class="btn btn-secondary">Back to Home</a>
                    
                    <div>
                        {% if excel_file %}
                            <a href="{{ url_for('download_excel') }}" class="btn btn-success">Download Excel</a>
                        {% endif %}
                        
                        {% if jobs %}
                            <a href="{{ url_for('make_all_cvs') }}" class="btn btn-primary">Generate All CVs</a>
                        {% endif %}
                    </div>
                </div>
                
                <div class="alert alert-info">
                    <h4 class="alert-heading">Found {{ jobs|length }} Jobs</h4>
                    <p>Click "Make CV" to generate a tailored CV for a specific job.</p>
                </div>
                
                {% for job in jobs %}
                <div class="card job-card">
                    <div class="card-header">
                        <h5 class="mb-0">{{ job.title }}</h5>
                    </div>
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">{{ job.company }}</h6>
                        
                        {% if job.matched_skills %}
                            <div class="mt-3">
                                <h6>Matched Skills:</h6>
                                <div>
                                    {% for skill in job.matched_skills %}
                                        <span class="skills-badge">{{ skill }}</span>
                                    {% endfor %}
                                </div>
                            </div>
                        {% endif %}
                        
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <a href="{{ job.link }}" target="_blank" class="btn btn-outline-primary btn-sm">View on LinkedIn</a>
                            <a href="{{ url_for('make_cv', job_id=loop.index0) }}" class="btn btn-success">Make CV</a>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        ''',
        
        'cv_success.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>CV Generated Successfully</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding-top: 20px; padding-bottom: 40px; }
                .category-card { margin-bottom: 1rem; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert alert-success">
                    <h4 class="alert-heading">Success!</h4>
                    <p>Your CV has been tailored for the position of <strong>{{ job.title }}</strong> at <strong>{{ job.company }}</strong>.</p>
                </div>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">Skills Added to Your CV</h5>
                    </div>
                    <div class="card-body">
                        {% if matched_categories %}
                            {% for category, skills in matched_categories.items() %}
                                <div class="card category-card">
                                    <div class="card-header">
                                        <h6 class="mb-0">{{ category }}</h6>
                                    </div>
                                    <div class="card-body">
                                        <p>{{ skills|join(', ') }}</p>
                                    </div>
                                </div>
                            {% endfor %}
                        {% else %}
                            <p class="text-muted">No specific skills matched.</p>
                        {% endif %}
                    </div>
                </div>
                
                <div class="d-flex justify-content-between">
                    <a href="{{ url_for('job_list') }}" class="btn btn-secondary">Back to Job List</a>
                    <a href="{{ url_for('download_cv') }}" class="btn btn-primary">Download CV</a>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        ''',
        
        'all_cvs_success.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>All CVs Generated</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding-top: 20px; padding-bottom: 40px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert alert-success">
                    <h4 class="alert-heading">Success!</h4>
                    <p>Successfully generated {{ cv_count }} tailored CVs.</p>
                </div>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">Download Options</h5>
                    </div>
                    <div class="card-body">
                        <p>You can download all generated CVs as a ZIP file.</p>
                        <a href="{{ url_for('download_all_cvs') }}" class="btn btn-primary">Download All CVs (ZIP)</a>
                    </div>
                </div>
                
                <a href="{{ url_for('job_list') }}" class="btn btn-secondary">Back to Job List</a>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        ''',
        
        '404.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Not Found</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5 text-center">
                <h1 class="display-1">404</h1>
                <h2>Page Not Found</h2>
                <p class="lead">The page you are looking for does not exist.</p>
                <a href="{{ url_for('index') }}" class="btn btn-primary">Go Home</a>
            </div>
        </body>
        </html>
        ''',
        
        '500.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Server Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5 text-center">
                <h1 class="display-1">500</h1>
                <h2>Server Error</h2>
                <p class="lead">Something went wrong on our end. Please try again later.</p>
                <a href="{{ url_for('index') }}" class="btn btn-primary">Go Home</a>
            </div>
        </body>
        </html>
        '''
    }
    
    for filename, content in templates.items():
        filepath = os.path.join(templates_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write(content)
            logger.info(f"Created template: {filename}")

# Add template filter to get basename from path
@app.template_filter('basename')
def basename_filter(path):
    return os.path.basename(path)

if __name__ == '__main__':
    main() 
