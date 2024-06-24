import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import anthropic

# Set up the Anthropic client
client = anthropic.Anthropic(api_key=st.secrets['api_key'])

def get_visualization_suggestions(df):
    prompt = f"""
    Given the following DataFrame information:
    
    Columns and data types:
    {df.dtypes}
    
    Sample data:
    {df.head().to_string()}
    
    Suggest 5-10 insightful visualizations for this data. For each visualization, provide:
    1. The type of chart
    2. The columns to use
    3. Any aggregations or transformations needed
    4. A brief explanation of the insight it might provide
    
    Format your response as a Python list of dictionaries, where each dictionary represents a visualization suggestion.
    """
    
    response = client.completions.create(
        model="claude-3-sonnet-20240229",
        prompt=prompt,
        max_tokens_to_sample=2000,
    )
    
    return eval(response.completion)

def create_visualization(df, viz_info):
    chart_type = viz_info['chart_type']
    columns = viz_info['columns']
    aggregation = viz_info.get('aggregation', None)
    
    if aggregation:
        df_agg = df.groupby(columns[0])[columns[1]].agg(aggregation).reset_index()
        fig = getattr(px, chart_type)(df_agg, x=columns[0], y=columns[1], title=viz_info['explanation'])
    else:
        fig = getattr(px, chart_type)(df, x=columns[0], y=columns[1], title=viz_info['explanation'])
    
    return fig

st.title("Data Visualization Dashboard")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Read CSV file
        df = pd.read_csv(uploaded_file)
        
        # Display basic information about the dataset
        st.write("Dataset Information:")
        st.write(f"Number of rows: {df.shape[0]}")
        st.write(f"Number of columns: {df.shape[1]}")
        
        # Extract column information
        column_info = []
        for column in df.columns:
            dtype = str(df[column].dtype)
            distinct_values = df[column].nunique()
            if distinct_values < 10:
                unique_values = df[column].unique().tolist()
            else:
                unique_values = None
            column_info.append({
                'name': column,
                'dtype': dtype,
                'distinct_values': distinct_values,
                'unique_values': unique_values
            })
        
        # Get visualization suggestions from Claude API
        viz_suggestions = get_visualization_suggestions(df)
        
        # Create filters
        st.sidebar.header("Filters")
        for col in column_info:
            if col['distinct_values'] < 10:
                selected_values = st.sidebar.multiselect(f"Select {col['name']}", options=col['unique_values'], default=col['unique_values'])
                df = df[df[col['name']].isin(selected_values)]
        
        # Create visualizations
        for viz in viz_suggestions:
            fig = create_visualization(df, viz)
            st.plotly_chart(fig)
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Please make sure you've uploaded a valid CSV file.")
else:
    st.write("Please upload a CSV file to begin.")
