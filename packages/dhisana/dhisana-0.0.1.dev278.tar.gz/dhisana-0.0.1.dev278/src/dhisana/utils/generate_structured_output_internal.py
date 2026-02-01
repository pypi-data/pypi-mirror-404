import asyncio
import hashlib
import json
import logging
import random
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException
from pydantic import BaseModel

from openai import OpenAIError, RateLimitError
from openai.lib._parsing._completions import type_to_response_format_param

from json_repair import repair_json

from dhisana.utils import cache_output_tools
from dhisana.utils.fetch_openai_config import (
    _extract_config,
    create_async_openai_client,
)

# Import search and scrape utilities for web search tools
try:
    from dhisana.utils.search_router import search_google_with_tools
except Exception:
    async def search_google_with_tools(*a, **k):
        return []

try:
    from dhisana.utils.web_download_parse_tools import get_text_content_from_url
except Exception:
    async def get_text_content_from_url(url: str) -> str:
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# Web search tool definitions for the Responses API
# ──────────────────────────────────────────────────────────────────────────────

SEARCH_GOOGLE_TOOL = {
    "type": "function",
    "name": "search_google",
    "description": "Search Google for information. Returns a list of search results with titles, links, and snippets.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up on Google"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (default: 5, max: 10)"
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

FETCH_URL_CONTENT_TOOL = {
    "type": "function",
    "name": "fetch_url_content",
    "description": "Fetch and extract text content from a URL. Use this to read the full content of a webpage.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch content from"
            }
        },
        "required": ["url"],
        "additionalProperties": False
    }
}


async def _execute_search_google(
    query: str, num_results: int, tool_config: Optional[List[Dict]]
) -> str:
    """Execute Google search and return results as JSON string."""
    try:
        num_results = min(max(num_results, 1), 10)
        raw = await search_google_with_tools(
            query, number_of_results=num_results, offset=0, tool_config=tool_config
        )
        results = []
        if isinstance(raw, list):
            for item in raw:
                try:
                    data = json.loads(item) if isinstance(item, str) else item
                    results.append({
                        "title": data.get("title", ""),
                        "link": data.get("link", ""),
                        "snippet": data.get("snippet", "")
                    })
                except Exception:
                    continue
        return json.dumps(results, default=str)
    except Exception as e:
        logging.warning("search_google tool failed: %s", e)
        return json.dumps({"error": str(e)})


async def _execute_fetch_url_content(url: str) -> str:
    """Fetch URL content and return as string."""
    try:
        content = await get_text_content_from_url(url)
        if content:
            max_len = 15000
            if len(content) > max_len:
                content = content[:max_len] + "\n... [content truncated]"
            return content
        return "Failed to fetch content from URL"
    except Exception as e:
        logging.warning("fetch_url_content tool failed for %s: %s", url, e)
        return f"Error fetching URL: {str(e)}"


async def _execute_web_search_tool(
    tool_name: str, args: dict, tool_config: Optional[List[Dict]]
) -> str:
    """Execute a web search tool and return the result as a string."""
    if tool_name == "search_google":
        query = args.get("query", "")
        num_results = args.get("num_results", 5)
        if not query:
            return json.dumps({"error": "Missing required parameter: query"})
        return await _execute_search_google(query, num_results, tool_config)

    elif tool_name == "fetch_url_content":
        url = args.get("url", "")
        if not url:
            return json.dumps({"error": "Missing required parameter: url"})
        return await _execute_fetch_url_content(url)

    else:
        logging.warning(f"Unknown tool requested: {tool_name}")
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ──────────────────────────────────────────────────────────────────────────────
# 1.  Helper functions
# ──────────────────────────────────────────────────────────────────────────────

def is_context_length_error(error: Exception) -> bool:
    """Check if an error is due to context length being exceeded."""
    error_str = str(error).lower()
    return "context_length_exceeded" in error_str or "context window" in error_str


# ──────────────────────────────────────────────────────────────────────────────
# 2.  Vector-store utilities (unchanged logic, new client factory)
# ──────────────────────────────────────────────────────────────────────────────


async def get_vector_store_object(
    vector_store_id: str, tool_config: Optional[List[Dict]] = None
) -> Dict:
    client_async = create_async_openai_client(tool_config)
    try:
        return await client_async.vector_stores.retrieve(vector_store_id=vector_store_id)
    except OpenAIError as e:
        logging.error(f"Error retrieving vector store {vector_store_id}: {e}")
        return None

async def list_vector_store_files(
    vector_store_id: str, tool_config: Optional[List[Dict]] = None
) -> List:
    client_async = create_async_openai_client(tool_config)
    page = await client_async.vector_stores.files.list(vector_store_id=vector_store_id)
    return page.data


# ──────────────────────────────────────────────────────────────────────────────
# 3.  Core logic – only the client initialisation lines changed
# ──────────────────────────────────────────────────────────────────────────────

async def get_structured_output_internal(
    prompt: str,
    response_format: BaseModel,
    effort: str = "low",
    use_web_search: bool = False,
    model: str = "gpt-5.1-chat",
    tool_config: Optional[List[Dict]] = None,
    use_cache: bool = True
):
    """
    Makes a direct call to the new Responses API for structured output.

    On a 429 (rate-limit) error the call is retried once after
    20 s + random exponential back-off.
    
    If use_web_search=True, uses Google search and URL scraping tools
    to enable web research (works with both OpenAI and Azure OpenAI).
    """
    try:
        # ─── caching bookkeeping ────────────────────────────────────────────
        response_type_str = response_format.__name__
        message_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        response_type_hash = hashlib.md5(response_type_str.encode("utf-8")).hexdigest()
        cache_key = f"{message_hash}:{response_type_hash}"

        if use_cache:
            cached_response = cache_output_tools.retrieve_output(
                "get_structured_output_internal", cache_key
            )
            if cached_response is not None:
                parsed_cached_response = response_format.parse_raw(cached_response)
                return parsed_cached_response, "SUCCESS"

        # ─── JSON schema for function calling ───────────────────────────────
        schema = type_to_response_format_param(response_format)
        json_schema_format = {
            "name": response_type_str,
            "type": "json_schema",
            "schema": schema["json_schema"]["schema"],
        }

        # ─── client initialisation ──────────────────────────────────────────
        client_async = create_async_openai_client(tool_config)

        # ─── Web search path (uses Google search + URL scraping tools) ──────
        if use_web_search:
            return await _get_structured_output_with_web_search(
                client_async=client_async,
                prompt=prompt,
                response_format=response_format,
                json_schema_format=json_schema_format,
                model=model,
                effort=effort,
                tool_config=tool_config,
                cache_key=cache_key,
            )

        # ─── Standard path (no web search) ──────────────────────────────────
        async def _make_request():
            if model.startswith("o"):  # reasoning param only for "o" family
                return await client_async.responses.create(
                    input=[
                        {"role": "system", "content": "You are a helpful AI. Output JSON only."},
                        {"role": "user", "content": prompt},
                    ],
                    model=model,
                    reasoning={"effort": effort},
                    text={"format": json_schema_format},
                    store=False,
                )
            return await client_async.responses.create(
                input=[
                    {"role": "system", "content": "You are a helpful AI. Output JSON only."},
                    {"role": "user", "content": prompt},
                ],
                model=model,
                text={"format": json_schema_format},
                store=False,
            )

        # -------------------------------------------------------------------
        # Call with one retry on 429
        # -------------------------------------------------------------------
        max_retries = 1
        attempt = 0
        while True:
            try:
                completion = await _make_request()
                break  # success → exit loop
            except (RateLimitError, OpenAIError) as e:
                # Check for context length exceeded error
                if is_context_length_error(e):
                    logging.error(f"Context length exceeded: {e}")
                    return f"Context length exceeded: {str(e)}", "CONTEXT_LENGTH_EXCEEDED"
                
                # Detect 429 / rate-limit
                error_str = str(e).lower()
                is_rl = (
                    isinstance(e, RateLimitError)
                    or getattr(e, "status_code", None) == 429
                    or "rate_limit" in error_str
                )
                if is_rl and attempt < max_retries:
                    attempt += 1
                    # 20 s base + exponential jitter
                    wait_time = 20 + random.uniform(0, 2 ** attempt)
                    logging.warning(
                        f"Rate-limit hit (429). Waiting {wait_time:.2f}s then retrying "
                        f"({attempt}/{max_retries})."
                    )
                    await asyncio.sleep(wait_time)
                    continue  # retry once
                logging.error(f"OpenAI API error: {e}")
                return f"OpenAI API error: {str(e)}", "API_ERROR"

        # ─── handle model output ────────────────────────────────────────────
        return _parse_completion_response(completion, response_format, cache_key)

    # Safety fallback: catch any OpenAI errors not caught by inner retry loop
    except OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        if is_context_length_error(e):
            return f"Context length exceeded: {str(e)}", "CONTEXT_LENGTH_EXCEEDED"
        return f"OpenAI API error: {str(e)}", "API_ERROR"
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return f"Unexpected error: {str(e)}", "ERROR"


async def _get_structured_output_with_web_search(
    client_async,
    prompt: str,
    response_format: BaseModel,
    json_schema_format: Dict,
    model: str,
    effort: str,
    tool_config: Optional[List[Dict]],
    cache_key: str,
):
    """
    Handles structured output with web search using Google search and URL scraping tools.
    Works with both OpenAI and Azure OpenAI.
    """
    logging.info(f"[WebSearch] Starting web search structured output: model={model}, effort={effort}")
    logging.debug(f"[WebSearch] Prompt length: {len(prompt)} chars")
    
    tools = [SEARCH_GOOGLE_TOOL, FETCH_URL_CONTENT_TOOL]
    
    system_content = (
        "You are a helpful AI. Output JSON only.\n\n"
        "Web Search Instructions:\n"
        "- Use search_google to find relevant information on the web.\n"
        "- Use fetch_url_content to read the full content of relevant URLs.\n"
        "- After gathering information, provide your response in the required JSON format."
    )
    
    # Build conversation history that we'll extend with tool calls/results
    conversation_history = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt},
    ]
    
    max_tool_iterations = 10
    tool_iteration = 0
    completion = None
    
    while tool_iteration < max_tool_iterations:
        tool_iteration += 1
        logging.info(f"[WebSearch] Tool iteration {tool_iteration}/{max_tool_iterations}, conversation_history length: {len(conversation_history)}")
        
        # Build request with current conversation history
        request = {
            "input": conversation_history,
            "model": model,
            "text": {"format": json_schema_format},
            "tools": tools,
            "store": False,
        }
        
        if model.startswith("o"):
            request["reasoning"] = {"effort": effort}
        
        # Retry logic for rate limits
        for attempt in range(2):
            try:
                logging.debug(f"[WebSearch] Sending request attempt {attempt + 1}")
                completion = await client_async.responses.create(**request)
                logging.info(f"[WebSearch] Response received, output items: {len(completion.output) if completion and completion.output else 0}")
                break
            except (RateLimitError, OpenAIError) as e:
                is_rl = (
                    isinstance(e, RateLimitError)
                    or getattr(e, "status_code", None) == 429
                    or "rate_limit" in str(e).lower()
                )
                if attempt == 0 and is_rl:
                    wait_time = 20 + random.uniform(0, 2.0)
                    logging.warning(f"[WebSearch] Rate-limit hit (429). Waiting {wait_time:.2f}s then retrying.")
                    await asyncio.sleep(wait_time)
                    continue
                logging.error(f"[WebSearch] OpenAI API error: {e}")
                raise HTTPException(status_code=502, detail=f"Error communicating with the OpenAI API: {str(e)}")
        
        if not completion:
            logging.error("[WebSearch] No completion returned after retries")
            raise HTTPException(status_code=502, detail="OpenAI request failed.")
        
        # Check for function tool calls in the response
        tool_calls = []
        for item in (completion.output or []):
            item_type = getattr(item, "type", None)
            logging.debug(f"[WebSearch] Output item type: {item_type}")
            if item_type == "function_call":
                tool_calls.append(item)
        
        if not tool_calls:
            # No tool calls, we have the final response
            logging.info(f"[WebSearch] No tool calls in iteration {tool_iteration}, returning final response")
            break
        
        # Execute tool calls and add results to conversation history
        # Note: With store=False, we can't append raw output items (they have IDs that Azure
        # can't resolve). We must create clean dicts with only the required fields.
        logging.info(f"[WebSearch] Processing {len(tool_calls)} web search tool call(s) in iteration {tool_iteration}")
        
        for tc in tool_calls:
            func_name = getattr(tc, "name", "")
            call_id = getattr(tc, "call_id", "")
            args_str = getattr(tc, "arguments", "{}")
            
            logging.info(f"[WebSearch] Tool call: {func_name}, call_id: {call_id}, args: {args_str[:200]}...")
            
            try:
                args = json.loads(args_str) if args_str else {}
            except json.JSONDecodeError as e:
                logging.warning(f"[WebSearch] Failed to parse tool arguments: {e}")
                args = {}
            
            # Add the function_call to conversation history as a clean dict (no id field)
            # Per OpenAI docs: function_call items need type, call_id, name, arguments
            conversation_history.append({
                "type": "function_call",
                "call_id": call_id,
                "name": func_name,
                "arguments": args_str,
            })
            
            # Execute the tool
            tool_result = await _execute_web_search_tool(func_name, args, tool_config)
            
            # Add tool result to conversation history
            conversation_history.append({
                "type": "function_call_output",
                "call_id": call_id,
                "output": tool_result,
            })
            
            logging.info(f"[WebSearch] Executed tool {func_name}, result length: {len(tool_result)}")
    
    logging.info(f"[WebSearch] Tool loop completed after {tool_iteration} iteration(s)")
    
    # Parse and return the final response
    result, status = _parse_completion_response(completion, response_format, cache_key)
    logging.info(f"[WebSearch] Parse result status: {status}")
    return result, status


def _parse_completion_response(completion, response_format: BaseModel, cache_key: str):
    """Parse completion response and return structured output."""
    logging.debug(f"[ParseResponse] Parsing completion, has output: {bool(completion and completion.output)}")
    
    if completion and completion.output and len(completion.output) > 0:
        logging.debug(f"[ParseResponse] Output items count: {len(completion.output)}")
        raw_text = None
        for out in completion.output:
            logging.debug(f"[ParseResponse] Checking output item type: {out.type}")
            if out.type == "message" and out.content:
                for content_item in out.content:
                    if hasattr(content_item, "text"):
                        raw_text = content_item.text
                        logging.debug(f"[ParseResponse] Found text content, length: {len(raw_text) if raw_text else 0}")
                        break
                    else:
                        logging.warning("[ParseResponse] Request refused: %s", str(content_item))
                        return "Request refused.", "FAIL"
                if raw_text:
                    break

        if not raw_text or not raw_text.strip():
            logging.warning("[ParseResponse] No text returned (possibly refusal or empty response)")
            return "No text returned (possibly refusal or empty response)", "FAIL"

        logging.debug(f"[ParseResponse] Raw text (first 500 chars): {raw_text[:500] if raw_text else 'None'}...")
        
        try:
            parsed_obj = response_format.parse_raw(raw_text)
            cache_output_tools.cache_output(
                "get_structured_output_internal", cache_key, parsed_obj.json()
            )
            logging.info("[ParseResponse] Successfully parsed response")
            return parsed_obj, "SUCCESS"

        except Exception as e:
            logging.warning(f"[ParseResponse] Could not parse JSON from model output: {e}")
            try:
                fixed_json = repair_json(raw_text)
                parsed_obj = response_format.parse_raw(fixed_json)
                cache_output_tools.cache_output(
                    "get_structured_output_internal", cache_key, parsed_obj.json()
                )
                logging.info("[ParseResponse] Successfully parsed response after JSON repair")
                return parsed_obj, "SUCCESS"
            except Exception as e2:
                logging.warning(f"[ParseResponse] JSON repair also failed: {e2}")
                logging.debug(f"[ParseResponse] Raw text that failed parsing: {raw_text[:1000] if raw_text else 'None'}...")
                return raw_text, "FAIL"
    else:
        logging.warning("[ParseResponse] No output returned from completion")
        return "No output returned", "FAIL"



async def get_structured_output_with_mcp(
    prompt: str,
    response_format: BaseModel,
    effort: str = "low",
    use_web_search: bool = False,
    model: str = "gpt-5.1-chat",
    tool_config: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Union[BaseModel, str], str]:
    """
    Sends a JSON-schema-constrained prompt to an OpenAI model, with an MCP
    server configured as a `tool`.

    * If the model returns a tool call that *requires approval*, the function
      immediately returns a minimal object that satisfies `response_format`
      with `"APPROVAL_PENDING"` in `response_summary`, along with the status
      string ``"PENDING_APPROVAL"``.
    * Once the tool has executed (the provider returns `mcp_tool_result`) or
      the model replies directly with the JSON payload, the parsed object is
      cached and returned with status ``"SUCCESS"``.
    * Any MCP tool-listing messages are ignored.
    """
    # ─── Validate MCP configuration ────────────────────────────────────────────
    mcp_cfg = _extract_config(tool_config, "mcpServer") or {}
    server_label: str = mcp_cfg.get("serverLabel", "")
    server_url: str | None = mcp_cfg.get("serverUrl")
    api_key_header_name: str | None = mcp_cfg.get("apiKeyHeaderName")
    api_key_header_value: str | None = mcp_cfg.get("apiKeyHeaderValue")

    if not (server_url and api_key_header_name and api_key_header_value):
        raise HTTPException(400, detail="MCP server configuration incomplete.")

    # ─── Cache key (prompt + schema) ──────────────────────────────────────────
    response_type_str = response_format.__name__
    cache_key = (
        f"{hashlib.md5(prompt.encode()).hexdigest()}:"
        f"{hashlib.md5(response_type_str.encode()).hexdigest()}"
    )
    if (cached := cache_output_tools.retrieve_output("get_structured_output_with_mcp", cache_key)):
        return response_format.parse_raw(cached), "SUCCESS"

    # ─── JSON-schema format for `text` param ──────────────────────────────────
    schema_cfg = type_to_response_format_param(response_format)
    json_schema_format = {
        "name": response_type_str,
        "type": "json_schema",
        "schema": schema_cfg["json_schema"]["schema"],
    }

    # ─── Build tool list ──────────────────────────────────────────────────────
    tools: List[Dict[str, Any]] = [
        {
            "type": "mcp",
            "server_label": server_label,
            "server_url": server_url,
            "headers": {api_key_header_name: api_key_header_value},
            "require_approval": "never"
        }
    ]
    if use_web_search and model.startswith("gpt-"):
        tools.append({"type": "web_search_preview"})

    # ─── Async OpenAI client ──────────────────────────────────────────────────
    client_async = create_async_openai_client(tool_config)

    async def _make_request():
        kwargs: Dict[str, Any] = {
            "input": [
                {"role": "system", "content": "You are a helpful AI. Output JSON only."},
                {"role": "user", "content": prompt},
            ],
            "model": model,
            "text": {"format": json_schema_format},
            "store": False,
            "tools": tools,
            "tool_choice": "required",
        }
        if model.startswith("o"):
            kwargs["reasoning"] = {"effort": effort}
        return await client_async.responses.create(**kwargs)

    # ─── Retry once for 429s ──────────────────────────────────────────────────
    completion = None
    for attempt in range(2):
        try:
            completion = await _make_request()
            break
        except (RateLimitError, OpenAIError) as exc:
            # Check for context length exceeded error
            if is_context_length_error(exc):
                logging.error(f"Context length exceeded: {exc}")
                return f"Context length exceeded: {str(exc)}", "CONTEXT_LENGTH_EXCEEDED"
            
            if attempt == 0 and (
                isinstance(exc, RateLimitError)
                or getattr(exc, "status_code", None) == 429
                or "rate_limit" in str(exc).lower()
            ):
                sleep_for = 20 + random.uniform(0, 2.0)
                logging.warning("429 rate-limit hit; retrying in %.1fs", sleep_for)
                await asyncio.sleep(sleep_for)
                continue
            logging.error("OpenAI API error: %s", exc)
            return f"OpenAI API error: {str(exc)}", "API_ERROR"
    
    if not completion:
        return "OpenAI request retry loop failed", "API_ERROR"

    # ─── Parse the model’s structured output ──────────────────────────────────
    if not (completion and completion.output):
        return "No output returned", "FAIL"

    raw_text: str | None = None
    status: str = "SUCCESS"

    for out in completion.output:
        # 1️⃣  Human approval required
        if out.type == "mcp_approval_request":
            logging.info("Tool call '%s' awaiting approval", out.name)
            placeholder_obj = response_format.parse_obj({"response_summary": "APPROVAL_PENDING"})
            return placeholder_obj, "PENDING_APPROVAL"

        # 2️⃣  Ignore capability listings
        if out.type == "mcp_list_tools":
            continue

        # 3️⃣  Tool finished: provider returned result object
        if out.type == "mcp_tool_result":
            try:
                # If result already matches schema, emit directly
                raw_text = (
                    json.dumps(out.result)
                    if isinstance(out.result, (dict, list))
                    else json.dumps({"response_summary": str(out.result)})
                )
            except Exception:  # pragma: no cover
                raw_text = json.dumps({"response_summary": "TOOL_EXECUTION_COMPLETE"})
            break

        # 4️⃣  Regular assistant message
        if out.type == "message" and out.content:
            for c in out.content:
                if hasattr(c, "text") and c.text:
                    raw_text = c.text
                    break
            if raw_text:
                break

        # 5️⃣  Anything else
        logging.debug("Unhandled output type: %s", out.type)

    if not raw_text or not raw_text.strip():
        return "No response", status

    # ─── Convert JSON -> pydantic object, with repair fallback ────────────────
    try:
        parsed_obj = response_format.parse_raw(raw_text)
    except Exception:
        logging.warning("Initial parse failed; attempting JSON repair")
        parsed_obj = response_format.parse_raw(repair_json(raw_text))

    # ─── Cache & return ───────────────────────────────────────────────────────
    cache_output_tools.cache_output(
        "get_structured_output_with_mcp", cache_key, parsed_obj.json()
    )
    return parsed_obj, status

async def get_structured_output_with_assistant_and_vector_store(
    prompt: str,
    response_format: BaseModel,
    vector_store_id: str,
    effort: str = "low",
    model="gpt-5.1-chat",
    tool_config: Optional[List[Dict]] = None,
    use_cache: bool = True
):
    """
    Same logic, now uses create_async_openai_client().
    """
    try:
        vector_store = await get_vector_store_object(vector_store_id, tool_config)
        if not vector_store:
            return await get_structured_output_internal(
                    prompt, response_format, tool_config=tool_config
                )
            
        files = await list_vector_store_files(vector_store_id, tool_config)
        if not files:
            return await get_structured_output_internal(
                prompt, response_format, tool_config=tool_config
            )

        response_type_str = response_format.__name__
        message_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        response_type_hash = hashlib.md5(response_type_str.encode("utf-8")).hexdigest()
        cache_key = f"{message_hash}:{response_type_hash}"
        
        if use_cache:
            cached_response = cache_output_tools.retrieve_output(
                "get_structured_output_with_assistant_and_vector_store", cache_key
            )
            if cached_response is not None:
                parsed_cached_response = response_format.model_validate_json(cached_response)
                return parsed_cached_response, "SUCCESS"

        schema = type_to_response_format_param(response_format)
        json_schema_format = {
            "name": response_type_str,
            "type": "json_schema",
            "schema": schema["json_schema"]["schema"],
        }

        client_async = create_async_openai_client(tool_config)

        completion = await client_async.responses.create(
            input=[
                {"role": "system", "content": "You are a helpful AI. Output JSON only."},
                {"role": "user", "content": prompt},
            ],
            model=model,
            text={"format": json_schema_format},
            tools=[{"type": "file_search", "vector_store_ids": [vector_store_id]}],
            tool_choice="required",
            store=False,
        )

        if completion and completion.output and len(completion.output) > 0:
            raw_text = None
            for out in completion.output:
                if out.type == "message" and out.content and len(out.content) > 0:
                    raw_text = out.content[0].text
                    break

            if not raw_text or not raw_text.strip():
                return "No response from the model", "FAIL"

            try:
                parsed_obj = response_format.parse_raw(raw_text)
                cache_output_tools.cache_output(
                    "get_structured_output_with_assistant_and_vector_store",
                    cache_key,
                    parsed_obj.json(),
                )
                return parsed_obj, "SUCCESS"
            except Exception:
                logging.warning("Model returned invalid JSON.")
                return raw_text, "FAIL"
        else:
            return "No output returned", "FAIL"

    # Safety fallback: catch any errors not caught during API call
    except OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        if is_context_length_error(e):
            return f"Context length exceeded: {str(e)}", "CONTEXT_LENGTH_EXCEEDED"
        return f"OpenAI API error: {str(e)}", "API_ERROR"
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return f"Unexpected error: {str(e)}", "ERROR"
