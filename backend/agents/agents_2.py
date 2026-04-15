from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, SystemMessage
#from services.trends_service import summarize_trend, search_specific_topic
from services.maps_service import get_docs_from_location
from services.data_analytics_service import insert_sample_data
from langchain_openai import AzureOpenAIEmbeddings
import json
from agents.data_analytics_handler import DataAnalyticsHandler
import logging
import os

from templates.prompts_str import  generic_prompt_str, rag_prompt_str, classifier_prompt_str, waving_prompt_string
logger = logging.getLogger(__name__)
class MultiAgentsBot:
    def __init__(self, vdb_client=None, data_analyst = None):
        self.vdb_client = vdb_client
        self.data_analyst = data_analyst
        ### Deployment name
        self.deployment_name = os.environ['DEPLOYMENT_NAME']

        #### Prompts

        self.generic_prompt =       PromptTemplate(input_variables=["human_input"],
                                             template=generic_prompt_str)
        self.rag_prompt =           ChatPromptTemplate.from_messages(
                                                        [
                                                            ('system', rag_prompt_str),
                                                            ('human', "{input}")
                                                        ]
                                                        )
        self.classifier_prompt =    PromptTemplate(input_variables=["query"]
                                                , template=classifier_prompt_str)
        self.waving_prompt =        PromptTemplate(input_variables=["human_input"],
                                             template=waving_prompt_string)

        ## Llm's
        self.generic_llm =      AzureChatOpenAI(deployment_name=self.deployment_name,
                                   temperature=0.8,
                                   max_tokens=300,
                                   n=1)
        self.rag_llm =          AzureChatOpenAI(deployment_name=self.deployment_name,
                                   temperature=0.5,
                                   max_tokens=500,
                                   n=1)
        self.classifier_llm =   AzureChatOpenAI(deployment_name=self.deployment_name,
                                      temperature=0.1,
                                      max_tokens=100,
                                      n=1)
        self.waving_llm =      AzureChatOpenAI(deployment_name=self.deployment_name,
                                   temperature=0.5,
                                   max_tokens=200,
                                   n=1)
        
        if self.vdb_client is not None:
            self.embeddings_model_runnable = AzureOpenAIEmbeddings(model=os.environ['EMBEDDINGS_MODEL'],
                                   chunk_size=1,
                                   api_version=os.environ['EMBEDDINGS_VERSION']
                                   )
        # Chains
        self.generic_chain =        self.generic_prompt | self.generic_llm
        self.question_answer_chain = create_stuff_documents_chain(self.rag_llm, self.rag_prompt)
        self.waving_chain =         self.waving_prompt | self.waving_llm
        self.classifier_chain =     self.classifier_prompt | self.classifier_llm
    
    def query_generic(self, query, viewed_data=''):
        return self.generic_chain.invoke({'human_input':query, 'viewed_data':viewed_data}).content
    
    def query_rag(self, query, qdrant_retriever, viewed_data=''):
        self.rag_chain = create_retrieval_chain(qdrant_retriever, self.question_answer_chain) #self.rag_prompt | self.rag_llm
        response = self.rag_chain.invoke({'input':query, 'viewed_data':viewed_data})

        # Extraer fuentes de los documentos
        sources = []
        if 'context' in response:
            for doc in response['context']:
                sources.append({
                    'source': doc.metadata.get('source', 'Desconocido'),
                    'page': doc.metadata.get('page', 'N/A')
                })
        
        return {
            'answer': response['answer'],
            'sources': sources
        }

    def query_classifier(self, query):
        return self.classifier_chain.invoke({'query':query}).content

    def query_waving(self, human_input):
        return self.waving_chain.invoke({'human_input': human_input}).content