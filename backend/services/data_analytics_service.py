import json
import re
from pydantic import BaseModel, Field, validator
from datetime import date as Date
from typing import Dict, Union

class GeneralDataModel(BaseModel):
    date: Date = Field(..., description="Fecha en formato ISO (YYYY-MM-DD)")
    variables: Dict[str, Union[int, float]] = Field(
        ..., 
        description="Un diccionario con variables dinámicas y valores numéricos"
    )

    @validator("variables")
    def validate_variables(cls, v):
        if not all(isinstance(value, (int, float)) for value in v.values()):
            raise ValueError("Todos los valores en 'variables' deben ser numéricos (int o float).")
        return v

# Ejemplo
data = [
    {"date": "1900-01-01", "variables": {"minimum_wage_hundreds_dlls": 2.5, "home_cost_Mdlls": 0.450}},
    {"date": "1910-01-01", "variables": {"minimum_wage_hundreds_dlls": 3.5, "home_cost_Mdlls": 0.500}},
    {"date": "1920-01-01", "variables": {"minimum_wage_hundreds_dlls": 3.9, "home_cost_Mdlls": 1.200}},
    {"date": "1930-01-01", "variables": {"minimum_wage_hundreds_dlls": 4.1, "home_cost_Mdlls": 1.600}},
    {"date": "1940-01-01", "variables": {"minimum_wage_hundreds_dlls": 4.4, "home_cost_Mdlls": 2.400}},
    {"date": "1950-01-01", "variables": {"minimum_wage_hundreds_dlls": 4.8, "home_cost_Mdlls": 2.350}},
    {"date": "1960-01-01", "variables": {"minimum_wage_hundreds_dlls": 5.1, "home_cost_Mdlls": 2.700}},
    {"date": "1970-01-01", "variables": {"minimum_wage_hundreds_dlls": 5.1, "home_cost_Mdlls": 4.400}},
    {"date": "1980-01-01", "variables": {"minimum_wage_hundreds_dlls": 5.2, "home_cost_Mdlls": 5.600}},
    {"date": "1990-01-01", "variables": {"minimum_wage_hundreds_dlls": 5.6, "home_cost_Mdlls": 6.900}},
    {"date": "2000-01-01", "variables": {"minimum_wage_hundreds_dlls": 5.9, "home_cost_Mdlls": 8.800}},
    {"date": "2010-01-01", "variables": {"minimum_wage_hundreds_dlls": 6.2, "home_cost_Mdlls": 12.400}},
    {"date": "2020-01-01", "variables": {"minimum_wage_hundreds_dlls": 6.3, "home_cost_Mdlls": 15.600}},
    {"date": "2030-01-01", "variables": {"minimum_wage_hundreds_dlls": 6.5, "home_cost_Mdlls": 18.500}}
]


def insert_sample_data(message):
    # Insert sample data
    try:
        json_message = json.loads(message)
        json_message.update({'chartData': data})
        return json.dumps(json_message)
    except Exception as e:
        print(e)
        try:
            json_message = re.sub(r"```json\{.*\})```", r"\1, 'chartData': data", message)
            json_message = json.loads(json_message)
            json_message.update({'chartData': data})
            return json.dumps(json_message)
        except Exception as e:
            print(e)
            return message
        
        