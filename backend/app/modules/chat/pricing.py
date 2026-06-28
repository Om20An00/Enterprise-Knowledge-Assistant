import tiktoken

def calculate_indexing_cost(chunks):

    price_per_1M_tokens_embedding = 0.06  
    
    encoder = tiktoken.get_encoding("cl100k_base")
  
    total_tokens = 0
    for chunk in chunks:
      
        if hasattr(chunk, 'page_content'):
            text = chunk.page_content
        elif hasattr(chunk, 'text'):
            text = chunk.text
        elif isinstance(chunk, dict):
            text = chunk.get("text", "")
        else:
            text = str(chunk)
        total_tokens += len(encoder.encode(text))
  
    embedding_cost = (total_tokens / 1000000) * price_per_1M_tokens_embedding
    
    return round(embedding_cost, 6)  
    


def calculate_prices(chunks, answer, query, request):
    price_per_1M_tokens_vector = 0.06 
    price_per_1M_tokens_llm_input = 0.15  
    price_per_1M_tokens_llm_output = 0.60  

    encoder = tiktoken.get_encoding("cl100k_base")

    chunks_text = " ".join([chunk.get("text", "") for chunk in chunks])
    llm_input_text = query + " " + chunks_text
    llm_input_tokens = len(encoder.encode(llm_input_text))
 
    llm_output_tokens = len(encoder.encode(answer))
 
    vector_tokens = len(encoder.encode(query))
    
    vector_cost = (vector_tokens / 1000000) * price_per_1M_tokens_vector
    llm_input_cost = (llm_input_tokens / 1000000) * price_per_1M_tokens_llm_input
    llm_output_cost = (llm_output_tokens / 1000000) * price_per_1M_tokens_llm_output
    llm_total_cost = llm_input_cost + llm_output_cost
    

    return [vector_cost, llm_total_cost]
