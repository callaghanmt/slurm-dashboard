#!/bin/bash

# Function to create sample content
create_sample_content() {
    local file=$1
    local title=$2
    
    echo "# $title" > "$file"
    echo "" >> "$file"
    echo "This is a sample page for $title. Replace this content with actual documentation." >> "$file"
    echo "" >> "$file"
    echo "## Sample Section" >> "$file"
    echo "" >> "$file"
    echo "Add more detailed information about $title here." >> "$file"
    echo "" >> "$file"
    echo "### Subsection" >> "$file"
    echo "" >> "$file"
    echo "- Bullet point 1" >> "$file"
    echo "- Bullet point 2" >> "$file"
    echo "- Bullet point 3" >> "$file"
}

# Main documentation pages
create_sample_content "docs/introduction.md" "Introduction to Slurm Dashboard"
create_sample_content "docs/installation.md" "Installation Guide"
create_sample_content "docs/usage.md" "Usage Instructions"
create_sample_content "docs/troubleshooting.md" "Troubleshooting"
create_sample_content "docs/future_improvements.md" "Future Improvements"

# Features
create_sample_content "docs/features/index.md" "Features Overview"
create_sample_content "docs/features/data_upload.md" "Data Upload"
create_sample_content "docs/features/date_range_selection.md" "Date Range Selection"
create_sample_content "docs/features/job_statistics.md" "Job Statistics"
create_sample_content "docs/features/user_statistics.md" "User Statistics"
create_sample_content "docs/features/activity_heatmap.md" "Activity Heatmap"
create_sample_content "docs/features/data_export.md" "Data Export"

# Code Explanation
create_sample_content "docs/code_explanation/index.md" "Code Explanation Overview"
create_sample_content "docs/code_explanation/data_processing.md" "Data Processing"
create_sample_content "docs/code_explanation/visualisation.md" "Visualisation"
create_sample_content "docs/code_explanation/streamlit_interface.md" "Streamlit Interface"

# Deployment
create_sample_content "docs/deployment/index.md" "Deployment Overview"
create_sample_content "docs/deployment/containerisation.md" "Containerisation"
create_sample_content "docs/deployment/hosting.md" "Hosting"

echo "Sample content has been added to all Markdown files."
