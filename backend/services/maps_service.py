
from httpx import get
import requests
import pandas as pd
import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores.faiss import FAISS

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

embeddings_model = os.getenv("EMBEDDINGS_MODEL")
chunk_size = 1
embeddings = AzureOpenAIEmbeddings(model=embeddings_model,
                                   chunk_size=chunk_size)

def similarity(query, Main_knowledge, opciones):
    """
    Sirve para extraer los documentos relevantes de acuerdo a la busqueda principal del usuario. \n \n

    Args: \n
        query = El mensaje inicial del usuario sin formatear \n
        Main_knoledge = El dataframe con los registros actualizados \n
        aws_keys = Las contraeñas de AWS en formato lista \n \n

    Return: \n
        docs = Son los documentos más similares a la búsqueda del usuario. \n

    Hay que tomar en cuenta que el chunk size esta con ese valor pues es el largo promedio de un documento con los datos de Maps.
    Este puede cambiar con otros tipos de datos y se tiene que ajustar.

    """

    ## Create the embedding object
    embeddings = AzureOpenAIEmbeddings(model=embeddings_model,
                                   chunk_size=chunk_size) 
    # Seteamos 500 para que en teoría no pase de ese número de caractéres los documentos
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)

    # Cargamos el dataframe, de la columna nombre
    loader = DataFrameLoader(Main_knowledge, page_content_column="Nombre")
    loader= loader.load()

    # Separamos por documento
    ld_data_split = text_splitter.split_documents(loader)

    #Lo cargamos en FAISS para usar su funcion de similaridad de texto
    docsearch = FAISS.from_documents(ld_data_split, embeddings)
    docs = docsearch.similarity_search(query, k=opciones)
    return docs

def get_maps(Input_str, location):
    """
    Sirve para generar un dataframe de 10 resultados de Google Maps. \n

    Args: \n
        Input_str = El texto de la búsqueda. \n
        aws_keys =  Las constraseñas de AWS en formato lista. \n
        aws_session: Sesión con AWS de tipo client. \n
    
    Return:  \n
        df = Un data frame con forma 10x6 en caso de éxito o 1x6 en caso de no existir resultados. \n
    """
    # Llave de la API
    api_key=os.environ['MAPS_API_KEY']
        
    # URL de contacto
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"

    # Consulta a buscar en la API
    query = Input_str 
    radio="1000"
    location = location.replace(" ", "") 
    # Usamos el método get para obtener info
    # almacenamos la respuesta
    r = requests.get(url + 'query=' + query +
                        '&location='+ location+
                        '&radious=' + radio +
                        '&key=' + api_key)

    # Pasamos a datos de formato json en datos de formato python
    x = r.json()

    # Ahora x contiene una lista de diccionarios anidados
    # Sabemos que el diccionario contiene un par de valores clave
    # x contiene los resultados de la busqueda
    y = x['results']

    #############################################################
    ################### pre process the data ####################

        # Handle no data
    try:
        # Convert the dictionary to a dataframe
        df = pd.DataFrame(y)
        df = df.head(10)

        # shift column 'Name' to first position
        first_column = df.pop('name')

        # insert column using insert(position,column_name,
        # first_column) function
        df.insert(0, 'Name', first_column)
        df= df.rename(columns={"Name": "Nombre",
                            "formatted_address": "Direccion",
                            "geometry":"Coordenadas",
                            "opening_hours":"Horario", 
                            "rating":"Calificacion"})
        df= df[['Nombre','Direccion','Coordenadas', 'Horario','Calificacion']].sort_values(["Nombre"]).reset_index(drop=True)
        df= df.assign(Query=query)
        df['New_key'] = 'FullData= Nombre: ' + df['Nombre'].map(str) + '; Direccion: ' + df['Direccion'].map(str) + '; Coordenadas: ' + df['Coordenadas'].map(str) + '; Horario: ' + df['Horario'].map(str) + '; Calificacion: ' + df['Calificacion'].map(str)
        df[['Direccion', 'Coordenadas', 'Horario','Calificacion']]= " "
        df.pop('Nombre')
        df= df.rename(columns={"New_key": "Nombre"})
        df= df[df.columns[[5,0,1,2,3,4]]]
    except:
        df= {'Nombre': [" No data "],'Direccion': [" "],'Coordenadas': [" "], 'Horario': [" "],'Calificacion': [" "], 'Query': [query]}
        df= pd.DataFrame(df)

     
    return df



def text_with_format(docs_object):
    """
    Sirve para ordenar un texto con saltos de línea. \n
    Args: \n
        - docs_object = Necesita la salida de docs del similarity  \n
    Return: \n
        Devuelve un string ordenado \n
    """
    my_string = ""
    full_chain = str("metadata={\'Direccion\': \' \', \'Coordenadas\': \' \', \'Horario\': \' \', \'Calificacion\': \' \', \'Query\': \'Hoteles\'}")
    try:
        list_of_docs = list(docs_object)
        for a in list_of_docs:
            to_str = str(a)
            to_str = to_str.replace("page_content=", "").replace(full_chain, "")
            my_string = my_string + to_str + '\n'
        new_docs = my_string.strip()
        
        return new_docs[:30000]
    
    except:
        return my_string
    
def get_docs_from_location(query, location, opciones):
    df_maps = get_maps(query, location)
    docs = similarity(query, df_maps, opciones)
    docs_str = text_with_format(docs)
    return docs_str