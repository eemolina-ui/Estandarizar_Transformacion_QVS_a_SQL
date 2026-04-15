"""
Function registry and schemas for data analysis operations.
"""
import inspect
from typing import Dict, List, Callable, Any, Optional, Union

class FunctionRegistry:
    """Registry for available functions with metadata."""
    
    def __init__(self):
        """Initialize an empty function registry."""
        self.functions = {}
    
    def register(self, 
                 func: Callable, 
                 description: str = None, 
                 parameters: Dict = None, 
                 returns: Dict = None):
        """
        Register a function with its schema.
        
        Args:
            func (Callable): The function to register
            description (str, optional): Description of the function
            parameters (Dict, optional): Parameters schema
            returns (Dict, optional): Return value schema
        """
        func_name = func.__name__
        
        # Get function signature and docstring
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        
        # Build schema from function properties if not provided
        if description is None:
            description = doc.split("\n")[0] if doc else f"Function {func_name}"
            
        if parameters is None:
            parameters = {}
            for name, param in sig.parameters.items():
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
                parameters[name] = {
                    "type": str(param_type).replace("<class '", "").replace("'>", ""),
                    "description": "",
                    "required": param.default == inspect.Parameter.empty
                }
        
        if returns is None:
            return_type = sig.return_annotation if sig.return_annotation != inspect.Signature.empty else None
            returns = {
                "type": str(return_type).replace("<class '", "").replace("'>", ""),
                "description": ""
            }
        
        # Store function and schema
        self.functions[func_name] = {
            "function": func,
            "description": description,
            "parameters": parameters,
            "returns": returns
        }
    
    def get_function(self, name: str) -> Callable:
        """
        Get a registered function by name.
        
        Args:
            name (str): Function name
            
        Returns:
            Callable: The registered function
            
        Raises:
            ValueError: If function is not found
        """
        if name not in self.functions:
            raise ValueError(f"Function '{name}' not found in registry")
        return self.functions[name]["function"]
    
    def get_schema(self, name: str = None) -> Dict:
        """
        Get schema for a function or all functions.
        
        Args:
            name (str, optional): Function name. If None, returns all schemas.
            
        Returns:
            Dict: Function schema(s)
            
        Raises:
            ValueError: If specified function is not found
        """
        if name is not None:
            if name not in self.functions:
                raise ValueError(f"Function '{name}' not found in registry")
            return {k: v for k, v in self.functions[name].items() if k != "function"}
        
        return {
            name: {k: v for k, v in schema.items() if k != "function"} 
            for name, schema in self.functions.items()
        }

    def get_function_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all registered functions.
        
        Returns:
            Dict[str, str]: Dictionary mapping function names to descriptions
        """
        return {name: schema["description"] for name, schema in self.functions.items()}

def register_default_functions(registry: FunctionRegistry) -> None:
    """
    Register default functions with the registry.
    
    Args:
        registry (FunctionRegistry): Function registry instance
    """
    # Import the standalone forecast function
    from ..forecasting.forecast_client import generate_forecast
    
    # Register the forecast function
    registry.register(
        generate_forecast,
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
            },
            "forecast_api_url": {
                "type": "str",
                "description": "URL for the forecast API. If None, uses environment variable.",
                "required": False,
                "default": None
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