from langchain_agent.chains.query_router_chain import load_query_router_chain
import json

async def get_query_router_response(query:str):
    chain = load_query_router_chain()

    response = chain.run(query= query)

    response = response.strip().strip("```json").strip("```")

    response = json.loads(response)

    return response
