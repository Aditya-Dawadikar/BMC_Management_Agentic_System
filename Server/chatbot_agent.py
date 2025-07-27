from langchain_agent.chains.chatbot_chain import load_chatbot_chain

async def get_chatbot_response(query: str, mongodb_data: any, s3_data: any):
    chain = load_chatbot_chain()

    response = chain.run(user_message=query, context=mongodb_data, s3_data=s3_data)

    return response
