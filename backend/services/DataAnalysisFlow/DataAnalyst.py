"""
Enhanced data analysis workflow leveraging LLMs for planning,
code generation, and result presentation with token tracking.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import json
import io
import base64
import ast
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union, Any, Optional

# Import custom modules
from .prompts import PromptTemplates
from .utils.bedrock_helpers import handle_bedrock_conversation, parse_llm_response
from .utils.function_schemas import FunctionRegistry, register_default_functions
from .forecasting.forecast_client import ForecastClient

class DataAnalysisFlow:
    """
    A comprehensive data analysis workflow that leverages LLMs for planning,
    code generation, and result presentation with token usage tracking.
    """
    
    def __init__(
        self, 
        llm_client,
        bedrock_model_id: str,
        data_directory: str = "./data",
        forecast_api_url: str = None,
        forecast_api_key: str = None,
        style_config: Dict = None,
        custom_functions: List[Dict] = None,
        logger: logging.Logger = None,
        track_tokens: bool = True
    ):
        """
        Initialize the data analysis flow.
        
        Args:
            llm_client: The LLM client (e.g., Bedrock)
            bedrock_model_id (str): Model ID for the LLM
            data_directory (str): Directory for data files
            forecast_api_url (str, optional): URL for forecast API
            forecast_api_key (str, optional): API key for forecast API
            style_config (Dict, optional): Configuration for visual styles
            custom_functions (List[Dict], optional): Custom functions to register
            logger (logging.Logger, optional): Logger instance
            track_tokens (bool, optional): Whether to track token usage
        """
        self.data_directory = Path(data_directory)
        self.bedrock_model_id = bedrock_model_id
        self.llm_client = llm_client
        self.style_config = style_config or {}
        self.track_tokens = track_tokens
        
        # Setup logging
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize prompt templates with style config
        self.prompt_templates = PromptTemplates(style_config)
        
        # Initialize function registry and register default functions
        self.function_registry = FunctionRegistry()
        register_default_functions(self.function_registry)
        
        # Register custom functions if provided
        if custom_functions:
            for func_dict in custom_functions:
                self.function_registry.register(
                    func_dict["function"],
                    func_dict.get("description"),
                    func_dict.get("parameters"),
                    func_dict.get("returns")
                )
        
        # Initialize forecast client if URL is provided
        self.forecast_client = None
        if forecast_api_url:
            self.forecast_client = ForecastClient(forecast_api_url, forecast_api_key)
            self._register_forecast_functions()
        
        # Scan available datasets
        self.available_datasets = self._scan_datasets()
        
        # Define the safe execution environment
        self.safe_globals = {
            'pd': pd,
            'np': np,
            'plt': plt,
            'sns': sns,
            'io': io,
            'base64': base64
        }
        
        # Add registered functions to safe_globals
        for func_name, func_info in self.function_registry.functions.items():
            self.safe_globals[func_name] = func_info["function"]
        
        # Initialize token tracking
        self.token_usage = {
            "planning": {"input_tokens": 0, "output_tokens": 0},
            "dataset_identification": {"input_tokens": 0, "output_tokens": 0},
            "code_generation": {"input_tokens": 0, "output_tokens": 0},
            "code_correction": {"input_tokens": 0, "output_tokens": 0},
            "total": {"input_tokens": 0, "output_tokens": 0}
        }
    
    def _register_forecast_functions(self):
        """Register forecast client methods to the function registry."""
        if not self.forecast_client:
            return
        
        # Import the standalone forecast function
        from .forecasting.forecast_client import generate_forecast
        
        # Create a wrapper that uses this instance's forecast client URL
        def generate_forecast_wrapper(data, target_column, date_column=None, prediction_length=30):
            """Wrapper for generate_forecast that uses the current forecast client URL"""
            return generate_forecast(
                data=data,
                target_column=target_column,
                date_column=date_column,
                prediction_length=prediction_length,
                forecast_api_url=self.forecast_client.base_url
            )
        
        # Register the wrapper function
        self.function_registry.register(
            generate_forecast_wrapper,
            description="Generate time series forecasts and extend the dataframe with predicted values",
            parameters={
                "data": {
                    "type": "pd.DataFrame",
                    "description": "DataFrame containing time series data",
                    "required": True
                },
                "target_column": {
                    "type": "str",
                    "description": "Name of the column to forecast",
                    "required": True
                },
                "date_column": {
                    "type": "str",
                    "description": "Name of the date/time column. If None, first column is used.",
                    "required": False,
                    "default": None
                },
                "prediction_length": {
                    "type": "int",
                    "description": "Number of periods to forecast",
                    "required": False,
                    "default": 30
                }
            },
            returns={
                "type": "pd.DataFrame",
                "description": """Extended DataFrame with forecast values and confidence intervals. \
                The columns in the resulting dataframe are: \
                target_column:str (the same name as the input, with the forecasted values), \
                date_column:str (same name as the input, with the forecasted dates), \
                future_assigned:boolean (whether the value is forecasted or not), \
                lower_quantile:float (the lower quantile of the forecasted values), \
                upper_quantile:float (the upper quantile of the forecasted values)\
                """
            }
        )
    
    def _scan_datasets(self) -> Dict[str, Dict]:
        """
        Scan the data directory and catalog the available datasets.
        
        Returns:
            Dict[str, Dict]: Dictionary with dataset name and metadata
        """
        datasets = {}
        for file in self.data_directory.glob("*.csv"):
            try:
                # Read the DataFrame to get additional information
                df = pd.read_csv(str(file))
                # Create a more readable dataset summary
                datasets[file.stem] = {
                    'path': str(file),
                    'shape': df.shape,
                    'dtypes': df.dtypes.apply(lambda x: x.name).to_dict(),
                    'columns': df.columns.tolist(),
                    'head': df.head(4).to_dict()
                }
                self.logger.info(f"Scanned dataset: {file.stem} with shape {df.shape}")
            except Exception as e:
                self.logger.warning(f"Error scanning dataset {file}: {str(e)}")
        return datasets
    
    def _update_token_usage(self, category: str, token_counts: Dict[str, int]):
        """
        Update token usage tracking for a specific category.
        
        Args:
            category (str): Category of the token usage (planning, code_generation, etc.)
            token_counts (Dict[str, int]): Token counts to add to the category
        """
        if not self.track_tokens or not token_counts:
            return
            
        # Update the specific category
        if category in self.token_usage:
            self.token_usage[category]["input_tokens"] += token_counts.get("input_tokens", 0)
            self.token_usage[category]["output_tokens"] += token_counts.get("output_tokens", 0)
        
        # Update total tokens
        self.token_usage["total"]["input_tokens"] += token_counts.get("input_tokens", 0)
        self.token_usage["total"]["output_tokens"] += token_counts.get("output_tokens", 0)
        
        self.logger.info(f"Updated token usage for {category}: {token_counts}")
        self.logger.info(f"Total token usage so far: {self.token_usage['total']}")
    
    def _plan_analysis(self, question: str, additional_context: str = None) -> Dict:
        """
        Plan the analysis approach based on the question.
        
        Args:
            question (str): User question
            additional_context (str, optional): Additional context for planning
            
        Returns:
            Dict: Planning result with required datasets, functions, and approach
        """
        # Get available function schemas
        available_functions = self.function_registry.get_schema()
        
        # Create planning prompt
        planning_prompt = self.prompt_templates.get_planning_prompt(
            question=question,
            available_functions=available_functions,
            available_datasets=self.available_datasets,
            additional_context=additional_context
        )
        
        # Query the model for a plan
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": question}
                ]
            }
        ]
        
        response = handle_bedrock_conversation(
            bedrock_client=self.llm_client,
            model_id=self.bedrock_model_id,
            messages=messages,
            system_prompts=planning_prompt,
            track_tokens=self.track_tokens
        )
        
        # Update token usage tracking for planning
        if self.track_tokens and "token_counts" in response:
            self._update_token_usage("planning", response["token_counts"])
        
        # Parse the planning response
        try:
            plan_text = response["output"]["message"]["content"][0]["text"]
            plan = json.loads(plan_text)
            self.logger.info(f"Generated plan for question: {question}")
            return plan
        except Exception as e:
            self.logger.error(f"Error parsing planning response: {str(e)}")
            # Return a minimal default plan
            return {
                "plan": f"Analyze data to answer: {question}",
                "required_functions": [],
                "required_datasets": self._identify_required_datasets(question),
                "expected_outputs": {
                    "data": "Processed data relevant to the question",
                    "visualizations": ["Appropriate visualizations"],
                    "insights": ["Key findings from the data"]
                }
            }
    
    def _identify_required_datasets(self, question: str, additional_context: str = None) -> List[str]:
        """
        Identify datasets required to answer the question.
        
        Args:
            question (str): User question
            additional_context (str, optional): Additional context about the data
            
        Returns:
            List[str]: List of required dataset names
        """
        # Create dataset identification prompt
        dataset_prompt = self.prompt_templates.get_dataset_identification_prompt(
            datasets=list(self.available_datasets.keys()),
            datasets_info=self.available_datasets,
            additional_context=additional_context
        )
        
        # Query the model
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": question}
                ]
            }
        ]
        
        response = handle_bedrock_conversation(
            bedrock_client=self.llm_client,
            model_id=self.bedrock_model_id,
            messages=messages,
            system_prompts=dataset_prompt,
            track_tokens=self.track_tokens
        )
        
        # Update token usage tracking for dataset identification
        if self.track_tokens and "token_counts" in response:
            self._update_token_usage("dataset_identification", response["token_counts"])
        
        # Parse the response
        try:
            datasets_text = response["output"]["message"]["content"][0]["text"]
            required_datasets = json.loads(datasets_text)["datasets_required"]
            self.logger.info(f"Identified required datasets: {required_datasets}")
            return required_datasets
        except Exception as e:
            self.logger.error(f"Error identifying required datasets: {str(e)}")
            return []
    
    def _load_datasets(self, dataset_names: List[str]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Dict]]:
        """
        Load the required datasets into DataFrames.
        
        Args:
            dataset_names (List[str]): Names of datasets to load
            
        Returns:
            Tuple[Dict[str, pd.DataFrame], Dict[str, Dict]]: 
                Loaded DataFrames and their metadata
        """
        loaded_data = {}
        info_loaded_data = {}
        
        for name in dataset_names:
            if name in self.available_datasets:
                try:
                    df = pd.read_csv(self.available_datasets[name]['path'])
                    loaded_data[name] = df
                    info_loaded_data[name] = {
                    'shape': df.shape,
                    'dtypes': df.dtypes.apply(lambda x: x.name).to_dict(),
                    'columns': df.columns.tolist(),
                    'head': df.head(4).to_dict()
                }
                    self.logger.info(f"Loaded dataset: {name} with shape {df.shape}")
                except Exception as e:
                    self.logger.error(f"Error loading dataset {name}: {str(e)}")
        
        return loaded_data, info_loaded_data
    
    def _generate_code(self, 
                     question: str, 
                     plan: Dict, 
                     loaded_data_info: Dict,
                     style_override: Dict = None) -> str:
        """
        Generate code to implement the analysis plan.
        
        Args:
            question (str): User question
            plan (Dict): Analysis plan
            loaded_data_info (Dict): Information about loaded datasets
            style_override (Dict, optional): Override default style config
            
        Returns:
            str: Generated Python code
        """
        # Get function schemas for required functions
        function_schemas = {}
        self.logger.info(f"Getting function schemas for required functions: {plan.get('required_functions', [])}")
        for func_name in plan.get("required_functions", []):
            try:
                self.logger.info(f"Getting schema for function: {func_name}")
                self.logger.info(f"Schema: {self.function_registry.get_schema(func_name)}")
                function_schemas[func_name] = self.function_registry.get_schema(func_name)
            except ValueError:
                self.logger.warning(f"Required function '{func_name}' not found in registry")
        
        # Create code generation prompt
        code_prompt = self.prompt_templates.get_code_generation_prompt(
            question=question,
            plan=plan,
            datasets_info=loaded_data_info,
            function_schemas=function_schemas,
            style_config=style_override or self.style_config
        )
        
        self.logger.info(f"Generated code generation prompt: {code_prompt}")
        # Query the model
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": question}
                ]
            }
        ]
        
        response = handle_bedrock_conversation(
            bedrock_client=self.llm_client,
            model_id=self.bedrock_model_id,
            messages=messages,
            system_prompts=code_prompt,
            track_tokens=self.track_tokens
        )
        
        # Update token usage tracking for code generation
        if self.track_tokens and "token_counts" in response:
            self._update_token_usage("code_generation", response["token_counts"])
        
        # Parse the code response
        code = parse_llm_response(response["output"]["message"]["content"][0]["text"])
        if code:
            self.logger.info("Successfully generated code")
        else:
            self.logger.error("Failed to parse generated code")
        
        return code
    
    def _correct_code(self, 
                    code: str, 
                    error: str, 
                    plan: Dict,
                    function_schemas: Dict,
                    question: str, 
                    loaded_data_info: Dict,
                    style_override: Dict = None) -> str:
        """
        Correct code that failed to execute.
        
        Args:
            code (str): Original code
            error (str): Error message
            question (str): User question
            loaded_data_info (Dict): Information about loaded datasets
            style_override (Dict, optional): Override default style config
            
        Returns:
            str: Corrected code
        """
        # Create code correction prompt
        correction_prompt = self.prompt_templates.get_code_correction_prompt(
            code=code,
            error=error,
            plan=plan,
            function_schemas=function_schemas,
            question=question,
            datasets_info=loaded_data_info,
            style_config=style_override or self.style_config
        )
        
        # Query the model
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": question}
                ]
            }
        ]
        
        response = handle_bedrock_conversation(
            bedrock_client=self.llm_client,
            model_id=self.bedrock_model_id,
            messages=messages,
            system_prompts=correction_prompt,
            track_tokens=self.track_tokens
        )
        
        # Update token usage tracking for code correction
        if self.track_tokens and "token_counts" in response:
            self._update_token_usage("code_correction", response["token_counts"])
        
        # Parse the corrected code
        corrected_code = parse_llm_response(response["output"]["message"]["content"][0]["text"])
        if corrected_code:
            self.logger.info("Successfully corrected code")
        else:
            self.logger.error("Failed to parse corrected code")
        
        return corrected_code
    
    def _execute_code(self, 
                    code: str, 
                    plan: Dict,
                    function_schemas: Dict,
                    local_vars: Dict, 
                    question: str, 
                    loaded_data_info: Dict,
                    style_override: Dict = None) -> Dict:
        """
        Execute the generated code and handle errors.
        
        Args:
            code (str): Code to execute
            local_vars (Dict): Local variables for execution
            question (str): User question
            loaded_data_info (Dict): Information about loaded datasets
            style_override (Dict, optional): Override default style config
            
        Returns:
            Dict: Execution result
        """
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Execute the code
                exec(code, self.safe_globals, local_vars)
                
                # Validate the result
                result = local_vars.get('result', None)
                if result is None:
                    raise ValueError("Code execution did not set 'result' variable")
                
                # Ensure result has the expected structure
                if not isinstance(result, dict):
                    raise ValueError("Result must be a dictionary")
                
                required_keys = ['text', 'data', 'images']
                for key in required_keys:
                    if key not in result:
                        result[key] = None if key != 'images' else []
                
                self.logger.info("Code executed successfully")
                return result
                
            except Exception as e:
                attempt += 1
                error_msg = str(e)
                self.logger.warning(f"Execution attempt {attempt} failed: {error_msg}")
                self.logger.info(f"Code that failed: {code}")
                if attempt < max_attempts:
                    # Try to correct the code
                    code = self._correct_code(
                        code, 
                        error_msg, 
                        plan,
                        function_schemas,
                        question, 
                        loaded_data_info,
                        style_override
                    )
                else:
                    # Return error information
                    return {
                        'text': f"Lo siento, no pude completar el análisis debido a un error: {error_msg}",
                        'data': None,
                        'images': [],
                        'error': error_msg
                    }
    
    def process_question(self, 
                        question: str, 
                        additional_context: str = None,
                        style_override: Dict = None) -> Dict:
        """
        Process a data analysis question and generate results.
        
        Args:
            question (str): User question
            additional_context (str, optional): Additional context for planning
            style_override (Dict, optional): Override default style config
            
        Returns:
            Dict: Analysis results including text, data, visualizations and token usage
        """
        self.logger.info(f"Processing question: {question}")
        
        # Reset token usage for this question
        if self.track_tokens:
            self.token_usage = {
                "planning": {"input_tokens": 0, "output_tokens": 0},
                "dataset_identification": {"input_tokens": 0, "output_tokens": 0},
                "code_generation": {"input_tokens": 0, "output_tokens": 0},
                "code_correction": {"input_tokens": 0, "output_tokens": 0},
                "total": {"input_tokens": 0, "output_tokens": 0}
            }
        
        try:
            # Plan the analysis
            plan = self._plan_analysis(question, additional_context)
            
            # Identify and load required datasets
            required_datasets = plan.get("required_datasets", [])
            if not required_datasets:
                required_datasets = self._identify_required_datasets(question, additional_context)
            
            loaded_data, loaded_data_info = self._load_datasets(required_datasets)
            
            # If no datasets were loaded but some were required, return an error
            if not loaded_data and required_datasets:
                result = {
                    'text': f"No pude encontrar los datasets necesarios: {', '.join(required_datasets)}",
                    'data': None,
                    'images': [],
                    'error': "Required datasets not found"
                }
                if self.track_tokens:
                    result['token_usage'] = self.token_usage
                return result
            
            # Prepare variables for code execution
            local_vars = {
                'data': loaded_data,
                'question': question,
                'result': None
            }
            
            # Generate code based on the plan
            code = self._generate_code(question, plan, loaded_data_info, style_override)
            
            if not code:
                result = {
                    'text': "Lo siento, no pude generar el código para analizar los datos.",
                    'data': None,
                    'images': [],
                    'error': "Code generation failed"
                }
                if self.track_tokens:
                    result['token_usage'] = self.token_usage
                return result
            
            # Execute the code and get results
            result = self._execute_code(code, plan, self.function_registry.get_schema(), local_vars, question, loaded_data_info, style_override)
            
            if result.get('data') is not None:
                # Handle list of dictionaries
                def convert_value(v):
                    """Convierte valores no serializables a JSON-friendly"""
                    if pd.isna(v):  # Convertir NaN a None
                        return None
                    if isinstance(v, (pd.Timestamp, datetime)):  # Pandas Timestamp y datetime estándar
                        return v.isoformat()
                    if isinstance(v, np.datetime64):  # Convertir numpy.datetime64 a string ISO
                        return pd.Timestamp(v).isoformat()
                    if hasattr(v, 'isoformat'):  # Otros objetos con método isoformat()
                        return v.isoformat()
                    if isinstance(v, np.ndarray):  # Convertir arrays de NumPy a listas
                        return v.tolist()
                    if isinstance(v, (np.integer, np.floating, np.bool_)):  # Convertir NumPy números/bools a tipos nativos
                        return v.item()  # Devuelve un int, float o bool estándar de Python
                    return v  # Si no necesita conversión, lo deja igual

                if isinstance(result['data'], list):
                    self.logger.info("Processing list of dictionaries: {}".format(result['data']))
                    result['data'] = [
                        {k: convert_value(v) for k, v in item.items()} for item in result['data']
                    ]

                    self.logger.info("Processed list of dictionaries: {}".format(result['data']))
            # Enhance the result with metadata
            result.update({
                'required_datasets': required_datasets,
                'generated_code': code,
                'plan': plan.get('plan'),
                'loaded_datasets': [name for name in loaded_data]
            })
            
            # Add token usage to the result if tracking is enabled
            if self.track_tokens:
                result['token_usage'] = self.token_usage
            
            self.logger.info("Question processing completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing question: {str(e)}")
            result = {
                'text': f"Lo siento, ocurrió un error durante el análisis: {str(e)}",
                'data': None,
                'images': [],
                'error': str(e)
            }
            if self.track_tokens:
                result['token_usage'] = self.token_usage
            return result
    
    def update_style_config(self, new_style_config: Dict) -> None:
        """
        Update the style configuration.
        
        Args:
            new_style_config (Dict): New style configuration
        """
        self.style_config.update(new_style_config)
        # Update prompt templates with new style
        self.prompt_templates = PromptTemplates(self.style_config)
        self.logger.info("Updated style configuration")
    
    def register_custom_function(self, 
                               func, 
                               description=None, 
                               parameters=None, 
                               returns=None) -> None:
        """
        Register a custom function for use in analysis.
        
        Args:
            func: Function to register
            description (str, optional): Function description
            parameters (Dict, optional): Function parameters schema
            returns (Dict, optional): Function return value schema
        """
        self.function_registry.register(func, description, parameters, returns)
        # Update safe_globals with the new function
        self.safe_globals[func.__name__] = func
        self.logger.info(f"Registered custom function: {func.__name__}")
    
    def get_available_datasets(self) -> Dict[str, Dict]:
        """
        Get information about available datasets.
        
        Returns:
            Dict[str, Dict]: Dictionary with dataset information
        """
        return self.available_datasets
    
    def get_available_functions(self) -> Dict[str, Dict]:
        """
        Get information about available functions.
        
        Returns:
            Dict[str, Dict]: Dictionary with function information
        """
        return self.function_registry.get_schema()
    
    def get_token_usage(self) -> Dict[str, Dict[str, int]]:
        """
        Get the current token usage statistics.
        
        Returns:
            Dict[str, Dict[str, int]]: Dictionary with token usage by category
        """
        return self.token_usage
    
    def reload_datasets(self) -> None:
        """Reload the available datasets from the data directory."""
        self.available_datasets = self._scan_datasets()
        self.logger.info("Reloaded datasets from data directory")