import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
@st.cache_data
def load_data():
    data = pd.read_csv('slurm_cost_data.csv')
    data['date'] = pd.to_datetime(data['date'])
    return data

# Streamlit app
def main():
    st.title("Slurm Accounting Dashboard")

    # Load data
    df = load_data()

    # Sidebar for controls
    st.sidebar.header("Controls")
    
    # Date range selector
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    # Partition selector
    partitions = df['partition'].unique()
    selected_partition = st.sidebar.selectbox("Select Partition", partitions)

    # Filter data based on selection
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date) & (df['partition'] == selected_partition)
    filtered_df = df.loc[mask]

    # Display total cost
    total_cost = filtered_df.groupby('date')['total_cost'].first().sum()
    st.header(f"Total Cost for {selected_partition}")
    st.metric("Total Cost", f"£{total_cost:.2f}")

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

    # Display raw data
    st.header("Raw Data")
    st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
