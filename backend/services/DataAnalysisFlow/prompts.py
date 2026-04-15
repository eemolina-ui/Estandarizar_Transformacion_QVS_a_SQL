"""
This module contains all prompt templates used by the DataAnalysisFlow class.
Templates are customizable and support formatting with additional context.
"""

class PromptTemplates:
    """Manages all prompt templates for data analysis workflow."""
    
    def __init__(self, style_config=None):
        """
        Initialize prompt templates with optional style configuration.
        
        Args:
            style_config (dict): Configuration for response style, graphics, etc.
        """
        self.style_config = style_config or {}
        
        # Default style configuration
        self.default_style = {
            "color_palette": ["#4C72B0", "#55A868", "#C44E52", "#8172B3", "#CCB974", "#64B5CD"],
            "plot_style": "plots en dark de seaborn (sns.set_style('dark'))",
            "text_style": "formal",
            "font_family": "la fuente sans-serif por defecto",
            "chart_type_preference": "auto"
        }
        
        # Combine provided style with defaults
        for key, value in self.default_style.items():
            if key not in self.style_config:
                self.style_config[key] = value
    
    def get_planning_prompt(self, question, available_functions, available_datasets=None, additional_context=None):
        """
        Creates a prompt for planning analysis approach.
        
        Args:
            question (str): User's question
            available_functions (dict): Dictionary of available functions and schemas
            available_datasets (dict, optional): Dictionary of available datasets
            additional_context (str, optional): Additional context for planning
            
        Returns:
            str: Formatted prompt
        """
        prompt = """
        Eres un planificador de análisis de datos. Tu tarea es crear un plan detallado para responder 
        la pregunta del usuario basado en los datos disponibles y las funciones que puedes utilizar.
        
        La pregunta del usuario es: {question}
        
        {datasets_section}
        
        Puedes utilizar las siguientes funciones en tu análisis:
        {available_functions}
        
        {additional_context}
        
        Tu respuesta debe ser un diccionario JSON con el siguiente formato:
        {{
            "plan": "Descripción detallada del plan de análisis paso a paso",
            "required_functions": ["nombre_funcion1", "nombre_funcion2", ...],
            "required_datasets": ["dataset1", "dataset2", ...],
            "expected_outputs": {{
                "data": "Descripción del tipo de datos que se espera generar",
                "visualizations": ["Descripción de las visualizaciones esperadas"],
                "insights": ["Principales insights que se buscarán"]
            }}
        }}
        
        Tu respuesta será leída en python con json.loads(<tu_respuesta>), por lo tanto debe ser un json string válido;
        Comienza con el primer corchete {{ y termina con el último corchete }}. No utilices backticks (`) en tu respuesta.
        El plan debe ser detallado y específico, indicando exactamente qué operaciones se realizarán,
        qué visualizaciones se crearán y qué insights se buscarán.

        Entre las indicaciones obligatorias que se tienen que especificar en el plan están:
        - El objeto data debe guardarse en el formato orientado a registros: data.to_dict(orient='records').
        """
        
        # Prepare the datasets section if available
        if available_datasets:
            datasets_section = f"""
            Información sobre los datasets disponibles:
            {self._format_datasets_info(available_datasets)}
            """
        else:
            datasets_section = "No hay información de datasets disponible."
        
        return prompt.format(
            question=question,
            datasets_section=datasets_section,
            available_functions=self._format_function_schemas(available_functions),
            additional_context=additional_context or ""
        )
    
    def get_dataset_identification_prompt(self, datasets, datasets_info, additional_context=None):
        """
        Creates a prompt for identifying required datasets.
        
        Args:
            datasets (list): List of available dataset names
            datasets_info (dict): Dictionary with dataset metadata
            additional_context (str, optional): Additional context about the data
            
        Returns:
            str: Formatted prompt
        """
        prompt = """
        Eres una herramienta de reconocimiento. Tu tarea es reconocer el dataset necesario para responder la pregunta del usuario.
        Tu respuesta debe ser un diccionario en el siguiente formato: 
        {{ "datasets_required": ["dataset1", "dataset2", ...] }}
        
        Tu respuesta será usada en código python, y será leída con json.loads(<tu_respuesta>), por lo tanto asegúrate de que sea un JSON válido;
        debes comenzar por el primer corchete {{ y terminar con el último corchete }}.

        Reglas:
        - si la pregunta no requiere un dataset, responde con una lista vacía.
        - Responde siempre en el formato indicado {{ "datasets_required": [...] }}, comenzando con el primer corchete {{ y terminando por el último corchete }}. 

        los datasets disponibles son: {datasets}

        La descripción de los datasets es la siguiente:
        {datasets_info}
        
        {additional_context}
        """
        
        return prompt.format(
            datasets=datasets,
            datasets_info=datasets_info,
            additional_context=additional_context or ""
        )
    
    def get_code_generation_prompt(self, question, plan, datasets_info, function_schemas, style_config=None):
        """
        Creates a prompt for generating code based on the plan.
        
        Args:
            question (str): User's question
            plan (dict): Analysis plan from planning step
            datasets_info (dict): Information about available datasets
            function_schemas (dict): Schemas for available functions
            style_config (dict, optional): Override default style config
            
        Returns:
            str: Formatted prompt
        """
        # Use provided style_config or fall back to instance default
        style = style_config or self.style_config
        
        prompt = """
        Eres un programador python, experto en Análisis de datos, que resuelve problemas de análisis de datos. 
        Tu tarea es escribir un script en python que responda la pregunta del usuario. 
        Debes usar los datos provistos y su descripción para generar la respuesta.

        La pregunta del usuario es: {question}

        El plan de análisis que debes seguir es:
        {plan}

        Las funciones requeridas que debes utilizar son:
        {required_functions}

        Las variables globales a las que tienes acceso son las siguientes:

        safe_globals = {{
            "pd": pd,
            "np": np,
            "plt": plt,
            "sns": sns,
            "io": io,
            "base64": base64,
            # Funciones adicionales
            {additional_functions}
        }}

        Los esquemas de las funciones adicionales son los siguientes:

        {aditional_functions_schemas}


        Las variables locales disponibles son las siguientes:

        local_vars = {{
            data: {{...}},  # Diccionario con DataFrames cargados
            result: None,   # Variable para almacenar el resultado            
        }}

        La información de los datasets cargados es esta: 
        {datasets_info}

        La forma en la que puedes acceder a los datos es a través del diccionario 'data', cuyas claves son los nombres de los datasets.
        nombres: {datasets_names}

        Estilo de gráficos:
        - Paleta de colores: {color_palette}
        - Estilo de gráfico: {plot_style}
        - Familia de fuentes: {font_family}
        - Tipo de gráfico preferido: {chart_type_preference}

        Tu respuesta debe ser un diccionario en el siguiente formato: 
        {{
            "code": "<Tu código python>"
        }}

        Será leída con json.loads(<tu_respuesta>), por lo tanto asegúrate de que sea un JSON válido;
        debes comenzar por el primer corchete {{ y terminar con el último corchete }}.
        Tu respuesta será ejecutada en un entorno seguro, por lo que no tienes acceso a funciones peligrosas como os.system, subprocess.run, etc.
        Tu código será ejecutado con exec(<tu código>, safe_globals, local_vars), y debe almacenar el resultado en la variable 'result';
        
        El código debe seguir estas reglas:
        1. Al inicio del código, configura los estilos de las gráficas según el estilo solicitado.
        2. Debes usar la paleta de colores proporcionada para cualquier visualización.    
        3. Puedes apoyarte de las funciones adicionales proporcionadas en 'safe_globals'.
        4. La salida final debe almacenarse en la variable 'result' como un diccionario con las siguientes claves:
           - 'text': Texto explicativo con los insights principales.
           - 'data': Datos en formato dict (usando to_dict(orient='records') para DataFrames).
           - 'images': Lista de imágenes en formato base64 con prefijo 'data:image/png;base64,'.
        5. Evita guardar texto con saltos de línea como \\n, ya que esto puede causar errores en la interpretación de la respuesta.
        6. deberás devolver gráficos en formato base 64. Debes guardar los gráficos generados en la lista 'images' y devolverlos en la respuesta. este código también corre por tu cuenta.
        7. Los datos que devuelvas en data, deben ser en formato json: resulting_data.to_dict(orient='records').
        Es muy importante que se devuelva como un diccionario orientado a registros, para que pueda ser interpretado correctamente por el sistema cliente.
        9. Algunos errores frecuentes en el código que hay que evitar son los siguientes: 
            - Éste es un error común: df['fecha_combinada'] = pd.concat([df['fecha_local'], df['fecha_utc']]) debido al siguiente error: Cannot mix tz-aware with tz-naive values. Estandariza las fechas antes de concatenarlas.
            - éste código: df['Fecha'] = pd.to_datetime(df[['Año', 'Mes', 'Dia']])  no funcionará debido al siguiente error: Execution attempt 1 failed: to assemble mappings requires at least that [year, month, day] be specified: [day,month,year] is missing. para dataframes con fechas en múltiples columnas, hay que concatenar las columnas en un string y luego convertir a datetime.
        10. Presta especial atención a los formatos de fecha para evitar errores de conversión.
        
        Repito: los datos deben ser devueltos en formato json, orientados a registros: resulting_data.to_dict(orient='records').


        pregunta de ejemplo: "Grafica un promedio de las edades por departamento de los usuarios en el dataset_1"

respuesta de ejemplo: 
{{
"code": \"\"\"
data['dataset_1']['age'] = data['dataset_1']['age'].astype(int)

plt.ion()
fig, ax = plt.subplots()
sns.barplot(x='department', y='age', data=data['dataset_1'], ax=ax)
plt.xticks(rotation=45)
plt.tight_layout()
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
img_1 = 'data:image/png;base64,' + base64.b64encode(buf.read()).decode())
plt.close()
plt.ioff()

data_grouped = data['dataset_1'].groupby('department')['age'].mean()

result = {{
    "data": data_grouped.to_dict(oriend='records'),
    "images": [img_1]
    "text": f\"\"\"El promedio de las edades por departamento es: {{data['dataset_1'].groupby('department')['age'].mean().to_dict()}}
    \"\"\"
}}
\"\"\"
}}
        """
        # Format required functions and available functions
        required_functions = plan.get("required_functions", [])
        formatted_required = self._format_required_functions(required_functions)
        formatted_additional = self._format_additional_functions(required_functions, function_schemas)
        datasets_info_formatted = self._format_datasets_info(datasets_info)
        return prompt.format(
            question=question,
            plan=plan.get("plan", "No se proporcionó un plan."),
            required_functions=formatted_required,
            additional_functions=formatted_additional,
            aditional_functions_schemas=self._format_function_schemas(function_schemas),
            datasets_info=datasets_info_formatted,
            datasets_names=plan.get("required_datasets", []),
            color_palette=style["color_palette"],
            plot_style=style["plot_style"],
            font_family=style["font_family"],
            chart_type_preference=style["chart_type_preference"]
        )
    
    def get_code_correction_prompt(self, code, error, question, function_schemas, plan,  datasets_info, style_config=None):
        """
        Creates a prompt for correcting code when an error occurs.
        
        Args:
            code (str): Original code
            error (str): Error message
            question (str): User's question
            datasets_info (dict): Information about datasets
            style_config (dict, optional): Override default style config
            
        Returns:
            str: Formatted prompt
        """
        # Use provided style_config or fall back to instance default
        style = style_config or self.style_config
        
        prompt = """
        Eres un corrector de código. 
        Tu tarea es revisar el código provisto, junto con el error y la descripción del error, y corregir el código para que no haya errores.
        Debes mantener la lógica del código intacta, siempre que sea posible.

        el plan de análisis que debes seguir es:

        {plan}
        
        El código proporcionado es en Python; y será ejecutado en un scope local, con las siguientes variables: 

        local_vars = {{
            data: {{...}},  # Diccionario con DataFrames cargados
            result: None,   # Variable para almacenar el resultado            
        }}

        safe_globals = {{
            "pd": pd,
            "np": np,
            "plt": plt,
            "sns": sns,
            "io": io,
            "base64": base64,
            #### Funciones adicionales
            {additional_functions}
        }}

        Los esquemas de las funciones adicionales son los siguientes:
        {aditional_functions_schemas}

        El código debe resolver la pregunta proporcionada en el mensaje del usuario: {question}
        
        Asegúrate de seguir estos estilos de visualización:
        - Paleta de colores: {color_palette}
        - Estilo de gráfico: {plot_style}
        - Familia de fuentes: {font_family}
        - Tipo de gráfico preferido: {chart_type_preference}

        Tu respuesta debe ser en el siguiente formato:

        {{
            "code": "<código corregido>",
        }}

        será leída con ast.literal_eval(<tu_respuesta>), y ejecutada con exec(<código_corregido>, safe_globals, local_vars).
        De modo que tu respuesta debe ser un formato JSON válido (comienza por el primer corchete {{ y termina con el último }}), y el código corregido debe ser un string de Python válido.

        Mantén el formato del código original en cuanto a caracteres, espacios, saltos de línea, etc.
        Evita guardar texto con saltos de línea como \\n, ya que esto puede causar errores en la interpretación de la respuesta.
        deberás devolver gráficos en formato base 64. Debes guardar los gráficos generados en la lista 'images' y devolverlos en la respuesta. este código también corre por tu cuenta.
        Los datos que devuelvas en data, deben ser en formato json: resulting_data.to_dict(orient='records').
        Es muy importante que se devuelva como un diccionario orientado a registros, para que pueda ser interpretado correctamente por el sistema cliente.
        Repito, los datos deben ser devueltos en formato json, orientados a registros: resulting_data.to_dict(orient='records').
        Presta especial atención a los formatos de fecha para evitar errores de conversión.

        Notas extra:
        - éste código: df['Fecha'] = pd.to_datetime(df[['Año', 'Mes', 'Dia']])  no funcionará debido al siguiente error: Execution attempt 1 failed: to assemble mappings requires at least that [year, month, day] be specified: [day,month,year] is missing. para dataframes con fechas en múltiples columnas, hay que concatenar las columnas en un string y luego convertir a datetime.
        - Éste es un error común: df['fecha_combinada'] = pd.concat([df['fecha_local'], df['fecha_utc']]) debido al siguiente error: Cannot mix tz-aware with tz-naive values. Estandariza las fechas antes de concatenarlas.

        Este es el código original:

        {code}

        Este es el error: 

        {error}

        Esta es una breve descripción de los datos que son usados en el código:

        {datasets_info}
        """
        required_functions = plan.get("required_functions", [])
        return prompt.format(
            question=question,
            code=code,
            error=error,
            plan=plan.get("plan", "No se proporcionó un plan."),
            datasets_info=self._format_datasets_info(datasets_info),
            additional_functions=self._format_additional_functions(required_functions, function_schemas),
            aditional_functions_schemas=self._format_function_schemas(function_schemas),
            color_palette=style["color_palette"],
            plot_style=style["plot_style"],
            font_family=style["font_family"],
            chart_type_preference=style["chart_type_preference"]
        )
    
    def _format_datasets_info(self, datasets_info):
        """Format datasets information for inclusion in prompts."""
        result = []
        for name, info in datasets_info.items():
            result.append(f"- {name}:")
            if 'shape' in info:
                result.append(f"  Filas: {info['shape'][0]}, Columnas: {info['shape'][1]}")
            if 'columns' in info:
                result.append(f"  Columnas: {', '.join(info['columns'])}")
            if 'head' in info:
                result.append("  Primeras filas: {0}".format(", \n".join(["{0}: {1}".format(key, value) for key, value in info['head'].items()])))
            if 'dtypes' in info:
                result.append(f"  Tipos de datos: {info['dtypes']}")
        return "\n".join(result)
    
    def _format_function_schemas(self, functions):
        """Format function schemas for inclusion in prompts."""
        result = []
        for name, schema in functions.items():
            result.append(f"- {name}: {schema['description']}")
            result.append(f"  Parámetros: {schema['parameters']}")
            result.append(f"  Retorna: {schema['returns']}")
        return "\n".join(result)
    
    def _format_required_functions(self, function_names):
        """Format required functions for inclusion in prompts."""
        if not function_names:
            return "No se requieren funciones específicas."
        
        result = []
        for name in function_names:
            result.append(f"- {name}")
        return "\n".join(result)
    
    def _format_additional_functions(self, function_names, function_schemas):
        """Format additional functions for inclusion in global namespace."""
        if not function_names:
            return ""
        
        result = []
        for name in function_names:
            if name in function_schemas:
                result.append(f'"{name}": {name},')
        return "\n".join(result)