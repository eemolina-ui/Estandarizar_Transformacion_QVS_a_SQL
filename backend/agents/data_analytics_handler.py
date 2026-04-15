import pandas as pd
import json
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, Optional
import requests
import logging
import re
#from datetime import datetime
from services.graphics_service import create_forecast_plots, plot_dataframe
from agents.pandasAgent import DataFrameManipulator
logger = logging.getLogger(__name__)

class DataAnalyticsHandler:
    def __init__(self, llm, mmllm):
        # self.current_df = pd.read_csv('./assets/desocupacion.csv')        
        # self.load_data(self.current_df)
        self.mmllm = mmllm
        self.llm = llm
        self.chronos_endpoint = "http://forecast-service:8000/forecast"
        self.last_forecast = None
        self.df_manipulator = None
        
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
    
    def load_data(self, data: pd.DataFrame) -> None:
        """Load data into the handler"""
        self.current_df = data

    async def generate_forecast(self, target_column: str, prediction_length: int = 30) -> Dict:
        """Generate forecasts using the Chronos endpoint"""
        if self.current_df is None:
            return {"error": "No data loaded"}

        try:
            # Prepare CSV data
            csv_data = self.current_df.to_csv(index=False)
            
            # Prepare the request
            files = {
                'file': ('./assets/orders_example.csv', csv_data, 'text/csv')
            }
            data = {
                'prediction_length': str(prediction_length),
                'target_column': target_column
            }
            response = requests.post(self.chronos_endpoint, data=data, files=files)
            if response.status_code == 200:
                self.last_forecast = response.json()

                # Extend the target column with forecast values
                extended_values = self.last_forecast['actual'] + self.last_forecast['forecast']
                lower_quantile = [None for _ in range(len(self.last_forecast['actual']))] + self.last_forecast['lower_quantile']
                upper_quantile = [None for _ in range(len(self.last_forecast['actual']))] + self.last_forecast['upper_quantile']
                future_assigned = [False] * len(self.last_forecast['actual']) + [True] * len(self.last_forecast['forecast'])


                # Usage in the original context:
                date_format = self.infer_date_format(str(self.current_df[self.current_df.columns.tolist()[0]].iloc[0]))

                dates = pd.to_datetime(self.current_df[self.current_df.columns.tolist()[0]], format='mixed', utc=True)
 
                freq = pd.infer_freq(dates)

                # Generate future dates
                future_dates = pd.date_range(start=dates.iloc[-1], periods=prediction_length + 1, freq=freq)[1:]

                # Extend the DataFrame with future dates
                self.current_df = pd.concat([
                    self.current_df, 
                    pd.DataFrame({self.current_df.columns.tolist()[0]: future_dates})
                ]).reset_index(drop=True)
                self.current_df.rename(columns={self.current_df.columns.tolist()[0]: 'date'}, inplace=True)
                self.current_df[target_column] = pd.Series(extended_values[:len(self.current_df)])
                self.current_df['future_assigned_column'] = pd.Series(future_assigned[:len(self.current_df)])
                self.current_df['lower_quantile'] = pd.Series(lower_quantile[:len(self.current_df)])
                self.current_df['upper_quantile'] = pd.Series(upper_quantile[:len(self.current_df)])
                logger.info(f"Forecast generated: {self.current_df}")
                try:
                    plots = create_forecast_plots(self.current_df, target_column)
                    return self.current_df, plots
                except Exception as e:
                    logger.error(f"Error generating forecast plots: {str(e)}")
            else:
                error_text = response.text()
                return {"error": f"Forecast error: {error_text}"}
        except Exception as e:
            return {"error": f"Error generating forecast: {str(e)}"}

    def analyze_data(self, query: str) -> Dict:
        """Perform basic data analysis based on the query"""
        try:
            # Get column names
            columns = self.current_df.columns.tolist()
            
            # Basic statistics for numeric columns
            numeric_cols = self.current_df.select_dtypes(include=['int64', 'float64']).columns
            stats = self.current_df[numeric_cols].describe()
            
            # Format the response
            analysis = {
                "columns": columns,
                "stats": stats.to_dict(),
                "row_count": len(self.current_df)
            }
            return analysis
        except Exception as e:
            return {"error": f"Error analyzing data: {str(e)}"}

    async def process_query(self, query: str) -> Dict:
        """Process a user query and return appropriate response"""
        try:
            dataframe_extraction_prompt = """
            You are a tool for extraction of a dataframe path from a user query.
            The user will ask for a data analysis; then you need to recognize the dataframe to which the user refers.
            
            The user probably will ask for some column names, or some statistics, or some analysis.
            Available dataframes and their specifications:

            1. Path: ./assets/sp500_data.csv
                Columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', Dividends', 'Stock Splits']
                Description: Standard & Poor's 500 index data. The 500 most valuable companies in the US stock market.
                Suggestions: The user probably will ask for aperture, closure, or volume. Or mention the S&P 500 / Stocks (acciones in spanish) / Volume (Volumen or Número de transacciones in spanish) / Dividends (Dividendos in spanish)

            2. Path: ./assets/desocupacion.csv
               Columns: ['Periodos', 'desocupacion']
               Description: Unemployment data

            3. Path: ./assets/orders_example.csv
               Columns: ['ordersdate', 'orders']
               Description: Order tracking data

            4. Path: ./assets/metro.csv
               Columns: ['mes', 'pasajeros']
               Description: Metro passenger data

            5. Path: ./assets/ICC.csv
               Columns: ['Periodos', 'ICC']
               Description: Consumer confidence index data

            You have to answer with the path of the dataframe that the user is referring to.
            Return only the exact path string, without quotes, backticks or special characters.
            Your answer will be used directly in pd.read_csv().

            Query: {query}
            """

            result = self.llm.invoke(dataframe_extraction_prompt.format(query=query[-8:]))
            # Extract path using regular expression
            path_match = re.search(r'(\.\/assets\/.*?\.csv)', result.content)
            if path_match:
                self.df_path = path_match.group(1)
                self.current_df = pd.read_csv(self.df_path)
                self.current_df.rename(columns={self.current_df.columns.tolist()[0]: 'date'}, inplace=True)
                date_format = self.infer_date_format(str(self.current_df['date'].iloc[0]))
                self.date_freq = pd.infer_freq(pd.to_datetime(self.current_df['date'], utc=True, format='mixed'))
                self.df_manipulator = DataFrameManipulator(self.llm, self.current_df)
            else: 
                message = {
                    "text": "Lo siento, no entiendo a qué datos te refieres. ¿Podrías ser más específico?",
                    "facialExpression": "default",
                    "animation": "Talking_0",
                }
                return message
        except Exception as e:
            return {
                "text": f"Lo siento, hubo un error procesando tu consulta: {str(e)}",
                "facialExpression": "default",
                "animation": "Talking_1",
                "type": "error"
            }

        
        try:
            # First, use the LLM to classify the query type
            classification_prompt = f"""
            Based on the following query, idenfity the query type:
            "{query[-1]}"
            1.FORECAST - If the query asks for predictions or future values 
            2.ANALYSIS - If the query asks for analysis of existing data 
            3.GRAPHICS - If the query asks for graphical representation of data 
            4.UNKNOWN - If the query type is unclear 

            The forecast, analysis and graphics queries will be processed in different pipelines.
            So, for example, if the query is a forecast, and the user do not specify a previos or extra process, return "FORECAST, false"
            On the other hand, if the user explicitly asks for agrupations, filters, or other process, return "FORECAST, true" and the same for the other types.

            If the user asks for a FORECAST, usually will ask for a target column and a prediction length. This information do not mean that a previous process is required; so in this case, you have to answer "FORECAST, false".
            On the other hand, if the user specifies a previos modification or process, like filters, groupings, or other, return "FORECAST, true". And the same for the other types.

            if previous or extra process is required, add true to the query type, for example:
            "<QUERY_TYPE>,true"

            if not, return "<QUERY_TYPE>, false"
            """
            
            query_type = self.llm.invoke(classification_prompt)
            logger.info(f"Query type: {query_type.content}")
            query_type = query_type.content.strip().upper().split(",")

            # Extract query type and process flag
            query_type, *process_flag = query_type
            process = bool(process_flag and process_flag[0].strip().lower() == 'true')
            
            if process:
                message, self.current_df, analysis = self.df_manipulator.process_query(query)

            if query_type == "FORECAST":
                # Use LLM to extract target column and prediction length
                # Get the frequency and format of dates
            
                extraction_prompt = """
                From this query: "{query}"
                Extract:
                1. The target column name
                2. The prediction length (in numbers)

                the columns of the dataframe are: {columns}

                For the prediction length, If the user is clear about the number of periods to forecast, use that number
                If not, infeer the number of periods to forecast based on the user query and the data frequency.
                {frequency}
                For example, if the user asks for "next month" and the data is monthly, the prediction length is 1.
                If the user asks for "next quarter" and the data is monthly, the prediction length is 3.
                If the user asks for "next year" and the data is monthly, the prediction length is 12.

                Considerations for specific columns: 
                - For the SP500 data, the user probably will ask for aperture, closure, or volume, or mention the S&P 500 / Stocks (acciones in spanish) / Volume (Volumen or Número de transacciones in spanish)
                - For the unemployment data, the user probably will ask for the unemployment rate or mention unemployment (desocupación in spanish)
                - For the orders data, the user probably will ask for the number of orders or mention orders ("órdenes" or "pedidos" in spanish)
                
                Return ONLY a JSON string with keys 'target_column' and 'prediction_length', just like this:
                {{"target_column": "revenue", "prediction_length": 30}}
                This JSON string will be used directly to input the forecast parameters. and will be parsed with json.loads(),
                therefore it must start with the first curly brace {{ and end with the last }}.
                Do not use special characters or extra spaces in the JSON string; all columns are in ascii.
                """.format(query=query[::2], columns=self.current_df.columns.tolist(), frequency=self.date_freq)
                logger.info(f"Extraction prompt: {extraction_prompt}")
                params = json.loads((self.llm.invoke(extraction_prompt)).content)
                logger.info(f"Extraction params: {params}")
                forecast_result, plots = await self.generate_forecast(
                    target_column=params['target_column'],
                    prediction_length=params['prediction_length']
                )
                
                # Process forecast result to align with the response format and make an analysis
                # Create a comparison table for analysis
                # comparison_df = pd.DataFrame()
                if isinstance(forecast_result, pd.DataFrame):
                    actual_values = forecast_result[~forecast_result['future_assigned_column']][params['target_column']]
                    forecast_values = forecast_result[forecast_result['future_assigned_column']][params['target_column']]
                    
                    comparison_table = {
                        "actual_values_stats": actual_values.describe().to_dict(),
                        "forecast_values_stats": forecast_values.describe().to_dict()
                    }
                    logger.info(f"Comparison table: {comparison_table}")

                    
                    analysis_prompt = """
                    Tu nombre es Ingrid, eres una asistente, experta en análisis de datos. 
                    Analiza las imágenes que se te proporcionan. 
                    Son dos gráficos que muestran el historial y la predicción de la variable objetivo.
                    Las medidas de tendencia central y dispersión de los valores reales y pronosticados son los siguientes: 

                    {comparison_table_json}
                    
                    Proporciona un análisis conciso y profesional que responda a la pregunta del usuario:
                    {query}
                    
                    Si es relevante, menciona las medidas de tendencia central y dispersión de los valores reales y pronosticados.
                    
                    Sé breve pero explicativo, sólo usa números si son relevantes para responder a la pregunta y redondea a un decimal,
                    recuerda que estás conversando con un usuario no técnico.

                    Responde en formato JSON con la siguiente estructura:
                    {{
                        "text": "tu análisis aquí",
                        "facialExpression": "default",
                        "animation": "Talking_0"
                    }}

                    Las diferentes expresiones faciales son: smile, sad, angry, surprised, funnyFace, and default.
                    Las diferentes animaciones son: Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, and Angry.
                    Tu respuesta debe poder ser decodificada con json.loads(), por lo tanto, comienza con el primer corchete {{ y cierra con el último }}
                    """.format(comparison_table_json=json.dumps(comparison_table), query=query[::2])
                    
                    forecast_analysis = self.mmllm.invoke(
                        [
                            SystemMessage(content="Genera un análisis de los datos de pronóstico."),
                            HumanMessage(
                            content=[
                                {"type": "image_url", "image_url": {'url':plots['historical_plot']}},
                                {"type": "image_url", "image_url": {'url':plots['forecast_plot']}},
                                {"type": "text", "text": analysis_prompt}
                            ])
                        ]
                    )
                    try:
                        forecast_result = json.loads(forecast_analysis.content)
                        logger.info(f"Forecast analysis: {forecast_analysis}")

                    except Exception as e:
                        logger.warning(f"Error parsing forecast analysis: {str(e)}")
                        logger.warning(f"Forecast analysis: {forecast_analysis.content}")
                        forecast_result = re.sub(r"```json\{.*\})```", r"\1", forecast_analysis)

                logger.info(f"Forecast analysis result: {forecast_result}")


                try:
                    chart_size = self.current_df['lower_quantile'].notna().sum()*9
                    
                    forecast_result.update({
                        "type": "data_analytics",
                        "chartData": [
                            {"date": str(date), "variables": {params['target_column']: value, "lower_quantile": lower, "upper_quantile": upper}}
                            for date, value, lower, upper in zip(
                                self.current_df[self.current_df.columns.tolist()[0]][-chart_size:].tolist(),
                                self.current_df[params['target_column']][-chart_size:].tolist(),
                                self.current_df['lower_quantile'][-chart_size:].tolist(),
                                self.current_df['upper_quantile'][-chart_size:].tolist()
                            )
                        ]
                        })
                    return json.loads(json.dumps(forecast_result, ensure_ascii=False).replace("NaN", "null"))
                except Exception as e:
                    logger.warning(f"Error updating forecast result: {str(e)}")
                    return json.loads(json.dumps(forecast_result, ensure_ascii=False).replace("NaN", "null"))

            elif query_type == "ANALYSIS" or query_type == "GRAPHICS":
                analysis_result = self.analyze_data(query)
                
                # Use LLM to generate a natural language response
                response_prompt = """
                Tu nombre es Ingrid, eres una asistente virtual experta en análisis de datos.
                Responde la consulta del usuario:

                "{query}"

                Puedes basarte en la imagen que se te proporciona y en el resumen de datos proporcionado a continuación:
                {analysis_result}
                
                Si es relevante, menciona las medidas de tendencia central y dispersión de los valores reales y pronosticados.
                Sé breve pero explicativo, sólo usa números si son relevantes para responder a la pregunta y redondea a un decimal,
                recuerda que estás conversando con un usuario no técnico.
                Tu respuesta debe poder ser decodificada con json.loads(), por lo tanto, comienza con el primer corchete {{ y cierra con el último }}

                {{
                    "text": "Respuesta en lenguaje natural",
                    "facialExpression": "smile",
                    "animation": "Talking_0",
                }}

                Las diferentes expresiones faciales son: smile, sad, angry, surprised, funnyFace, and default.
                Las diferentes animaciones son: Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, and Angry. 

                
                """.format(query=query[::2], analysis_result=json.dumps(analysis_result))
                

                base_64_image = plot_dataframe(self.current_df)
                logger.info(f"--------------------------------------------------------")
                logger.info(f"SE GRAFICÓ EL DATAFRAME")
                logger.info(f"--------------------------------------------------------")
                response = self.mmllm.invoke(
                    [
                        SystemMessage(content="Genera un análisis de los datos."),
                        HumanMessage(
                        content=[
                            {"type": "text", "text": response_prompt},
                            {"type":"image_url", "image_url": {"url": base_64_image}}
                        ]),

                    ]
                )
                response = json.loads(response.content)

                # Get numeric columns
                numeric_cols = self.current_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                response.update({
                    "type": "data_analytics",
                    "chartData": [
                        {
                            "date": str(row['date']),
                            "variables": {
                                col: row[col] for col in numeric_cols
                            }
                        }
                        for _, row in self.current_df.iterrows()
                    ]
                })
                return response

            else:
                return {
                    "text": "Lo siento, no pude entender el tipo de análisis que necesitas. ¿Podrías reformular tu pregunta?",
                    "type": "error"
                }

        except Exception as e:
            return {
                "text": f"Lo siento, hubo un error procesando tu consulta: {str(e)}",
                "type": "error"
            }