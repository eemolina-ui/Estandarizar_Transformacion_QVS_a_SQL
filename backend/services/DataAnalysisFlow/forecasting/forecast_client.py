"""
Client for interacting with external forecasting services.
"""
import requests
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

class ForecastClient:
    """Client for accessing forecasting API endpoints."""
    
    def __init__(self, base_url: str, api_key: str = None):
        """
        Initialize the forecast client.
        
        Args:
            base_url (str): Base URL for the forecasting API
            api_key (str, optional): API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["X-API-Key"] = api_key
        
        # Store last forecast result
        self.last_forecast = None
    
    @staticmethod
    def infer_date_format(date_str):
        """
        Infer the date format from a string representation.
        
        Args:
            date_str (str): String representation of a date
            
        Returns:
            str: Inferred date format
        """
        formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y',
            '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
            '%Y%m%d', '%d%m%Y', '%m%d%Y',
            '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S', '%m-%d-%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                pd.to_datetime(date_str, format=fmt)
                return fmt
            except (ValueError, TypeError):
                continue
        
        return None  # Default to None if no format matches
    
    def forecast(
        self, 
        data: pd.DataFrame, 
        target_column: str, 
        date_column: str = None,
        prediction_length: int = 30,
        return_extended_df: bool = True
    ) -> Union[pd.DataFrame, Dict]:
        """
        Generate forecasts for time series data and optionally extend the original dataframe.
        
        Args:
            data (pd.DataFrame): DataFrame containing the time series data
            target_column (str): Name of the column to forecast
            date_column (str, optional): Name of the date/time column. If None, first column is used.
            prediction_length (int, optional): Number of periods to forecast
            return_extended_df (bool, optional): If True, returns extended DataFrame; otherwise returns forecast dict
            
        Returns:
            Union[pd.DataFrame, Dict]: Extended DataFrame with forecasts or forecast results dictionary
        """
        try:
            # Use first column as date column if not specified
            if date_column is None:
                date_column = data.columns[0]
                logger.info(f"Using {date_column} as date column")
            
            # Create a copy to avoid modifying the original
            current_df = data.copy()
            
            # Prepare CSV data for the request
            csv_data = current_df.to_csv(index=False)
            
            # Prepare the request
            files = {
                'file': ('./data.csv', csv_data, 'text/csv')
            }
            request_data = {
                'prediction_length': str(prediction_length),
                'target_column': target_column
            }
            
            # Send the request to the endpoint
            response = requests.post(
                f"{self.base_url}",  # Note: Using the base URL directly
                data=request_data,
                files=files
            )
            
            # Process successful response
            if response.status_code == 200:
                # Store the forecast result
                self.last_forecast = response.json()
                logger.info(f"Forecast generated successfully")
                
                # If only forecast data is requested, return it
                if not return_extended_df:
                    return self.last_forecast
                
                # Process to extend the dataframe with forecast values
                extended_values = self.last_forecast['actual'] + self.last_forecast['forecast']
                lower_quantile = [None for _ in range(len(self.last_forecast['actual']))] + self.last_forecast['lower_quantile']
                upper_quantile = [None for _ in range(len(self.last_forecast['actual']))] + self.last_forecast['upper_quantile']
                future_assigned = [False] * len(self.last_forecast['actual']) + [True] * len(self.last_forecast['forecast'])
                
                # Ensure date column is datetime
                current_df[date_column] = pd.to_datetime(current_df[date_column], format='mixed', utc=True)
                
                # Infer frequency from dates
                dates = current_df[date_column]
                freq = pd.infer_freq(dates)
                if freq is None:
                    # Try to infer a reasonable frequency if pandas can't
                    if len(dates) >= 2:
                        # Calculate average time difference
                        avg_diff = (dates.iloc[-1] - dates.iloc[0]) / (len(dates) - 1)
                        if avg_diff.days >= 28 and avg_diff.days <= 31:
                            freq = 'M'  # Monthly
                        elif avg_diff.days >= 7 and avg_diff.days <= 7.5:
                            freq = 'W'  # Weekly
                        elif avg_diff.days >= 0.9 and avg_diff.days <= 1.1:
                            freq = 'D'  # Daily
                        else:
                            freq = 'D'  # Default to daily
                    else:
                        freq = 'D'  # Default if can't infer
                
                # Generate future dates
                future_dates = pd.date_range(start=dates.iloc[-1], periods=prediction_length + 1, freq=freq)[1:]
                
                # Extend the DataFrame with future dates
                extended_df = pd.concat([
                    current_df, 
                    pd.DataFrame({date_column: future_dates})
                ]).reset_index(drop=True)
                
                # # Ensure date column is called 'date' for consistency
                # if date_column != 'date':
                #     extended_df.rename(columns={date_column: 'date'}, inplace=True)
                
                # Add the forecast values and metrics
                extended_df[target_column] = pd.Series(extended_values[:len(extended_df)])
                extended_df['future_assigned'] = pd.Series(future_assigned[:len(extended_df)])
                extended_df['lower_quantile'] = pd.Series(lower_quantile[:len(extended_df)])
                extended_df['upper_quantile'] = pd.Series(upper_quantile[:len(extended_df)])
                
                logger.info(f"Extended DataFrame created with {len(future_dates)} forecast periods")
               
                # Return the extended DataFrame
                return extended_df
                
            else:
                error_text = response.text
                logger.error(f"Forecast API request failed: {error_text}")
                return {"error": f"Forecast error: {error_text}"}
                
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            return {"error": f"Error generating forecast: {str(e)}"}

# Standalone function for direct registration with function registry
def generate_forecast(
    data: pd.DataFrame, 
    target_column: str, 
    date_column: str = None,
    prediction_length: int = 30,
    forecast_api_url: str = None
) -> pd.DataFrame:
    """
    Generate time series forecasts and extend the dataframe with predicted values.
    
    Args:
        data (pd.DataFrame): DataFrame containing the time series data
        target_column (str): Name of the column to forecast
        date_column (str, optional): Name of the date/time column. If None, first column is used.
        prediction_length (int, optional): Number of periods to forecast
        forecast_api_url (str, optional): URL for the forecast API. If None, uses environment variable.
        
    Returns:
        pd.DataFrame: Extended DataFrame with forecast values and confidence intervals
    """
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get API URL from environment if not provided
    if forecast_api_url is None:
        forecast_api_url = os.environ.get('FORECAST_API_URL')
        if not forecast_api_url:
            logger.error("No forecast API URL provided")
            return {"error": "No forecast API URL provided"}
    
    # Create a temporary client
    client = ForecastClient(forecast_api_url)
    
    # Execute forecast
    result = client.forecast(
        data=data,
        target_column=target_column,
        date_column=date_column,
        prediction_length=prediction_length
    )
    
    return result