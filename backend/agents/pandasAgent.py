from langchain_openai import AzureChatOpenAI
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
import json
import re


class DataFrameManipulator:
    def __init__(self, llm: AzureChatOpenAI, df: pd.DataFrame, columns: Optional[List[str]]=None, date_format: Optional[str] = None):
        """
        Initialize the DataFrameManipulator.
        
        Args:
            llm: AzureChatOpenAI instance for code generation
            df: Input DataFrame to manipulate
        """
        self.df = df
        self.columns = columns
        self.date_format = date_format
        self.llm = llm
        self.code_prompt = """Given a DataFrame 'df' and this request: "{query}"

        Write Python code to perform the requested operation. The code should:
        1. Use 'df' as the input DataFrame name
        2. Store any modified DataFrame in 'result_df'
        3. Store any analysis results in 'analysis_result'
        4. Use only pandas operations
        5. DO NOT PERFORM PLOTS / VISUALIZATIONS (They will be performed based on the output of this code)
        6. DO NOT PERFORM FORECASTING (It will be performed based on the output of this code)
        7. DO NOT SET THE INDEX. The columns might be used for further analysis.

        Considerations: 
        - In the current version of pandas, to convert a column to datetime, you must add utc=True to the to_datetime function.
        - If you need to convert to datetime, it is convenient to use format='mixed'

        IMPORTANT: IF THE USER DO NOT REQUEST EXPLICITLY MODIFICATIONS OR PROCESSING, YOU MUST RETURN THE ORIGINAL DATAFRAME.
        IF THE USER DO NOT NEED TO MODIFY THE DATAFRAME, THE COMPLETE ROWS WILL BE USED FOR FURTHER ANALYSIS.
        The DataFrame has these columns: {columns}

        {date_format}

        Return response in this format:
        {{
            "CODE": "<your code here>",
            "RETURN_VARS": ["result_df"] or ["analysis_result"] or ["result_df", "analysis_result"]
        }}

        Example responses:

        For modification:
        {{
            "CODE": "result_df = df.copy()\\nresult_df['new_col'] = df['A'] + df['B']",
            "RETURN_VARS": ["result_df"]
        }}

        For analysis:
        {{
            "CODE": "analysis_result = df['A'].mean()",
            "RETURN_VARS": ["analysis_result"]
        }}

        For both:
        {{
            "CODE": "result_df = df.copy()\\nresult_df['new_col'] = df['A'] + df['B']\\nanalysis_result = result_df['new_col'].mean()",
            "RETURN_VARS": ["result_df", "analysis_result"]
        }}

        Your answer will be decoded with json.loads(), therefore you must start your response with '{{' and end with '}}'.
        """
    
    def infer_date_format(self, sample_date: str) -> str:
                    """
                    Infer the date format from a sample date string.
                    
                    Args:
                        sample_date: A string containing a date
                        
                    Returns:
                        str: The inferred date format string, or None if format cannot be determined
                    """
                    if '/' in sample_date:
                        if len(sample_date.split('/')) == 2:
                            return '%Y/%m'
                        else:
                            return '%Y/%m/%d'
                    elif '-' in sample_date:
                        if len(sample_date.split('-')) == 2:
                            return '%Y-%m'
                        else:
                            return '%Y-%m-%d'
                    return None
    
    def execute_and_return(self, code: str, return_vars: List[str]) -> Dict[str, Any]:
        """
        Execute code and return specified variables
        
        Args:
            code: String containing Python code to execute
            return_vars: List of variable names to return
            
        Returns:
            Dictionary containing the requested variables and their values
        """
        local_vars = {'df': self.df, 'pd': pd}
        
        try:
            exec(code, {'pd': pd}, local_vars)
            return {var: local_vars.get(var) for var in return_vars}
        except Exception as e:
            raise RuntimeError(f"Code execution failed: {str(e)}")

    def process_query(self, query: str) -> Tuple[str, Optional[pd.DataFrame], Optional[Any]]:
        """
        Process a natural language query to manipulate or analyze the DataFrame
        
        Args:
            query: Natural language query describing the desired operation
            
        Returns:
            Tuple containing:
            - Message describing the operation result
            - Modified DataFrame (if applicable)
            - Analysis result (if applicable)
        """
        try:
            # Get response from LLM

            if self.columns is None:
                self.columns = self.df.columns.tolist()
            
            if self.date_format is None:
                self.date_format = self.infer_date_format(self.df.iloc[0, 0])

            response = self.llm.invoke(
                self.code_prompt.format(
                    query=query, 
                    columns=self.columns,
                    date_format=self.date_format if self.date_format is not None else ""
                )
            )
            
            # Parse the response
            try:
                print('LLM response:', response.content)
                instructions = json.loads(response.content)
                for key in instructions:
                    print(key,': ', instructions[key])
            except json.JSONDecodeError:
                try:
                    instructions = re.sub(r"```json.*?```", "", response.content)
                    instructions = json.loads(instructions)
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON response from LLM")
                
            if "CODE" not in instructions or "RETURN_VARS" not in instructions:
                raise ValueError("Response missing required fields")
                
            # Execute the code
            results = self.execute_and_return(
                instructions["CODE"],
                instructions["RETURN_VARS"]
            )
            
            # Process results
            result_df = results.get('result_df')
            analysis_result = results.get('analysis_result')
            
            # Update internal DataFrame if modified
            if result_df is not None and isinstance(result_df, pd.DataFrame):
                self.df = result_df
                
            # Construct return message
            message_parts = []
            if result_df is not None:
                message_parts.append("DataFrame modified")
            if analysis_result is not None:
                message_parts.append(f"Analysis result: {analysis_result}")
                
            return (
                " and ".join(message_parts),
                result_df,
                analysis_result
            )
            
        except Exception as e:
            return f"Error processing query: {str(e)}", None, None