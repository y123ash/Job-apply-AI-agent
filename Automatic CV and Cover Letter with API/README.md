# CV and Cover Letter Tailoring System

This project provides an automated system to tailor your CV and cover letter based on job descriptions using OpenAI's API. The system analyzes your existing documents and the job description, then generates customized versions that highlight relevant skills and experiences.

## Project Structure

```
cv_tailoring_project/
├── data/                   # Directory for storing CV and cover letter templates
│   ├── Cover Letter_Imon .docx
│   └── Imon Hosen - Resume_Template_ATS.docx
├── notebooks/              # Jupyter notebooks for interactive usage
│   └── cv_tailoring_system.ipynb
├── output/                 # Directory for storing generated documents
├── src/                    # Source code
│   ├── parsers/            # Document parsing modules
│   │   └── document_parser.py
│   ├── updaters/           # Document updating modules
│   │   └── document_updater.py
│   └── utils/              # Utility modules
│       └── openai_integration.py
└── README.md               # Project documentation
```

## Features

- Parse and analyze Word document CV and cover letter templates
- Extract sections, personal information, and content structure
- Analyze job descriptions using OpenAI's API
- Generate tailored CV with updated profile summary, skills, and experience highlights
- Create customized cover letter that addresses specific job requirements
- Interactive Jupyter notebook interface for easy usage
- Support for batch processing multiple job applications

## Requirements

- Python 3.6+
- python-docx
- openai
- Jupyter Notebook/Lab
- OpenAI API key

## Getting Started

1. Clone this repository or download the project files
2. Install the required dependencies:
   ```
   pip install python-docx openai jupyter
   ```
3. Place your CV and cover letter templates in the `data` directory
4. Launch the Jupyter notebook:
   ```
   jupyter notebook notebooks/cv_tailoring_system.ipynb
   ```
5. Follow the step-by-step instructions in the notebook

## Using the System

The Jupyter notebook provides a user-friendly interface with the following steps:

1. **Setup and Configuration**: Import necessary libraries and set up the environment
2. **Set up OpenAI API Key**: Enter your OpenAI API key
3. **Load Your CV and Cover Letter**: Load and analyze your existing documents
4. **Enter Job Description**: Paste the job description you're applying for
5. **Analyze Job Description**: Identify key requirements and skills
6. **Generate Tailored Documents**: Create customized versions of your CV and cover letter
7. **Customization Options**: Modify parameters to customize the tailoring process
8. **Process Multiple Job Applications**: Batch process multiple job descriptions

## Customization

You can customize the system by:

- Modifying the document parser to handle different CV/cover letter formats
- Adjusting the OpenAI prompts in the integration module
- Changing the OpenAI model used for analysis and generation
- Implementing additional document updating strategies

## OpenAI API Key

You'll need an OpenAI API key to use this system. You can obtain one from [OpenAI's website](https://platform.openai.com/account/api-keys).

The API key can be provided in two ways:
1. Directly in the Jupyter notebook (recommended for personal use)
2. As an environment variable named `OPENAI_API_KEY`

## Notes

- The system uses GPT-3.5-turbo by default for cost efficiency, but you can modify it to use GPT-4 for potentially better results
- Document parsing is based on a simplified approach and may need adjustments for different document formats
- The system creates new documents rather than modifying the originals to preserve your templates

## License

This project is provided for personal use.
