"""
Utility functions for interacting with Amazon Bedrock API.
"""
import json
import ast
from typing import Dict, List, Any, Optional, Tuple
import logging
logger = logging.getLogger(__name__)

def count_tokens(
    bedrock_client,
    model_id: str,
    messages: List[dict],
    system_prompts: str = None
) -> Dict[str, int]:
    """
    Count input tokens for a given model, messages, and system prompt using Bedrock's token counting API.
    
    Args:
        bedrock_client: The Bedrock client instance
        model_id (str): The model ID to use
        messages (List[dict]): List of message dicts with role and content
        system_prompts (str, optional): System prompts to use
        
    Returns:
        Dict[str, int]: Dictionary with input token count
    """
    try:
        # Format input for token counting
        formatted_input = {
            "messages": messages,
            "system": [{"text": system_prompts}] if system_prompts else None
        }

        # Call the token counting API
        token_response = bedrock_client.count_tokens(
            modelId=model_id,
            contentType="application/json",
            body=json.dumps(formatted_input)
        )
        
        return {
            "input_tokens": token_response.get("inputTokenCount", 0)
        }
    except Exception as e:
        logger.warning(f"Failed to count tokens: {e}")
        return {"input_tokens": 0}

def handle_bedrock_conversation(
    bedrock_client,
    model_id: str,
    messages: List[dict],
    system_prompts: str = None,
    temperature: float = 0.5,
    top_k: int = 200,
    image_bytes: bytes = None,
    track_tokens: bool = True
) -> Dict:
    """
    Handles conversations with Amazon Bedrock client and tracks token usage.
    
    Args:
        bedrock_client: The Bedrock client instance
        model_id (str): The model ID to use
        messages (List[dict]): List of message dicts with role and content
        system_prompts (str, optional): System prompts to use
        temperature (float, optional): Temperature parameter
        top_k (int, optional): Top-k parameter
        image_bytes (bytes, optional): Image bytes to include
        track_tokens (bool, optional): Whether to track token usage
        
    Returns:
        dict: Response from the model with token usage information
    """
    # Track input tokens if requested
    token_counts = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


    # If image is provided, add it to the last message
    if image_bytes:
        if isinstance(messages[-1]["content"], list):
            messages[-1]["content"].append({
                "image": {
                    "format": "png",
                    "source": {
                        "bytes": image_bytes
                    }
                }
            })
        else:
            messages[-1]["content"] = [{
                "text": messages[-1]["content"]
            }, {
                "image": {
                    "format": "png",
                    "source": {
                        "bytes": image_bytes
                    }
                }
            }]

    # Set up inference parameters
    inference_config = {"temperature": temperature}
    additional_model_fields = {"top_k": top_k}

    # Make the API call
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        system=[{"text": system_prompts}] if system_prompts else None,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )
    
    # Extract token usage from the response if available
    if track_tokens and "usage" in response:
        input_token_count = response.get("usage", {}).get("inputTokens", 0)
        output_token_count = response.get("usage", {}).get("outputTokens", 0)
        total_token_count = response.get("usage", {}).get("totalTokens", 0)
        token_counts["output_tokens"] = int(output_token_count) if output_token_count else token_counts["output_tokens"]
        # Some models may provide the input token count in the response as well 
        token_counts["input_tokens"] = int(input_token_count) if input_token_count else token_counts["input_tokens"]
        token_counts["total_tokens"] = int(total_token_count) if total_token_count else token_counts["total_tokens"]
    
    # Add token counts to the response
    response["token_counts"] = token_counts
    
    return response

def format_messages(
    prompt: str,
    instruction: str = None,
    conversation_history: List[dict] = None,
    system_prompt: str = None
) -> List[dict]:
    """
    Formats messages for Bedrock conversation API.

    Args:
        prompt (str): The main user prompt/question
        instruction (str, optional): Additional instruction to prepend
        conversation_history (List[dict], optional): Previous conversation messages
        system_prompt (str, optional): System prompt to use

    Returns:
        List[dict]: Formatted messages list
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
        
    if conversation_history:
        messages.extend(conversation_history)
        
    final_prompt = f"{instruction}\n{prompt}" if instruction else prompt
    messages.append({"role": "user", "content": final_prompt})
    
    return messages

def parse_llm_response(response_str: str, key: str = 'code') -> Optional[Any]:
    """
    Parses the response from the LLM.
    
    Args:
        response_str (str): The response string from the LLM
        key (str): The key to extract from the parsed response
        
    Returns:
        Any: The extracted value, or None if parsing failed
    """
    try:
        # Using ast.literal_eval for safer evaluation
        response_dict = ast.literal_eval(response_str)
        return response_dict.get(key)
    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {e}. Content: {response_str}")
        # If direct parsing fails, try to extract JSON from markdown code blocks
        try:
            import re
            # Try to find JSON in markdown code blocks
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                json_dict = json.loads(json_str)
                return json_dict.get(key)
        except Exception as e:
            logger.warning(f"Failed to parse JSON from LLM response: {e}. Content: {response_str}")
            
            pass
        
        # Last resort: try to find any dictionary-like structure
        try:
            dict_match = re.search(r"\{[^{}]*\}", response_str)
            if dict_match:
                dict_str = dict_match.group(0)
                dict_obj = ast.literal_eval(dict_str)
                return dict_obj.get(key)
        except Exception:
            return None