from langchain_agent.chains.preprocessor_chain import load_preprocessor_chain

async def get_preprocessor_response(text: str, todays_date: str):
    chain = load_preprocessor_chain()

    response = chain.run(text=text, todays_date=todays_date)

    return response
