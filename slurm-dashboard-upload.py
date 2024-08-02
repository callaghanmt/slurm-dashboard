import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
from datetime import datetime
import os

# Function to parse the AllocTRES field
def parse_alloc_tres(alloc_tres):
    if pd.isna(alloc_tres) or not isinstance(alloc_tres, str):
        return 0
    try:
        items = alloc_tres.split(',')
        billing = next((item.split('=')[1] for item in items if item.startswith('billing=')), None)
        return float(billing) / (1 * 10**8) if billing else 0
    except Exception:
        return 0

# Function to calculate job duration in minutes
def calculate_duration(start, end):
    if pd.isna(start) or pd.isna(end):
        return 0
    duration = (end - start).total_seconds() / 60
    return max(duration, 0)  # Ensure non-negative duration

# Function to load and process data
def load_data(uploaded_file):
    content = uploaded_file.getvalue().decode('utf-8')
    df = pd.read_csv(StringIO(content), sep='|')
    
    # Check if required columns exist
    required_columns = ['Account', 'User', 'AllocTRES', 'Start', 'End']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return None

    # Parse AllocTRES and calculate cost
    df['billing_rate'] = df['AllocTRES'].apply(parse_alloc_tres)
    
    # Convert Start and End to datetime, handling potential errors
    for col in ['Start', 'End']:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calculate duration only for valid datetime entries
    df['duration'] = df.apply(lambda row: calculate_duration(row['Start'], row['End']) if pd.notna(row['Start']) and pd.notna(row['End']) else 0, axis=1)
    df['total_cost'] = df['billing_rate'] * df['duration']
    df['total_cost_pounds'] = df['total_cost'] / 100  # Convert pence to pounds
    
    return df

# Main Streamlit app
# Main Streamlit app
def main():
    st.title("Slurm Accounting Dashboard")

    # File uploader
    uploaded_file = st.file_uploader("Choose a file", type="txt")
    if uploaded_file is not None:
        df = load_data(uploaded_file)

        # Sidebar for controls
        st.sidebar.header("Controls")
        
        # Date range selector
        min_date = df['Start'].min().date()
        max_date = df['End'].max().date()
        start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

        # Account selector
        accounts = df['Account'].unique()
        selected_account = st.sidebar.selectbox("Select Account", ['All'] + list(accounts))

        # Filter data based on selection
        mask = (df['Start'].dt.date >= start_date) & (df['End'].dt.date <= end_date)
        if selected_account != 'All':
            mask &= (df['Account'] == selected_account)
        filtered_df = df.loc[mask]

        # Calculate total cost for the billing period
        total_cost = filtered_df['total_cost_pounds'].sum()

        # Display total cost for the billing period
        st.header("Billing Summary")
        st.subheader(f"Total Cost this Billing Period: £{total_cost:.2f}")

        # Calculate and display total cost per account
        account_costs = filtered_df.groupby('Account')['total_cost_pounds'].sum().sort_values(ascending=False)
        st.subheader("Total Cost per Account")
        
        # Create a DataFrame for better formatting
        account_costs_df = pd.DataFrame({
            'Account': account_costs.index,
            'Total Cost (£)': account_costs.values
        })
        
        # Format the 'Total Cost' column
        account_costs_df['Total Cost (£)'] = account_costs_df['Total Cost (£)'].apply(lambda x: f"£{x:.2f}")
        
        # Display the table
        st.table(account_costs_df)


       # 1. Account Usage Distribution
        st.header("Account Usage Distribution")
        account_usage = filtered_df.groupby('Account')['total_cost_pounds'].sum()

        fig, ax = plt.subplots(figsize=(10, 6))
        wedges, texts, autotexts = ax.pie(account_usage, 
                                        autopct=lambda pct: f'{pct:.1f}%' if pct > 2 else '',
                                        pctdistance=0.8, 
                                        textprops={'color': "w"})

        # Add a legend
        ax.legend(wedges, account_usage.index,
                title="Accounts",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1))

        ax.set_title("Total Cost Distribution by Account")

        # Adjust the layout to make room for the legend
        plt.tight_layout()

        st.pyplot(fig)

        # 2. Top Users by Cost
        st.header("Top Users by Cost")
        top_users = filtered_df.groupby('User')['total_cost_pounds'].sum().nlargest(10)

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(top_users.index, top_users.values)

        # Add value labels on top of each bar
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'£{height:.2f}',
                    ha='center', va='bottom')

        # Set labels and title
        ax.set_xlabel('User')
        ax.set_ylabel('Total Cost (£)')
        ax.set_title('Top 10 Users by Cost')

        # Rotate x-axis labels for better readability if needed
        plt.xticks(rotation=45, ha='right')

        # Add pound signs to y-axis ticks
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))

        # Adjust layout
        plt.tight_layout()

        st.pyplot(fig)

        # 3. Job Duration Distribution
        st.header("Job Duration Distribution")
        fig, ax = plt.subplots()
        sns.histplot(filtered_df['duration'], bins=30, kde=True, ax=ax)
        ax.set_xlabel("Job Duration (minutes)")
        ax.set_title("Distribution of Job Durations")
        st.pyplot(fig)

        # 4. Account Activity Timeline
        st.header("Account Activity Timeline")
        timeline_data = filtered_df.groupby(['Account', pd.Grouper(key='Start', freq='D')])['total_cost_pounds'].sum().unstack(level=0).fillna(0)
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(timeline_data, cmap='YlOrRd', ax=ax)
        ax.set_xlabel("Date")
        ax.set_ylabel("Account")
        ax.set_title("Account Activity Timeline (Total Cost)")
        st.pyplot(fig)

        # 5. User Activity Heatmap

        st.header("User Activity Heatmap")

        # Prepare data for heatmap
        user_activity = filtered_df.groupby([filtered_df['Start'].dt.dayofweek, filtered_df['Start'].dt.hour])['User'].count().unstack()

        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(user_activity, cmap='YlOrRd', ax=ax)

        # Set labels and title
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Day of Week')
        ax.set_title('User Activity Heatmap')

        # Replace numeric labels with day names
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ax.set_yticklabels(days)

        # Add colorbar label
        cbar = ax.collections[0].colorbar
        cbar.set_label('Number of Jobs Started')

        plt.tight_layout()
        st.pyplot(fig)

        # Add caption
        st.caption("This heatmap shows the distribution of job start times across days of the week and hours of the day. " 
                "Darker colors indicate higher activity (more jobs started) during those time periods.")

        # 6. Cost Trend Analysis
        st.header("Cost Trend Analysis")
        daily_cost = filtered_df.groupby(filtered_df['Start'].dt.date)['total_cost_pounds'].sum().cumsum()

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(daily_cost.index, daily_cost.values)

        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Cost (£)")
        ax.set_title("Cumulative Cost Over Time")

        # Format y-axis ticks to show pound sign and comma separators
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)

        plt.tight_layout()
        st.pyplot(fig)

        
        # 7. Average Job Cost by Account
        st.header("Average Job Cost by Account")
        avg_job_cost = filtered_df.groupby('Account')['total_cost_pounds'].mean().sort_values(ascending=False)

        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(avg_job_cost.index, avg_job_cost.values)

        # Add value labels on top of each bar
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'£{height:.2f}',
                    ha='center', va='bottom')

        ax.set_xlabel("Account")
        ax.set_ylabel("Average Cost per Job (£)")
        ax.set_title("Average Job Cost by Account")

        # Format y-axis ticks to show pound sign and comma separators
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:,.2f}'))

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()
        st.pyplot(fig)

        # 8. Job Concurrency
        st.header("Job Concurrency Over Time")
        job_starts = pd.DataFrame({'time': filtered_df['Start'], 'value': 1})
        job_ends = pd.DataFrame({'time': filtered_df['End'], 'value': -1})
        job_events = pd.concat([job_starts, job_ends]).sort_values('time')
        job_concurrency = job_events['value'].cumsum()
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(job_events['time'], job_concurrency)
        ax.set_xlabel("Time")
        ax.set_ylabel("Number of Concurrent Jobs")
        ax.set_title("Job Concurrency Over Time")
        st.pyplot(fig)

        # 9. Cost per Minute Comparison
        st.header("Cost per Minute Comparison")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.boxplot(x='Account', y='billing_rate', data=filtered_df, ax=ax)
        ax.set_xlabel("Account")
        ax.set_ylabel("Cost per Minute")
        ax.set_title("Distribution of Cost per Minute by Account")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # 10. User Diversity per Account
        st.header("User Diversity per Account")
        user_diversity = filtered_df.groupby('Account')['User'].nunique().sort_values(ascending=False)
        st.bar_chart(user_diversity)

        # Display raw data
        st.header("Raw Data")
        st.dataframe(filtered_df)

if __name__ == "__main__":
    main()