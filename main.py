import json

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL


client = OpenAI(api_key=OPENAI_API_KEY)


INSTRUCTIONS = """
You are a customer operations assistant.

Your job is to answer customer-account questions using
authoritative tool data.

Rules:
- Never invent customer information.
- If customer information is required, use get_customer.
- Do not claim an action happened unless a tool confirms it.
- If the requested information is unavailable, say so clearly.
"""


TOOLS = [
    {
        "type": "function",
        "name": "get_customer",
        "description": (
            "Retrieve authoritative customer information. "
            "Use this when the user asks about a customer's "
            "name, account status, or plan."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The unique customer ID."
                }
            },
            "required": ["customer_id"],
            "additionalProperties": False
        }
    }
]


def get_customer(customer_id: int):
    customers = {
        1842: {
            "name": "Alice",
            "status": "active",
            "plan": "pro"
        },
        2190: {
            "name": "Rahul",
            "status": "active",
            "plan": "basic"
        }
    }

    return customers.get(customer_id)


def execute_tool(name: str, arguments: dict):
    if name == "get_customer":
        return get_customer(**arguments)

    raise ValueError(f"Unknown tool: {name}")


def run_agent(user_input: str):

    input_items = [
        {
            "role": "user",
            "content": user_input
        }
    ]

    while True:

        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=INSTRUCTIONS,
            tools=TOOLS,
            input=input_items,
        )

        # Add the model's output to the conversation.
        input_items += response.output

        # Look for tool calls.
        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # No tool call means the model has finished.
        if not tool_calls:
            return response.output_text

        # Execute every requested tool.
        for tool_call in tool_calls:

            print(
                f"\n[TOOL REQUEST] "
                f"{tool_call.name} "
                f"{tool_call.arguments}"
            )

            arguments = json.loads(tool_call.arguments)

            result = execute_tool(
                tool_call.name,
                arguments
            )

            print(f"[TOOL RESULT] {result}")

            # Send tool result back to the model.
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(result)
                }
            )


def main():

    print("Customer Operations Agent")
    print("Type 'exit' to quit.\n")

    while True:

        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        try:
            answer = run_agent(user_input)

            print(f"\nAgent: {answer}\n")

        except Exception as error:
            print(f"\nERROR: {error}\n")


if __name__ == "__main__":
    main()