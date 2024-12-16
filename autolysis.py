import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import json
import subprocess

def install_requirements():
    """Install required dependencies inline."""
    required_libraries = ['pandas', 'seaborn', 'matplotlib', 'requests']
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + required_libraries)

def query_llm(messages, model="gpt-4o-mini"):
    """ 
    Send a request to the AI Proxy for chat completions.

    Args:
        messages (list): A list of message dictionaries for the chat model.
        model (str): The model to use (default is "gpt-4o-mini").

    Returns:
        str: The response content from the model.
    """
    # Get the API token and endpoint from the environment
    api_key = os.getenv("AIPROXY_TOKEN")
    endpoint = os.getenv("AIPROXY_ENDPOINT", "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions")

    if not api_key:
        raise ValueError("API key not found. Set the AIPROXY_TOKEN environment variable.")

    # Define headers and payload
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": model,
        "messages": messages
    }

    # Make the request
    response = requests.post(endpoint, headers=headers, json=json_data)

    # Handle the response
    if response.status_code == 200:
        try:
            json_output = response.json()
            return json_output['choices'][0]['message']['content']
        except (KeyError, json.JSONDecodeError) as e:
            raise Exception(f"Unexpected response format: {response.text}")
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

def create_output_directory(output_dir):
    """Create the output directory if it does not exist."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

def data_cleanup_and_preprocessing(dataframe):
    """
    Cleans and preprocesses the data.
    - Removes missing values.
    - Normalizes numeric columns.
    """
    # Select numeric columns only
    numeric_dataframe = dataframe.select_dtypes(include=["number"])
    
    # Fill missing numeric values with column means
    numeric_dataframe = numeric_dataframe.fillna(numeric_dataframe.mean())

    # Normalize numeric columns to a 0-1 scale
    numeric_dataframe = (numeric_dataframe - numeric_dataframe.min()) / (numeric_dataframe.max() - numeric_dataframe.min())
    
    # Add back non-numeric columns to maintain the original structure
    non_numeric_dataframe = dataframe.select_dtypes(exclude=["number"])
    dataframe = pd.concat([numeric_dataframe, non_numeric_dataframe], axis=1)
    
    return dataframe


def generate_generic_visualizations(dataframe, output_dir):
    """Generate and save generic visualizations."""
    # Filter to include only numeric columns for correlation
    numeric_dataframe = dataframe.select_dtypes(include=["number"])
    
    if not numeric_dataframe.empty:
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric_dataframe.corr(), annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
        plt.title("Correlation Heatmap")
        heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
        plt.savefig(heatmap_path)
        plt.close()
    else:
        print("No numeric columns available for correlation analysis.")

def generate_final_narrative(insights):
    """Generate a fictional, interesting story that includes data analysis insights in a creative way."""
    final_prompt = f"""
    Create a fictional, engaging, and interesting story in which the following data analysis insights are incorporated throughout the narrative. The story should flow naturally, integrating these insights in a creative and compelling manner. The insights are:

    1. **Overview**: {insights['overview']}
    2. **Missing Values**: {insights['missing_values']}
    3. **Correlation Analysis**: {insights['correlation']}
    4. **Outlier Analysis**: {insights['outliers']}

    As you build the story, include the following parts:
    - Introduce a fictional setting, character(s), or scenario where the dataset plays a role.
    - As the story progresses, gradually reveal the key dataset insights (e.g., dataset overview, missing values, correlations, outliers) as part of the plot.
    - Use these insights as part of the problem-solving process, challenges, or discoveries the characters face in the story.
    - End the story with a conclusion that ties everything together, using the insights as part of the final takeaway or moral of the story.

    The story should be engaging, creative, and narrative-driven while still including all the key insights from the dataset analysis. Ensure that the insights are organically woven into the plot.
    """
    narrative = query_llm([{"role": "user", "content": final_prompt}])
    return narrative

def generate_analysis_insights(dataframe, structured_results):
    """Generate insights using the LLM based on structured results."""
    prompts = {
        "overview": f"Provide an overview of the dataset with columns: {list(dataframe.columns)}. Include numerical and categorical column insights.",
        "missing_values": f"Narrate a story about the percentage of missing and unique values in each column: {structured_results['missing_values']}",
        "correlation": f"Based on the correlation analysis: {structured_results['correlation']}, identify key insights about strongly correlated columns.",
        "outliers": f"Highlight the columns with the most outliers based on the following analysis: {structured_results['outliers']}"
    }
    insights = {key: query_llm([{"role": "user", "content": prompt}]) for key, prompt in prompts.items()}
    return insights

def generate_readme_part1(output_dir, insights, structured_results):
    """Generate a formal, fact-based story in markdown format."""
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w") as readme_file:
        readme_file.write("# Dataset Analysis Report\n\n")
        
        # Section 1: Dataset Overview
        readme_file.write("## Dataset Overview\n")
        readme_file.write(insights["overview"] + "\n\n")
        
        # Section 2: Missing Values
        readme_file.write("## Missing Values\n")
        readme_file.write(insights["missing_values"] + "\n\n")
        
        # Section 3: Correlation Analysis
        readme_file.write("## Correlation Analysis\n")
        readme_file.write(insights["correlation"] + "\n\n")
        
        # Section 4: Outlier Analysis
        readme_file.write("## Outlier Analysis\n")
        # Highlight top 5 outlier columns and their data
        outlier_data = sorted(structured_results['outliers'].items(), key=lambda x: x[1], reverse=True)[:5]
        outlier_info = "\n".join([f"{col}: {count} outliers" for col, count in outlier_data])
        readme_file.write(f"Top 5 columns with the most outliers:\n{outlier_info}\n\n")

        # Conclusion section
        readme_file.write("## Conclusion\n")
        readme_file.write("This report provides a comprehensive overview and insights derived from the dataset.\n")

def generate_readme_part2(output_dir, insights):
    """Generate a elaborate,creative story that ties everything together."""
    story_prompt = f"""
    Write a creative, fictional story of about 400 words that ties together the following key insights from the dataset:
    1. The dataset includes these columns: {list(insights['overview'])}.
    2. Missing values are present in the following columns: {insights['missing_values']}.
    3. The most relevant correlations, both positive and negative, are: {insights['correlation']}.
    4. The top 5 columns with the most outliers are: {insights['outliers']}.

    The story should be no longer than 400 words and should creatively present these findings in a fun and engaging way while still being informative and factual. Ensure that all key details are included.
    """
    # Generate the story from the LLM
    story = query_llm([{"role": "user", "content": story_prompt}])
    
    # Append it to the README
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "a") as readme_file:
        readme_file.write("\n## Cool Story Which Ties It Up Together\n")
        readme_file.write(story + "\n")

def main():
    import sys
    
    install_requirements()
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' does not exist.")
        sys.exit(1)

    output_dir = os.path.splitext(csv_file)[0]
    create_output_directory(output_dir)

    # Specify the encoding explicitly
    try:
        dataframe = pd.read_csv(csv_file, encoding='ISO-8859-1')
    except UnicodeDecodeError as e:
        print(f"Error reading CSV file with encoding 'ISO-8859-1': {e}")
        sys.exit(1)

    dataframe = data_cleanup_and_preprocessing(dataframe)

    structured_results = {
        "missing_values": dataframe.isnull().mean().to_dict(),
        "correlation": dataframe.select_dtypes(include=['number']).corr().to_dict(),
        "outliers": {col: ((dataframe[col] < (dataframe[col].mean() - 3 * dataframe[col].std())) | \
                            (dataframe[col] > (dataframe[col].mean() + 3 * dataframe[col].std()))).sum() \
                      for col in dataframe.select_dtypes(include=["number"]).columns}
    }

    generate_generic_visualizations(dataframe, output_dir)

    insights = generate_analysis_insights(dataframe, structured_results)

    # Generate first part of the README (formal story)
    generate_readme_part1(output_dir, insights, structured_results)

    # Generate second part of the README (creative story)
    generate_readme_part2(output_dir, insights)

    print(f"Analysis complete. Outputs saved in directory: {output_dir}")

if __name__ == "__main__":
    main()