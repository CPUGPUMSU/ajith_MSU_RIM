import pandas as pd
import streamlit as st
from io import BytesIO

# Function to calculate adjustment factors
def calculate_adjustment_factors(distribution, survey_counts):
    dist_series = pd.Series(distribution, index=distribution.keys())
    factors = dist_series / survey_counts
    factors.fillna(0, inplace=True)
    factors.replace([float('inf'), -float('inf')], 0, inplace=True)
    return factors

# RIM weighting function
def apply_rim_weighting(df, distributions, columns):
    df['weight'] = 1
    for _ in range(10):
        for col, dist in zip(columns, distributions):
            survey_dist = df.groupby(col)['weight'].sum() / df['weight'].sum()
            factors = calculate_adjustment_factors(dist, survey_dist)
            df['weight'] *= df[col].map(factors).fillna(1)
    return df

# Function for normalizing weights
def normalize_weights(df):
    df['weight'] *= len(df) / df['weight'].sum()
    return df

# Streamlit App
def main():
    st.title("RIM Weighting Application")

    # File Upload
    uploaded_file = st.file_uploader("Choose a file to upload", type=['xlsx', 'xls', 'csv'])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Display DataFrame
        if st.checkbox('Show raw data'):
            st.write(df)

        # Column Selection
        st.subheader("Select Columns for RIM Weighting")
        all_columns = df.columns.tolist()
        selected_columns = st.multiselect("Choose columns", all_columns)

        # Process user inputs for categories and ratios
        distributions = []
        for col in selected_columns:
            st.subheader(f"Values in {col}")
            unique_values = df[col].unique()
            values_to_keep = []
            ratios = []
            for val in unique_values:
                keep_value = st.checkbox(f"Keep '{val}' in {col}", key=f"{col}_{val}")
                if keep_value:
                    values_to_keep.append(val)
                    ratio = st.number_input(f"Enter the ratio for '{val}' in {col}:", min_value=0.0, max_value=1.0, step=0.01, key=f"ratio_{col}_{val}")
                    ratios.append(ratio)

            if values_to_keep:
                # Calculate and display 'Others' ratio
                sum_of_ratios = sum(ratios)
                others_ratio = 1 - sum_of_ratios
                st.write(f"'Others' ratio for {col}: {others_ratio:.2f}")
                if sum_of_ratios < 1:
                    dist = {value: ratio for value, ratio in zip(values_to_keep, ratios)}
                    dist['Others'] = others_ratio
                    distributions.append(dist)
                else:
                    st.error("The sum of ratios for selected values exceeds 1. Please adjust the ratios.")

                # Update DataFrame based on selected values
                df[col] = df[col].apply(lambda x: x if x in values_to_keep else 'Others')

        if st.button("Apply RIM Weighting"):
            rim_weighted_df = apply_rim_weighting(df, distributions, selected_columns)
            rim_weighted_df = normalize_weights(rim_weighted_df)
            st.subheader("RIM-Weighted Data")
            st.write(rim_weighted_df)
            st.download_button(
                label="Download RIM-Weighted Data as Excel",
                data=to_excel(rim_weighted_df),
                file_name="rim_weighted_data.xlsx",
                mime="application/vnd.ms-excel"
            )

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

if __name__ == "__main__":
    main()
