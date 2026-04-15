from serpapi import GoogleSearch
import time
from pytrends.request import TrendReq
from langchain_openai import OpenAI#import openai
import os
import re


from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI

import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

trends_prompt = "Imagine you are an expert and try to summarize the next news \
    headers in one single spanish short phrase \
        explaining why {trending_search} is relevant today in the news: {headers}"
news_prompt = "Eres un experto en {trending_search} y debes resumir por qué {trending_search} es relevante hoy en las noticias.\
      Si hay más de una noticia, haz notar que estás hablando de más de una noticia. Los encabezados son los siguientes: {headers}"
trends_llm = AzureChatOpenAI(deployment_name=os.environ['DEPLOYMENT_NAME'],
                             model=os.environ['MODEL_NAME'],
                            temperature=0.5,
                            max_tokens=200,
                            n=1)

prompt = PromptTemplate(
        input_variables=["trending_search", "headers"], 
        template=trends_prompt)
news_prompt = PromptTemplate(
        input_variables=["trending_search", "headers"], 
        template=news_prompt)

#import the libraries
import pandas as pd
from pytrends.request import TrendReq
pytrend = TrendReq()
# Get Google Keyword Suggestions
keywords = pytrend.suggestions(keyword='Facebook')
df = pd.DataFrame(keywords)
df.head(5)

def text_to_printable_url(texto):
    # Reemplazar signos de puntuación por caracteres vacíos
    texto = re.sub(r'[!\"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~]', '', texto)
    # Reemplazar caracteres especiales por sus correspondientes sin acento
    texto = re.sub(r'[áÁ]', 'a', texto)
    texto = re.sub(r'[éÉ]', 'e', texto)
    texto = re.sub(r'[íÍ]', 'i', texto)
    texto = re.sub(r'[óÓ]', 'o', texto)
    texto = re.sub(r'[úÚ]', 'u', texto)
    texto = ''.join([c for c in texto if c.isprintable()])
    return texto

def summarize_trend():
    trends_chain = prompt | trends_llm 

    pytrends = TrendReq(hl='en-US', tz=360)
    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        try:
            t_s = pytrends.realtime_trending_searches(pn='MX')[0:3]
            news_list = []

            for t in range(0, len(t_s)):
                trending_search = t_s['title'][t].split(',')[0]
                search = GoogleSearch({
                    "q": f"{trending_search}",   # search search
                    "location": "Mexico",
                    "tbm": "nws",  # news
                    "tbs": "qdr:d", # last 24h
                    "num": 10,
                    "api_key": f"{os.environ['SERPAPI_API_KEY']}"#google search keys
                })

                results = search.get_dict()
                if results.get("news_results") == None:
                    pass
                else:
                    headers = []
                    if len(results.get("news_results")) > 3:
                        for i in list(range(0, 3)):
                            headers.append(results.get("news_results")[i].get('snippet'))
                    else:
                        for i in list(range(0, len(results.get("news_results")))):
                            headers.append(results.get("news_results")[i].get('snippet'))
                    response = trends_chain.invoke({'trending_search': trending_search, 'headers': headers})
                    trends_response = response.content
                    news_list.append(trends_response.strip())
            return news_list

        except Exception as e:
            print(e)
            attempts += 1
            if attempts < max_attempts:
                print(f"Retrying in 1 second (Attempt {attempts} of {max_attempts})...")
                time.sleep(1)

    print(f"Maximum number of retry attempts ({max_attempts}) reached. Unable to fetch data.")
    return []


def search_specific_topic(topic):
    trends_chain = news_prompt | trends_llm 
    search = GoogleSearch({
                "q": f"{topic}",   # search search
                "location": "Mexico",
                "tbm": "nws",  # news
                "tbs": "qdr:d", # last 24h
                "num": 10,
                "api_key": f"{os.environ['SERPAPI_API_KEY']}"#google search keys
            })

    results = search.get_dict()
    if results.get("news_results") == None:
        pass
    else:
        headers = []
        if len(results.get("news_results")) > 3:
            for i in list(range(0, 3)):
                headers.append(results.get("news_results")[i].get('snippet'))
        else:
            for i in list(range(0, len(results.get("news_results")))):
                headers.append(results.get("news_results")[i].get('snippet'))
        print(headers)
        response = trends_chain.invoke({'trending_search': topic, 'headers': headers})
        trends_response = response.content
    return trends_response.strip()

def generate_trending_prompt(news, openai_key):
    llm = OpenAI(temperature=0.1, openai_api_key=openai_key)  
    prompt = llm.invoke(f'Detecta el concepto gráfico que mejor represente la noticia siguiente. Describe en pocas palabras el concepto. Utiliza descripciones puntuales y que evoquen una imagen clara que se relacione con la noticia. Solo dame la descripción, sin usar signos de puntuación. La noticia es: <<<{news}>>> ').strip()
    return prompt