import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from calendar import monthrange

# ... (keep the previous imports and helper functions)

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

    # Display cost over time chart with budget line
    st.header("Cost Over Time")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot the actual cost
    sns.lineplot(data=filtered_df, x='date', y='total_cost', ax=ax, color='blue', label='Actual Cost')
    
    # Calculate and plot the budget line
    date_range = pd.date_range(start=start_date, end=end_date)
    daily_budget = budget_for_period / len(date_range)
    cumulative_budget = [daily_budget * (i+1) for i in range(len(date_range))]
    ax.plot(date_range, cumulative_budget, linestyle='--', color='red', label='Budget')
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Cost (£)")
    ax.legend()
    plt.title(f"Cost Over Time vs Budget for {selected_partition}")
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
