
from app.agent.llm_client import llm
from app.agent.langchain_tools import LANGCHAIN_TOOLS
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
import json


# Bind tools to the LLM
tool_enabled_llm = llm.bind_tools(LANGCHAIN_TOOLS)

# System prompt to restrict tool usage
SYSTEM_PROMPT = """You are a data analysis assistant. 

IMPORTANT RULES:
1. You MUST ONLY use the 'dataset_analyst' tool for ALL data-related questions
2. Never try to use other tools like matplotlib, pandas, numpy, or any other library
3. All visualization and analysis requests go through the 'dataset_analyst' tool
4. Do not hallucinate or invent tools that don't exist
5. If the user question is NOT about the current dataset or its columns, DO NOT call any tools.
   Instead, reply with a short text message explaining that you can only analyze the dataset
   and asking the user to rephrase their question in terms of the dataset.

Available tools:
- dataset_analyst: For analyzing datasets, creating visualizations, and computing statistics

Always use the dataset_analyst tool when the user asks about data.

After you receive tool results, use them to answer the user directly.
Do not keep calling tools again and again for the same query."""


def run_agent(query: str, session_id: str = "titanic_default"):
    """
    Executes the LangChain tool-enabled LLM with tool calling.

    The model decides whether to call tools and this function
    handles the tool invocation and returns the final response.
    A safety limit on tool-calling iterations prevents infinite loops.
    """

    # Initial LLM invocation with system prompt
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]
    response = tool_enabled_llm.invoke(messages)
    messages.append(response)

    tool_result_data = None

    # Safety limit to avoid infinite tool-calling loops
    max_tool_iterations = 5
    iteration = 0

    # If the response contains tool calls, execute them
    while getattr(response, "tool_calls", None) and iteration < max_tool_iterations:
        iteration += 1
        tool_calls = response.tool_calls

        for tool_call in tool_calls:
            # Find the tool by name
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # Always enforce the current session_id on tool calls that accept it.
            # This ensures that analysis uses the dataset selected in the frontend,
            # rather than leaving session selection up to the LLM.
            if isinstance(tool_args, dict):
                tool_args["session_id"] = session_id

            # Execute the tool
            from app.agent.langchain_tools import LANGCHAIN_TOOLS

            tool_result = None
            for tool in LANGCHAIN_TOOLS:
                if tool.name == tool_name:
                    tool_result = tool.invoke(tool_args)
                    tool_result_data = tool_result  # Store the tool result
                    break

            # Add a SMALL summary of the tool result to messages (to avoid huge token usage)
            tool_message_content = ""
            try:
                parsed = tool_result
                if isinstance(tool_result, str):
                    parsed = json.loads(tool_result)

                if isinstance(parsed, dict):
                    text_resp = parsed.get("text_response")
                    has_chart = bool(parsed.get("chart"))
                    data = parsed.get("data")

                    # Small preview only
                    if isinstance(data, list):
                        data_preview = data[:3]
                    else:
                        data_preview = data

                    summary = {
                        "text_response": text_resp,
                        "has_chart": has_chart,
                        "data_preview": data_preview,
                    }
                    tool_message_content = json.dumps(summary, default=str)
                else:
                    tool_message_content = str(tool_result)
            except Exception:
                tool_message_content = str(tool_result)

            messages.append(
                ToolMessage(
                    content=tool_message_content,
                    tool_call_id=tool_call["id"],
                )
            )

        # Get next response from LLM, now including tool results
        response = tool_enabled_llm.invoke(messages)
        messages.append(response)

    # Return both the final response and tool result data
    return {
        "response": getattr(response, "content", response),
        "tool_result": tool_result_data,
    }