# SLURM Dashboard Streamlit App

# Slurm Accounting Dashboard

## Description

The Slurm Accounting Dashboard is a Streamlit-based web application designed to visualise and analyse Slurm accounting data. It provides insights into cluster usage, job costs, and user activity through interactive charts and tables.

## Features

- Total cost summary for the billing period
- Account usage distribution visualisation
- Top users by cost analysis
- User activity heatmap
- Account activity timeline
- Cost trend analysis
- Average job cost by account
- Cost per minute comparison across accounts
- Raw data display

## How It Works

The application reads Slurm accounting data from a text file, processes it, and generates various visualizations to help understand cluster usage patterns and costs. Users can filter data by date range and specific accounts using the sidebar controls.

## Installation

To run this application locally, follow these steps:

1. Clone this repository:

~~~
git clone https://github.com/callaghanmt/slurm-dashboard.git
cd slurm-dashboard
~~~
2. Create a new Conda environment:

~~~
conda create -n slurm-dashboard python=3.8
conda activate slurm-dashboard
~~~

3. Install the required packages:

~~~
pip install -r requirements.txt
~~~

## Usage

1. Activate the Conda environment:

~~~
conda activate slurm-dashboard
~~~

2. Run the Streamlit app:

~~~
streamlit run app.py
~~~

3. Open your web browser and navigate to the URL displayed in the terminal (usually http://localhost:8501).

4. Use the file uploader in the app to select your Slurm accounting data file (in .txt format).

5. Use the sidebar controls to filter the data by date range and account.

6. Explore the various visualisations and insights provided by the dashboard.

## Data Format

The app expects the Slurm accounting data to be in a specific text format.

## Contributing

Contributions to improve the Slurm Accounting Dashboard are welcome. Please feel free to submit issues or pull requests.

## License
See LICENSE file in this repo.
