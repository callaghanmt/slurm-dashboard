import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from calendar import monthrange

# Configure the page
st.set_page_config(page_title="Slurm Accounting Dashboard", layout="wide")

# Load the data
@st.cache_data()
def load_data():
    try:
        usage_data = pd.read_csv('slurm_cost_data.csv')
        usage_data['date'] = pd.to_datetime(usage_data['date'])
        
        budget_data = pd.read_csv('budget_data.csv')
        
        return usage_data, budget_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

# Calculate budget usage
def calculate_budget_usage(filtered_df, budget_data, selected_partition, start_date, end_date):
    total_cost = filtered_df.groupby('date')['total_cost'].first().sum()
    
    monthly_budget = budget_data[budget_data['partition'] == selected_partition]['monthly_budget'].values[0]
    
    # Calculate the number of days in the selected period
    days_in_period = (end_date - start_date).days + 1
    
    # Calculate the budget for the selected period
    budget_for_period = (monthly_budget / 30) * days_in_period
    
    remaining_budget = budget_for_period - total_cost
    usage_percentage = (total_cost / budget_for_period) * 100
    
    return total_cost, budget_for_period, remaining_budget, usage_percentage

# Streamlit app
def main():
    st.title("Slurm Accounting Dashboard")

    # Load data
    usage_df, budget_df = load_data()
    
    if usage_df is None or budget_df is None:
        st.stop()

    # Sidebar for controls
    st.sidebar.header("Controls")
    
    # Date range selector
    min_date = usage_df['date'].min().date()
    max_date = usage_df['date'].max().date()
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    # Partition selector
    partitions = usage_df['partition'].unique()
    selected_partition = st.sidebar.selectbox("Select Partition", partitions)

    # Filter data based on selection
    mask = (usage_df['date'].dt.date >= start_date) & (usage_df['date'].dt.date <= end_date) & (usage_df['partition'] == selected_partition)
    filtered_df = usage_df.loc[mask]

    # Calculate budget usage
    total_cost, budget_for_period, remaining_budget, usage_percentage = calculate_budget_usage(filtered_df, budget_df, selected_partition, start_date, end_date)

    # Display budget information
    st.header(f"Budget Information for {selected_partition}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cost", f"£{total_cost:.2f}")
    col2.metric("Budget for Period", f"£{budget_for_period:.2f}")
    col3.metric("Remaining Budget", f"£{remaining_budget:.2f}")
    col4.metric("Usage Percentage", f"{usage_percentage:.1f}%")

    # Display budget usage chart
    st.header("Budget Usage")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(['Used', 'Remaining'], [total_cost, remaining_budget], color=['#ff9999', '#66b3ff'])
    ax.set_ylabel("Amount (£)")
    ax.set_title(f"Budget Usage for {selected_partition}")
    for i, v in enumerate([total_cost, remaining_budget]):
        ax.text(i, v, f'£{v:.2f}', ha='center', va='bottom')
    st.pyplot(fig)

    # Display cost over time chart
    st.header("Cost Over Time")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(data=filtered_df, x='date', y='total_cost', ax=ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Cost (£)")
    st.pyplot(fig)

    # Display user breakdown
    st.header("Cost per User")
    user_costs = filtered_df.groupby('user')['user_cost'].sum().sort_values(ascending=False)
    st.bar_chart(user_costs)

    # Relative usage per user within partition
    st.header(f"Relative Usage per User in {selected_partition}")
    
    # Calculate total usage per user
    user_totals = filtered_df.groupby('user')['user_cost'].sum()
    
    # Option to switch between pie chart and stacked bar
    chart_type = st.radio("Select chart type for relative usage", ('Pie Chart', 'Stacked Bar'))
    
    if chart_type == 'Pie Chart':
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.pie(user_totals, labels=user_totals.index, autopct='%1.1f%%')
        ax.set_title(f"User Usage Distribution in {selected_partition}")
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        user_totals.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title(f"User Usage Distribution in {selected_partition}")
        ax.set_xlabel("User")
        ax.set_ylabel("Total Cost (£)")
    
    st.pyplot(fig)

    # Display raw data
    st.header("Raw Data")
    st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
