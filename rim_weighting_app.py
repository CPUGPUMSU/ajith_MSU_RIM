import streamlit as st
import pandas as pd

# Function for proportions
def calculate_adjustment_factors(distribution, survey_counts, categories):
    adjustment_factors = {}
    for category in categories:
        actual_proportion = distribution.get(category, 0)
        survey_proportion = survey_counts.get(category, 0)
        if survey_proportion > 0:
            adjustment_factors[category] = actual_proportion / survey_proportion
        else:
            adjustment_factors[category] = 0
    return adjustment_factors

# RIM function
def apply_rim_weighting(df, distributions, columns):
    df['weight'] = 1
    for _ in range(10):  # Iteration count can be adjusted
        for col, dist in zip(columns, distributions):
            categories = dist.keys()
            survey_dist = df.groupby(col)['weight'].sum() / df['weight'].sum()
            factors = calculate_adjustment_factors(dist, survey_dist, categories)
            df['weight'] = df.apply(lambda row: row['weight'] * factors.get(row[col], 1), axis=1)
    return df

# Normalizing
def normalize_weights(df, original_count):
    total_weight = df['weight'].sum()
    normalization_factor = original_count / total_weight
    df['weight'] *= normalization_factor
    return df


st.title("RIM Weighting Application - MSU")


uploaded_file = st.file_uploader("Choose a file for RIM weighting")
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file,engine='openpyxl')
    st.write("Columns available for selection:")
    all_columns = df.columns

    
    selected_columns = st.multiselect("Select columns for RIM weighting:", all_columns)

    
    distributions = []
    for col in selected_columns:
        st.write(f"Unique values in {col}: ", df[col].unique())
        values_to_keep = st.multiselect(f"Select values to keep in {col}:", df[col].unique())
        
        
        ratios = []
        for value in values_to_keep + ['Others']:
            ratio = st.number_input(f"Enter ratio for {value} in {col}:", min_value=0.0, max_value=1.0, step=0.01, key=f"{col}_{value}")
            ratios.append(ratio)

        
        dist = {value: ratio for value, ratio in zip(values_to_keep + ['Others'], ratios)}
        distributions.append(dist)

        
        df[col] = df[col].apply(lambda x: x if x in values_to_keep else 'Others')

    if st.button("Apply RIM Weighting"):
        original_count = len(df)
        rim_weighted_df = apply_rim_weighting(df, distributions, selected_columns)
        rim_weighted_df = normalize_weights(rim_weighted_df, original_count)

        
        st.write("RIM-weighted data is ready for download.")
        st.download_button(label="Download Data",
                           data=rim_weighted_df.to_csv().encode('utf-8'),
                           file_name="rim_weighted_data.csv",
                           mime="text/csv")
