import streamlit as st
import pandas as pd
from datetime import datetime

# Title and File Upload
st.title("Batch Analysis App")
st.write("Upload your CSV files to generate Summary and Detailed views.")

# Upload CSV Files
sheet1_file = st.file_uploader("Upload 'Average Course Consumption By Batch' (Sheet1):", type=['csv'])
sheet2_file = st.file_uploader("Upload 'Average Live Participation by Batch' (Sheet2):", type=['csv'])
sheet3_file = st.file_uploader("Upload 'Consumption Based Batch Health' (Sheet3):", type=['csv'])
sheet4_file = st.file_uploader("Upload 'Live Based Batch Health' (Sheet4):", type=['csv'])

if sheet1_file and sheet2_file and sheet3_file and sheet4_file:
    # Load the sheets
    sheet1 = pd.read_csv(sheet1_file)
    sheet2 = pd.read_csv(sheet2_file)
    sheet3 = pd.read_csv(sheet3_file)
    sheet4 = pd.read_csv(sheet4_file)

    # Rename columns in Sheet3 for clarity
    sheet3.rename(columns={
        'Institutions Wh Institution Batch Batch UID Name': 'Batch Name',
        'Average of Average Consumption': 'Average Consumption',
        'Average of Elevate Weeklyelevatebatchactiveparticipation Bat 3d103a10': 'Active Participation',
        'Batch Health': 'Batch Health (Consumption)'
    }, inplace=True)

    # Rename columns in Sheet4 for clarity
    sheet4.rename(columns={
        'Batch Health': 'Batch Health (Live Participation)'
    }, inplace=True)

    # Step 1: Full Outer Join of Sheet3 and Sheet4
    master_data = pd.merge(sheet3, sheet4, on=['Batch Name', 'Week Number'], how='outer', suffixes=('_Sheet3', '_Sheet4'))

    # Step 2: Combine Active Participation
    master_data['Active Participation'] = master_data['Active Participation_Sheet3'].combine_first(master_data['Active Participation_Sheet4'])

    # Drop redundant Active Participation columns
    master_data.drop(columns=['Active Participation_Sheet3', 'Active Participation_Sheet4'], inplace=True)

    # Step 3: Merge with Sheet2
    merged_data = pd.merge(master_data, sheet2, on='Batch Name', how='left')

    # Step 4: Merge with Sheet1
    merged_data = pd.merge(merged_data, sheet1, on='Batch Name', how='left')

    # Step 5: Add Week Number Numeric and Sort
    merged_data['Week Number Numeric'] = merged_data['Week Number'].str.extract(r'(\d+)').astype(float)
    merged_data.sort_values(by=['Batch Name', 'Week Number Numeric'], inplace=True)

    # Step 6: Calculate Latest Week for Each Batch
    latest_week_data = merged_data.groupby('Batch Name')['Week Number Numeric'].max().reset_index()
    latest_week_data.rename(columns={'Week Number Numeric': 'Latest Week'}, inplace=True)

    # Step 7: Calculate Current Week for Each Batch
    # Convert 'Batch Start Date' to datetime format
    merged_data['Batch Start Date'] = pd.to_datetime(merged_data['Batch Start Date'], errors='coerce')

    # Calculate current week number based on today's date
    current_date = datetime.now()
    merged_data['Current Week'] = ((current_date - merged_data['Batch Start Date']).dt.days // 7) + 1

    # Add Current Week to Summary
    current_week_data = merged_data.groupby('Batch Name')['Current Week'].first().reset_index()

    # Step 8: Generate Summary View
    summary_view = merged_data.groupby('Batch Name').agg({
        'Batch Start Date': 'first',  # Use the first occurrence for Batch Start Date
        'Average Consumption_x': 'mean',  # Average Consumption from Sheet3
        'Active Participation': 'mean',  # Combined Active Participation from both sheets
        'Batch Health (Consumption)': 'mean',  # Batch Health from Sheet3
        'Average Live Participation_x': 'mean',  # Average Live Participation from Sheet4
        'Batch Health (Live Participation)': 'mean'  # Batch Health from Sheet4
    }).reset_index()

    # Merge Latest Week and Current Week with Summary View
    summary_view = pd.merge(summary_view, latest_week_data, on='Batch Name', how='left')
    summary_view = pd.merge(summary_view, current_week_data, on='Batch Name', how='left')

    # Calculate Overall Batch Health
    summary_view['Overall Batch Health'] = (summary_view['Batch Health (Consumption)'] *
                                            summary_view['Batch Health (Live Participation)']) / 100

    # Reorder Columns: Place Overall Batch Health in Column H
    summary_view = summary_view[['Batch Name', 'Batch Start Date',
                                 'Average Consumption_x', 'Active Participation',
                                 'Batch Health (Consumption)', 'Average Live Participation_x',
                                 'Batch Health (Live Participation)', 'Overall Batch Health',
                                 'Latest Week', 'Current Week']]

    # Format Batch Start Date in the desired format
    summary_view['Batch Start Date'] = summary_view['Batch Start Date'].dt.strftime('%A, %B %d, %Y')

    # Round Numeric Columns in Summary View to 2 Decimal Places
    numeric_columns_summary = ['Average Consumption_x', 'Active Participation',
                                'Batch Health (Consumption)', 'Average Live Participation_x',
                                'Batch Health (Live Participation)', 'Overall Batch Health']
    summary_view.loc[:, numeric_columns_summary] = summary_view[numeric_columns_summary].round(2)

    # Rename columns for clarity in Summary View
    summary_view.rename(columns={
        'Average Consumption_x': 'Avg Consumption',
        'Active Participation': 'Avg Active Participation',
        'Batch Health (Consumption)': 'Avg Batch Health (Consumption)',
        'Average Live Participation_x': 'Avg Live Participation',
        'Batch Health (Live Participation)': 'Avg Batch Health (Live Participation)'
    }, inplace=True)

    # Step 9: Generate Detailed View
    detailed_view = merged_data[['Batch Name', 'Week Number', 'Average Consumption_x',
                                 'Active Participation', 'Batch Health (Consumption)',
                                 'Average Live Participation_x', 'Batch Health (Live Participation)']]

    # Rename columns for clarity in Detailed View
    detailed_view = detailed_view.rename(columns={
        'Average Consumption_x': 'Avg Consumption',
        'Active Participation': 'Avg Active Participation',
        'Batch Health (Consumption)': 'Avg Batch Health (Consumption)',
        'Average Live Participation_x': 'Avg Live Participation',
        'Batch Health (Live Participation)': 'Avg Batch Health (Live Participation)'
    })

    # Round Numeric Columns in Detailed View to 2 Decimal Places
    numeric_columns_detailed = ['Avg Consumption', 'Avg Active Participation',
                                'Avg Batch Health (Consumption)', 'Avg Live Participation',
                                'Avg Batch Health (Live Participation)']
    detailed_view.loc[:, numeric_columns_detailed] = detailed_view[numeric_columns_detailed].round(2)

    # Display Results
    st.subheader("Summary View")
    st.dataframe(summary_view)

    st.subheader("Detailed View")
    st.dataframe(detailed_view)

    # Download Links
    st.download_button("Download Summary View as CSV", summary_view.to_csv(index=False), file_name="Summary_View.csv")
    st.download_button("Download Detailed View as CSV", detailed_view.to_csv(index=False), file_name="Detailed_View.csv")
