# Create empty configuration files
touch _config.yml
touch _toc.yml

# Create root-level Markdown files
touch introduction.md
touch installation.md
touch usage.md
touch troubleshooting.md
touch future_improvements.md

# Create and populate features directory
mkdir -p features
touch features/data_upload.md
touch features/date_range_selection.md
touch features/job_statistics.md
touch features/user_statistics.md
touch features/activity_heatmap.md
touch features/data_export.md

# Create and populate code_explanation directory
mkdir -p code_explanation
touch code_explanation/data_processing.md
touch code_explanation/visualisation.md
touch code_explanation/streamlit_interface.md

# Create and populate deployment directory
mkdir -p deployment
touch deployment/containerisation.md
touch deployment/hosting.md

echo "Directory structure and empty Markdown files created successfully."
