from redfish_controller import (get_all_chassis_data,
                                redfish_factory)
from redfish_schema import RedfishAction
from langchain_agent.chains.redfish_action_chain import load_redfish_action_chain
from langchain_agent.chains.chatbot_chain import load_chatbot_chain
import json
import re

def clean_llm_json(output: str) -> str:
    """
    Cleans code block formatting and ensures valid JSON string.
    Strips ```json ... ``` and ``` ... ``` markers.
    """
    # Remove code block markers
    cleaned = re.sub(r"^```(?:json)?\s*", "", output.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


async def get_agent_response(query: str):
    # fetch the latest resource state with get_all_chassis_data()
    resources = {}
    resources = await get_all_chassis_data()

    # print(resources)

    if resources == {}:
        return {
            "error": "No active OpenBMC resources (Chassis' Temperature/Voltage/Power) found."
        }

    # get llm response
    chain = load_redfish_action_chain()

    # parse response into dict
    response = chain.run(resources=json.dumps(resources), query=query)

    response = clean_llm_json(response)

    # pass the action to the redfish_factory()
    try:
        action = RedfishAction(**json.loads(response))
        print("Agent Decision:\n", action.model_dump_json(indent=2))

        # call respective Redfish apis
        return redfish_factory(action)

    except Exception as e:
        print(f"Invalid response: {response}\nError: {e}")
