import asyncio
import json
import logging
import os
import re
import aiohttp
import backoff

from dhisana.schemas.sales import LeadsQueryFilters, CompanyQueryFilters
from dhisana.utils.assistant_tool_tag import assistant_tool
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List, Optional, Tuple, Union

from dhisana.utils.clean_properties import cleanup_properties

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_apollo_access_token(tool_config: Optional[List[Dict]] = None) -> Tuple[str, bool]:
    """
    Retrieves an Apollo access token from tool configuration or environment variables.

    Args:
        tool_config (list): Optional tool configuration payload provided to the tool.

    Returns:
        Tuple[str, bool]: A tuple containing the token string and a boolean flag indicating
            whether the token represents an OAuth bearer token (``True``) or an API key (``False``).

    Raises:
        ValueError: If the Apollo integration has not been configured.
    """
    token: Optional[str] = None
    is_oauth = False

    if tool_config:
        apollo_config = next(
            (item for item in tool_config if item.get("name") == "apollo"), None
        )
        if apollo_config:
            config_map = {
                item["name"]: item.get("value")
                for item in apollo_config.get("configuration", [])
                if item
            }

            raw_oauth = config_map.get("oauth_tokens")
            if isinstance(raw_oauth, str):
                try:
                    raw_oauth = json.loads(raw_oauth)
                except Exception:
                    raw_oauth = None
            if isinstance(raw_oauth, dict):
                token = (
                    raw_oauth.get("access_token")
                    or raw_oauth.get("token")
                )
                if token:
                    is_oauth = True

            if not token:
                direct_access_token = config_map.get("access_token")
                if direct_access_token:
                    token = direct_access_token
                    is_oauth = True

            if not token:
                api_key = config_map.get("apiKey") or config_map.get("api_key")
                if api_key:
                    token = api_key
                    is_oauth = False
        else:
            logger.warning("No 'apollo' config item found in tool_config.")

    if not token:
        env_oauth_token = os.getenv("APOLLO_ACCESS_TOKEN")
        if env_oauth_token:
            token = env_oauth_token
            is_oauth = True

    if not token:
        env_api_key = os.getenv("APOLLO_API_KEY")
        if env_api_key:
            token = env_api_key
            is_oauth = False

    if not token:
        logger.error("Apollo integration is not configured.")
        raise ValueError(
            "Apollo integration is not configured. Please configure the connection to Apollo in Integrations."
        )

    return token, is_oauth


@assistant_tool
@backoff.on_exception(
    backoff.expo,
    aiohttp.ClientResponseError,
    max_tries=2,
    giveup=lambda e: e.status != 429,
    factor=10,
)
async def enrich_person_info_from_apollo(
    linkedin_url: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    fetch_valid_phone_number: Optional[bool] = False,
    tool_config: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Fetch a person's details from Apollo using LinkedIn URL, email, or phone number.
    
    Parameters:
    - **linkedin_url** (*str*, optional): LinkedIn profile URL of the person.
    - **email** (*str*, optional): Email address of the person.
    - **phone** (*str*, optional): Phone number of the person.
    - **fetch_valid_phone_number** (*bool*, optional): If True, include phone numbers in the API response. Defaults to False.

    Returns:
    - **dict**: JSON response containing person information.
    """
    logger.info("Entering enrich_person_info_from_apollo")

    token, is_oauth = get_apollo_access_token(tool_config)

    if not linkedin_url and not email and not phone:
        logger.warning("No linkedin_url, email, or phone provided. At least one is required.")
        return {'error': "At least one of linkedin_url, email, or phone must be provided"}

    headers = {"Content-Type": "application/json"}
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token

    data = {}
    if linkedin_url:
        logger.debug(f"LinkedIn URL provided: {linkedin_url}")
        data['linkedin_url'] = linkedin_url
    if email:
        logger.debug(f"Email provided: {email}")
        data['email'] = email
    if phone:
        logger.debug(f"Phone provided: {phone}")
        data['phone_numbers'] = [phone]  # Apollo expects a list for phone numbers
    
    # Add reveal_phone_number parameter if fetch_valid_phone_number is True
    if fetch_valid_phone_number:
        logger.debug("fetch_valid_phone_number flag is True, including phone numbers in API response")
        data['reveal_phone_number'] = True

    url = 'https://api.apollo.io/api/v1/people/match'

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                logger.debug(f"Received response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    logger.info("Successfully retrieved person info from Apollo.")
                    return result
                elif response.status == 429:
                    msg = "Rate limit exceeded"
                    logger.warning(msg)
                    await asyncio.sleep(30)
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=msg,
                        headers=response.headers
                    )
                else:
                    result = await response.json()
                    logger.warning(f"enrich_person_info_from_apollo error: {result}")
                    return {'error': result}
        except Exception as e:
            logger.exception("Exception occurred while fetching person info from Apollo.")
            return {'error': str(e)}


@backoff.on_exception(
    backoff.expo,
    aiohttp.ClientResponseError,
    max_tries=2,
    giveup=lambda e: e.status != 429,
    factor=10,
)
async def lookup_person_in_apollo_by_name(
    full_name: str,
    company_name: Optional[str] = None,
    tool_config: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Fetch a person's details from Apollo using their full name and optionally company name.

    Parameters:
    - **full_name** (*str*): Full name of the person.
    - **company_name** (*str*, optional): Name of the company where the person works.
    - **tool_config** (*list*, optional): Tool configuration for API keys.

    Returns:
    - **dict**: JSON response containing person information.
    """
    logger.info("Entering lookup_person_in_apollo_by_name")

    if not full_name:
        logger.warning("No full_name provided.")
        return {'error': "Full name is required"}

    token, is_oauth = get_apollo_access_token(tool_config)
    headers = {"Content-Type": "application/json"}
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token

    # Construct the query payload
    data = {
        "q_keywords": f"{full_name} {company_name}" if company_name else full_name,
        "page": 1,
        "per_page": 10
    }

    url = 'https://api.apollo.io/api/v1/mixed_people/search'
    logger.debug(f"Making request to Apollo with payload: {data}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                logger.debug(f"Received response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    logger.info("Successfully looked up person by name on Apollo.")
                    return result
                elif response.status == 429:
                    msg = "Rate limit exceeded"
                    logger.warning(msg)
                    await asyncio.sleep(30)
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=msg,
                        headers=response.headers
                    )
                else:
                    result = await response.json()
                    logger.warning(f"lookup_person_in_apollo_by_name error: {result}")
                    return {'error': result}
        except Exception as e:
            logger.exception("Exception occurred while looking up person by name.")
            return {'error': str(e)}

@assistant_tool
@backoff.on_exception(
    backoff.expo,
    aiohttp.ClientResponseError,
    max_tries=2,
    giveup=lambda e: e.status != 429,
    factor=30,
)
async def enrich_organization_info_from_apollo(
    organization_domain: Optional[str] = None,
    tool_config: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Fetch an organization's details from Apollo using the organization domain.
    
    Parameters:
    - **organization_domain** (*str*, optional): Domain of the organization.

    Returns:
    - **dict**: JSON response containing organization information.
    """
    logger.info("Entering enrich_organization_info_from_apollo")

    token, is_oauth = get_apollo_access_token(tool_config)

    if not organization_domain:
        logger.warning("No organization domain provided.")
        return {'error': "organization domain must be provided"}

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "accept": "application/json"
    }
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token

    url = f'https://api.apollo.io/api/v1/organizations/enrich?domain={organization_domain}'
    logger.debug(f"Making GET request to Apollo for organization domain: {organization_domain}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                logger.debug(f"Received response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    logger.info("Successfully retrieved organization info from Apollo.")
                    return result
                elif response.status == 429:
                    msg = "Rate limit exceeded"
                    logger.warning(msg)
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=msg,
                        headers=response.headers
                    )
                else:
                    result = await response.json()
                    logger.warning(f"Error from Apollo while enriching org info: {result}")
                    return {'error': result}
        except Exception as e:
            logger.exception("Exception occurred while fetching organization info from Apollo.")
            return {'error': str(e)}



@backoff.on_exception(
    backoff.expo,
    aiohttp.ClientResponseError,
    max_tries=5,
    giveup=lambda e: e.status != 429,
    factor=2,
)
async def fetch_apollo_data(session, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    logger.info("Entering fetch_apollo_data")
    logger.debug("Making POST request to Apollo.")
    async with session.post(url, headers=headers, json=payload) as response:
        logger.debug(f"Received response status: {response.status}")
        if response.status == 200:
            result = await response.json()
            logger.info("Successfully fetched data from Apollo.")
            return result
        elif response.status == 429:
            msg = "Rate limit exceeded"
            logger.warning(msg)
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=msg,
                headers=response.headers
            )
        else:
            logger.error(f"Unexpected status code {response.status} from Apollo. Raising exception.")
            response.raise_for_status()


async def search_people_with_apollo(
    tool_config: Optional[List[Dict[str, Any]]] = None,
    dynamic_payload: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    logger.info("Entering search_people_with_apollo")

    if not dynamic_payload:
        logger.warning("No payload given; returning empty result.")
        return []

    token, is_oauth = get_apollo_access_token(tool_config)
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
    }
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token

    url = "https://api.apollo.io/api/v1/mixed_people/search"
    logger.info(f"Sending payload to Apollo (single page): {json.dumps(dynamic_payload, indent=2)}")

    async with aiohttp.ClientSession() as session:
        data = await fetch_apollo_data(session, url, headers, dynamic_payload)
        if not data:
            logger.error("No data returned from Apollo.")
            return []

        people = data.get("people", [])
        contacts = data.get("contacts", [])
        return people + contacts

def fill_in_properties_with_preference(input_user_properties: dict, person_data: dict) -> dict:
    """
    For each property:
      - If input_user_properties already has a non-empty value, keep it.
      - Otherwise, take the value from person_data if available.
    """

    def is_empty(value):
        """Returns True if the value is None, empty string, or only whitespace."""
        return value is None or (isinstance(value, str) and not value.strip())

    # Full name
    # Because `person_data.get("name")` has precedence over input_user_properties,
    # we only update it if input_user_properties is empty/None for "full_name".
    if is_empty(input_user_properties.get("full_name")) and person_data.get("name"):
        input_user_properties["full_name"] = person_data["name"]

    # First name
    if is_empty(input_user_properties.get("first_name")) and person_data.get("first_name"):
        input_user_properties["first_name"] = person_data["first_name"]

    # Last name
    if is_empty(input_user_properties.get("last_name")) and person_data.get("last_name"):
        input_user_properties["last_name"] = person_data["last_name"]

    # Email
    if is_empty(input_user_properties.get("email")):
        input_user_properties["email"] = person_data.get("email", "")

    # Phone
    if is_empty(input_user_properties.get("phone")):
        # person_data["contact"] might not be defined, so we chain get calls
        input_user_properties["phone"] = ((person_data.get("contact", {}) or {})
                                          .get("sanitized_phone", ""))

    # LinkedIn URL
    if is_empty(input_user_properties.get("user_linkedin_url")) and person_data.get("linkedin_url"):
        input_user_properties["user_linkedin_url"] = person_data["linkedin_url"]

    # Organization data
    org_data = person_data.get("organization") or {}
    if org_data:
        # Primary domain
        if is_empty(input_user_properties.get("primary_domain_of_organization")) and org_data.get("primary_domain"):
            input_user_properties["primary_domain_of_organization"] = org_data["primary_domain"]

        # Organization name
        if is_empty(input_user_properties.get("organization_name")) and org_data.get("name"):
            input_user_properties["organization_name"] = org_data["name"]

        # Organization LinkedIn URL
        if is_empty(input_user_properties.get("organization_linkedin_url")) and org_data.get("linkedin_url"):
            input_user_properties["organization_linkedin_url"] = org_data["linkedin_url"]

        # Organization website
        if is_empty(input_user_properties.get("organization_website")) and org_data.get("website_url"):
            input_user_properties["organization_website"] = org_data["website_url"]

        # Keywords
        if is_empty(input_user_properties.get("keywords")) and org_data.get("keywords"):
            input_user_properties["keywords"] = ", ".join(org_data["keywords"])

    # Title / Job Title
    if is_empty(input_user_properties.get("job_title")) and person_data.get("title"):
        input_user_properties["job_title"] = person_data["title"]

    # Headline
    if is_empty(input_user_properties.get("headline")) and person_data.get("headline"):
        input_user_properties["headline"] = person_data["headline"]

    # Summary about lead (fallback to headline if summary is missing, or if none set yet)
    if is_empty(input_user_properties.get("summary_about_lead")) and person_data.get("headline"):
        input_user_properties["summary_about_lead"] = person_data["headline"]

    # City/State -> lead_location (avoid literal "None")
    city = person_data.get("city")
    state = person_data.get("state")
    parts = []
    for value in (city, state):
        if value is None:
            continue
        s = str(value).strip()
        if not s or s.lower() == "none":
            continue
        parts.append(s)
    lead_location = ", ".join(parts) if parts else None
    if is_empty(input_user_properties.get("lead_location")) and lead_location:
        input_user_properties["lead_location"] = lead_location

    # Filter out placeholder emails
    if input_user_properties.get("email") and "domain.com" in input_user_properties["email"].lower():
        input_user_properties["email"] = ""

    return input_user_properties


async def search_leads_with_apollo(
    query: LeadsQueryFilters,
    max_items_to_search: Optional[int] = 10,
    example_url: Optional[str] = None,
    tool_config: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict]:
    logger.info("Entering search_leads_with_apollo")

    max_items = max_items_to_search or 10
    if max_items > 2500:
        logger.warning("Requested max_items_to_search > 2000, overriding to 2000.")
        max_items = 2500

    # -----------------------------
    # A) example_url -> parse query
    # -----------------------------
    if example_url:
        logger.debug(f"example_url provided: {example_url}")

        parsed_url = urlparse(example_url)
        query_string = parsed_url.query

        if not query_string and "?" in parsed_url.fragment:
            fragment_query = parsed_url.fragment.split("?", 1)[1]
            query_string = fragment_query

        query_params = parse_qs(query_string)

        page_list = query_params.get("page", ["1"])
        per_page_list = query_params.get("per_page", ["100"])

        try:
            page_val = int(page_list[-1])
        except ValueError:
            page_val = 1

        try:
            per_page_val = int(per_page_list[-1])
        except ValueError:
            per_page_val = min(max_items, 100)

        dynamic_payload: Dict[str, Any] = {
            "page": page_val,
            "per_page": per_page_val,
        }

        # You can augment this mapping if you have more custom fields
        mapping = {
            "personLocations": "person_locations",
            "organizationNumEmployeesRanges": "organization_num_employees_ranges",
            "personTitles": "person_titles",
            # Important: handle personNotTitles as well
            "personNotTitles": "person_not_titles",

            "qOrganizationJobTitles": "q_organization_job_titles",
            "sortAscending": "sort_ascending",
            "sortByField": "sort_by_field",
            "contactEmailStatusV2": "contact_email_status",
            "searchSignalIds": "search_signal_ids",
            "organizationLatestFundingStageCd": "organization_latest_funding_stage_cd",
            "revenueRange[max]": "revenue_range_max",
            "revenueRange[min]": "revenue_range_min",
            "currentlyUsingAnyOfTechnologyUids": "currently_using_any_of_technology_uids",
            "organizationIndustries": "organization_industries",
            "organizationIndustryTagIds": "organization_industry_tag_ids",
            "notOrganizationIds": "not_organization_ids",
            "qOrganizationDomainsList": "q_organization_domains_list",
        }

        for raw_key, raw_value_list in query_params.items():
            # Strip off [] if present so we can do a snake_case transform
            if raw_key.endswith("[]"):
                key = raw_key[:-2]
            else:
                key = raw_key

            # If the mapping has this raw_key or the stripped key, use it:
            if raw_key in mapping:
                key = mapping[raw_key]
            elif key in mapping:
                key = mapping[key]
            else:
                # fallback: convert camelCase -> snake_case
                key = re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()

            # If there's only one item, let's pull it out as a single str
            # otherwise, keep it a list
            if len(raw_value_list) == 1:
                final_value: Union[str, List[str]] = raw_value_list[0]
            else:
                final_value = raw_value_list

            # Known booleans
            if key in ("sort_ascending",):
                val_lower = str(final_value).lower()
                final_value = val_lower in ("true", "1", "yes")

            # Parse numeric fields
            if key in ("page", "per_page"):
                try:
                    final_value = int(final_value)
                except ValueError:
                    pass

            # Join arrays for q_keywords
            if key == "q_keywords" and isinstance(final_value, list):
                final_value = " ".join(final_value)

            # ---------------------------------------------
            # Force any param that originated from `[]` to
            # be a list, even if there's only one value.
            # Or handle known array-likely parameters:
            # ---------------------------------------------
            if raw_key.endswith("[]"):
                # Guaranteed to treat it as a list
                if isinstance(final_value, str):
                    final_value = [final_value]
            else:
                # Or if we have a known array param
                if key in (
                    "person_locations",
                    "person_titles",
                    "person_seniorities",
                    "organization_locations",
                    "q_organization_domains_list",
                    "contact_email_status",
                    "organization_ids",
                    "organization_num_employees_ranges",
                    "person_not_titles",  # <--- added so single item is forced into list
                    "q_organization_job_titles",
                    "organization_latest_funding_stage_cd",
                    "organization_industries",
                    "organization_industry_tag_ids",
                ):
                    if isinstance(final_value, str):
                        final_value = [final_value]

            dynamic_payload[key] = final_value

        # Remove invalid sort
        if dynamic_payload.get("sort_by_field") == "[none]":
            dynamic_payload.pop("sort_by_field")

        if "per_page" not in query_params:
            dynamic_payload["per_page"] = min(max_items, 100)

    # -----------------------------------
    # B) No example_url -> build from `query`
    # -----------------------------------
    else:
        dynamic_payload = {
            "page": 1,
            "per_page": min(max_items, 100),
        }
        
        # Only add fields if they have values (don't pass empty defaults)
        if query.person_current_titles:
            dynamic_payload["person_titles"] = query.person_current_titles
        if query.person_locations:
            dynamic_payload["person_locations"] = query.person_locations
        if query.filter_by_signals:
            dynamic_payload["search_signal_ids"] = query.filter_by_signals
        if query.search_keywords:
            dynamic_payload["q_keywords"] = query.search_keywords
        
        # Only add employee ranges if explicitly provided
        if query.organization_num_employees_ranges:
            dynamic_payload["organization_num_employees_ranges"] = query.organization_num_employees_ranges
        elif query.min_employees_in_organization is not None or query.max_employees_in_organization is not None:
            min_emp = query.min_employees_in_organization or 1
            max_emp = query.max_employees_in_organization or 1000000
            dynamic_payload["organization_num_employees_ranges"] = [f"{min_emp},{max_emp}"]
        
        if query.job_openings_with_titles:
            dynamic_payload["q_organization_job_titles"] = query.job_openings_with_titles
        if query.latest_funding_stages:
            dynamic_payload["organization_latest_funding_stage_cd"] = query.latest_funding_stages
        if query.sort_by_field is not None:
            dynamic_payload["sort_by_field"] = query.sort_by_field
        if query.sort_ascending is not None:
            dynamic_payload["sort_ascending"] = query.sort_ascending
        if query.person_seniorities:
            dynamic_payload["person_seniorities"] = query.person_seniorities
        if query.industries:
            dynamic_payload["organization_industries"] = query.industries
        if query.company_industry_tag_ids:
            dynamic_payload["organization_industry_tag_ids"] = query.company_industry_tag_ids
        # Add company domains to include in search
        if query.company_domains:
            dynamic_payload["q_organization_domains_list"] = query.company_domains

    # -----------------------------
    # C) Fetch multiple pages
    # -----------------------------
    all_people: List[Dict[str, Any]] = []
    total_fetched = 0

    current_page = int(dynamic_payload.get("page", 1))
    per_page = int(dynamic_payload.get("per_page", min(max_items, 100)))

    while total_fetched < max_items:
        page_payload = dict(dynamic_payload)
        page_payload["page"] = current_page
        page_payload["per_page"] = per_page

        logger.debug(f"Fetching page {current_page}, per_page {per_page}")
        page_results = await search_people_with_apollo(tool_config=tool_config, dynamic_payload=page_payload)

        if not page_results:
            break

        all_people.extend(page_results)
        page_count = len(page_results)
        total_fetched += page_count

        if page_count < per_page or total_fetched >= max_items:
            break

        current_page += 1

    logger.info(f"Fetched a total of {len(all_people)} items from Apollo (across pages).")

    # -----------------------------------------------
    # Convert raw results -> dictionary objects
    # -----------------------------------------------
    leads: List[Dict[str, Any]] = []
    for user_data_from_apollo in all_people:
        person_data = user_data_from_apollo

        input_user_properties: Dict[str, Any] = {}

        additional_props = input_user_properties.get("additional_properties") or {}
        input_user_properties = fill_in_properties_with_preference(input_user_properties, person_data)
        
        person_data = cleanup_properties(person_data)    
        
        additional_props["apollo_person_data"] = json.dumps(person_data)
        input_user_properties["additional_properties"] = additional_props

        leads.append(input_user_properties)

    logger.info(f"Converted {len(leads)} Apollo records into dictionaries.")
    return leads


async def search_leads_with_apollo_page(
    query: LeadsQueryFilters,
    page: Optional[int] = 1,
    per_page: Optional[int] = 25,
    example_url: Optional[str] = None,
    tool_config: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Fetch a single page of Apollo leads using ``page`` and ``per_page``.

    This helper performs one request to the Apollo API and returns the fetched
    leads along with comprehensive pagination metadata.

    Args:
        query: LeadsQueryFilters object containing search criteria
        page: Page number to fetch (1-indexed, defaults to 1)
        per_page: Number of results per page (defaults to 25)
        example_url: Optional URL to parse search parameters from
        tool_config: Optional tool configuration for API keys

    Returns:
        Dict containing:
        - current_page: The current page number
        - per_page: Number of results per page
        - total_entries: Total number of results available
        - total_pages: Total number of pages available
        - has_next_page: Boolean indicating if more pages exist
        - next_page: Next page number (None if no more pages)
        - results: List of lead dictionaries for this page
    """
    logger.info("Entering search_leads_with_apollo_page")

    if example_url:
        parsed_url = urlparse(example_url)
        query_string = parsed_url.query

        if not query_string and "?" in parsed_url.fragment:
            fragment_query = parsed_url.fragment.split("?", 1)[1]
            query_string = fragment_query

        query_params = parse_qs(query_string)

        dynamic_payload: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        mapping = {
            "personLocations": "person_locations",
            "organizationNumEmployeesRanges": "organization_num_employees_ranges",
            "personTitles": "person_titles",
            "personNotTitles": "person_not_titles",
            "qOrganizationJobTitles": "q_organization_job_titles",
            "sortAscending": "sort_ascending",
            "sortByField": "sort_by_field",
            "contactEmailStatusV2": "contact_email_status",
            "searchSignalIds": "search_signal_ids",
            "organizationLatestFundingStageCd": "organization_latest_funding_stage_cd",
            "revenueRange[max]": "revenue_range_max",
            "revenueRange[min]": "revenue_range_min",
            "currentlyUsingAnyOfTechnologyUids": "currently_using_any_of_technology_uids",
            "organizationIndustries": "organization_industries",
            "organizationIndustryTagIds": "organization_industry_tag_ids",
            "notOrganizationIds": "not_organization_ids",
            "qOrganizationDomainsList": "q_organization_domains_list",
        }

        for raw_key, raw_value_list in query_params.items():
            if raw_key.endswith("[]"):
                key = raw_key[:-2]
            else:
                key = raw_key

            if raw_key in mapping:
                key = mapping[raw_key]
            elif key in mapping:
                key = mapping[key]
            else:
                key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()

            if len(raw_value_list) == 1:
                final_value: Union[str, List[str]] = raw_value_list[0]
            else:
                final_value = raw_value_list

            if key in ("sort_ascending",):
                val_lower = str(final_value).lower()
                final_value = val_lower in ("true", "1", "yes")

            if key in ("page", "per_page"):
                try:
                    final_value = int(final_value)
                except ValueError:
                    pass

            if key == "q_keywords" and isinstance(final_value, list):
                final_value = " ".join(final_value)

            if raw_key.endswith("[]"):
                if isinstance(final_value, str):
                    final_value = [final_value]
            else:
                if key in (
                    "person_locations",
                    "person_titles",
                    "person_seniorities",
                    "organization_locations",
                    "q_organization_domains_list",
                    "contact_email_status",
                    "organization_ids",
                    "organization_num_employees_ranges",
                    "person_not_titles",
                    "q_organization_job_titles",
                    "organization_latest_funding_stage_cd",
                    "organization_industries",
                    "organization_industry_tag_ids",
                ):
                    if isinstance(final_value, str):
                        final_value = [final_value]

            dynamic_payload[key] = final_value

        if dynamic_payload.get("sort_by_field") == "[none]":
            dynamic_payload.pop("sort_by_field")

    # -----------------------------------
    # B) No example_url -> build from `query`
    # -----------------------------------
    else:
        dynamic_payload = {}
        
        # Only add fields if they have values (don't pass empty defaults)
        if query.person_current_titles:
            dynamic_payload["person_titles"] = query.person_current_titles
        if query.person_locations:
            dynamic_payload["person_locations"] = query.person_locations
        if query.filter_by_signals:
            dynamic_payload["search_signal_ids"] = query.filter_by_signals
        if query.search_keywords:
            dynamic_payload["q_keywords"] = query.search_keywords
        
        # Only add employee ranges if explicitly provided
        if query.organization_num_employees_ranges:
            dynamic_payload["organization_num_employees_ranges"] = query.organization_num_employees_ranges
        elif query.min_employees_in_organization is not None or query.max_employees_in_organization is not None:
            min_emp = query.min_employees_in_organization or 1
            max_emp = query.max_employees_in_organization or 1000000
            dynamic_payload["organization_num_employees_ranges"] = [f"{min_emp},{max_emp}"]
        
        if query.job_openings_with_titles:
            dynamic_payload["q_organization_job_titles"] = query.job_openings_with_titles
        if query.latest_funding_stages:
            dynamic_payload["organization_latest_funding_stage_cd"] = query.latest_funding_stages
        if query.sort_by_field is not None:
            dynamic_payload["sort_by_field"] = query.sort_by_field
        if query.sort_ascending is not None:
            dynamic_payload["sort_ascending"] = query.sort_ascending
        if query.q_organization_keyword_tags:
            dynamic_payload["q_organization_keyword_tags"] = query.q_organization_keyword_tags
            
        if query.q_not_organization_keyword_tags:
            dynamic_payload["q_not_organization_keyword_tags"] = query.q_not_organization_keyword_tags
        if query.industries:
            dynamic_payload["organization_industries"] = query.industries
        if query.company_industry_tag_ids:
            dynamic_payload["organization_industry_tag_ids"] = query.company_industry_tag_ids

        # Add company domains to include in search (Apollo API: q_organization_domains_list[])
        if query.company_domains:
            dynamic_payload["q_organization_domains_list"] = query.company_domains

    page_payload = dict(dynamic_payload)
    page_payload["page"] = page
    page_payload["per_page"] = per_page

    print(f"Fetching Apollo page {page} with per_page {per_page}..."
          f" Payload: {json.dumps(page_payload, indent=2)}")

    # Get the full Apollo API response with pagination metadata
    token, is_oauth = get_apollo_access_token(tool_config)
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
    }
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token

    url = "https://api.apollo.io/api/v1/mixed_people/search"
    
    async with aiohttp.ClientSession() as session:
        apollo_response = await fetch_apollo_data(session, url, headers, page_payload)
        if not apollo_response:
            return {"current_page": page, "per_page": per_page, "total_entries": 0, "total_pages": 0, "has_next_page": False, "results": []}

        # Extract pagination metadata
        pagination = apollo_response.get("pagination", {})
        current_page = pagination.get("page", page)
        total_entries = pagination.get("total_entries", 0)
        total_pages = pagination.get("total_pages", 0)
        per_page_actual = pagination.get("per_page", per_page)
        
        # Determine if there are more pages
        has_next_page = current_page < total_pages
        
        # Extract people and contacts
        people = apollo_response.get("people", [])
        contacts = apollo_response.get("contacts", [])
        page_results = people + contacts

    leads: List[Dict[str, Any]] = []
    for person_data in page_results:
        input_user_properties: Dict[str, Any] = {}
        additional_props = input_user_properties.get("additional_properties") or {}
        input_user_properties = fill_in_properties_with_preference(input_user_properties, person_data)
        person_data = cleanup_properties(person_data)
        additional_props["apollo_person_data"] = json.dumps(person_data)
        input_user_properties["additional_properties"] = additional_props
        leads.append(input_user_properties)

    logger.info(f"Converted {len(leads)} Apollo records into dictionaries (single page mode). Page {current_page} of {total_pages}")
    
    return {
        "current_page": current_page,
        "per_page": per_page_actual,
        "total_entries": total_entries,
        "total_pages": total_pages,
        "has_next_page": has_next_page,
        "next_page": current_page + 1 if has_next_page else None,
        "results": leads
    }

@assistant_tool
async def get_organization_domain_from_apollo(
    organization_id: str,
    tool_config: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Fetch an organization's domain from Apollo using the organization ID.

    Parameters:
    - organization_id (str): ID of the organization.

    Returns:
    - dict: Contains the organization's ID and domain, or an error message.
    """
    logger.info("Entering get_organization_domain_from_apollo")

    if not organization_id:
        logger.warning("No organization_id provided.")
        return {'error': 'organization_id must be provided'}

    try:
        result = await get_organization_details_from_apollo(organization_id, tool_config=tool_config)
        if 'error' in result:
            return result
        domain = result.get('primary_domain')
        if domain:
            logger.info("Successfully retrieved domain from Apollo organization details.")
            return {'organization_id': organization_id, 'domain': domain}
        else:
            logger.warning("Domain not found in the organization details.")
            return {'error': 'Domain not found in the organization details'}
    except Exception as e:
        logger.exception("Exception occurred in get_organization_domain_from_apollo.")
        return {'error': str(e)}


@assistant_tool
@backoff.on_exception(
    backoff.expo,
    aiohttp.ClientResponseError,
    max_tries=3,
    giveup=lambda e: e.status != 429,
    factor=60,
)
async def get_organization_details_from_apollo(
    organization_id: str,
    tool_config: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Fetch an organization's details from Apollo using the organization ID.

    Parameters:
    - organization_id (str): ID of the organization.

    Returns:
    - dict: Organization details or an error message.
    """
    logger.info("Entering get_organization_details_from_apollo")

    token, is_oauth = get_apollo_access_token(tool_config)
    if not organization_id:
        logger.warning("No organization_id provided.")
        return {'error': "Organization ID must be provided"}

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Accept": "application/json"
    }
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token

    url = f'https://api.apollo.io/api/v1/organizations/{organization_id}'
    logger.debug(f"Making GET request to Apollo for organization ID: {organization_id}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                logger.debug(f"Received response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    org_details = result.get('organization', {})
                    if org_details:
                        logger.info("Successfully retrieved organization details from Apollo.")
                        return org_details
                    else:
                        logger.warning("Organization details not found in the response.")
                        return {'error': 'Organization details not found in the response'}
                elif response.status == 429:
                    msg = "Rate limit exceeded"
                    limit_minute = response.headers.get('x-rate-limit-minute')
                    limit_hourly = response.headers.get('x-rate-limit-hourly')
                    limit_daily = response.headers.get('x-rate-limit-daily')
                    logger.info(f"get_organization_details_from_apollo x-rate-limit-minute: {limit_minute}")
                    logger.info(f"get_organization_details_from_apollo x-rate-limit-hourly: {limit_hourly}")
                    logger.info(f"get_organization_details_from_apollo x-rate-limit-daily: {limit_daily}")
                    logger.warning(msg)
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=msg,
                        headers=response.headers
                    )
                else:
                    result = await response.json()
                    logger.warning(f"get_organization_details_from_apollo error: {result}")
                    return {'error': result}
        except Exception as e:
            logger.exception("Exception occurred while fetching organization details from Apollo.")
            return {'error': str(e)}


async def enrich_user_info_with_apollo(
    input_user_properties: Dict[str, Any],
    tool_config: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Enriches the user info (input_user_properties) with data from Apollo.
    Attempts direct enrichment if LinkedIn URL or email is provided; otherwise,
    performs a name-based search. Updates the user_properties dictionary in place.

    Parameters:
    - input_user_properties (Dict[str, Any]): A dictionary with user details.
    - tool_config (List[Dict], optional): Apollo tool configuration.

    Returns:
    - Dict[str, Any]: Updated input_user_properties with enriched data from Apollo.
    """
    logger.info("Entering enrich_user_info_with_apollo")

    if not input_user_properties:
        logger.warning("No input_user_properties provided; returning empty dict.")
        return {}

    linkedin_url = input_user_properties.get("user_linkedin_url", "")
    email = input_user_properties.get("email", "")
    user_data_from_apollo = None

    logger.debug(f"Properties => LinkedIn URL: {linkedin_url}, Email: {email}")

    # If LinkedIn url or email is present, attempt direct enrichment
    if linkedin_url or email:
        try:
            user_data_from_apollo = await enrich_person_info_from_apollo(
                linkedin_url=linkedin_url,
                email=email,
                tool_config=tool_config
            )
        except Exception:
            logger.exception("Exception occurred while enriching person info from Apollo by LinkedIn or email.")
    else:
        # Fallback to name-based lookup
        first_name = input_user_properties.get("first_name", "")
        last_name = input_user_properties.get("last_name", "")
        full_name = input_user_properties.get("full_name", f"{first_name} {last_name}").strip()
        company = input_user_properties.get("organization_name", "")

        if not full_name:
            logger.warning("No full_name or (first_name + last_name) provided.")
            input_user_properties["found_user_in_apollo"] = False
            return input_user_properties

        logger.debug(f"Looking up Apollo by name: {full_name}, company: {company}")
        try:
            search_result = await lookup_person_in_apollo_by_name(
                full_name=full_name,
                company_name=company,
                tool_config=tool_config
            )

            # Extract people and contacts from the search result
            people = search_result.get("people", [])
            contacts = search_result.get("contacts", [])
            results = people + contacts
            logger.info(f"Name-based lookup returned {len(results)} results from Apollo.")

            for person in results:
                person_name = person.get("name", "").lower()
                person_first_name = person.get("first_name", "").lower()
                person_last_name = person.get("last_name", "").lower()
                person_company = (person.get("organization", {}) or {}).get("name", "").lower()

                # Match the full name or first/last name and company
                if (
                    (person_name == full_name.lower() or
                     (person_first_name == first_name.lower() and person_last_name == last_name.lower()))
                    and (not company or person_company == company.lower())
                ):
                    logger.info(f"Found matching person {person.get('name')} in Apollo. Enriching data.")
                    linkedin_url = person.get("linkedin_url", "")
                    if linkedin_url:
                        try:
                            user_data_from_apollo = await enrich_person_info_from_apollo(
                                linkedin_url=linkedin_url,
                                tool_config=tool_config
                            )
                        except Exception:
                            logger.exception("Exception occurred during second stage Apollo enrichment.")
                    if user_data_from_apollo:
                        break
        except Exception:
            logger.exception("Exception occurred while performing name-based lookup in Apollo.")

    if not user_data_from_apollo:
        logger.debug("No user data returned from Apollo.")
        input_user_properties["found_user_in_apollo"] = False
        return input_user_properties

    # At this point, user_data_from_apollo likely has "person" key
    person_data = user_data_from_apollo.get("person", {})
    additional_props = input_user_properties.get("additional_properties") or {}
    

    # Fill missing contact info if not already present
    if not input_user_properties.get("email"):
        input_user_properties["email"] = person_data.get("email", "")
    if not input_user_properties.get("phone"):
        input_user_properties["phone"] = (person_data.get("contact", {}) or {}).get("sanitized_phone", "")

    # Map fields
    if person_data.get("name"):
        input_user_properties["full_name"] = person_data["name"]
    if person_data.get("first_name"):
        input_user_properties["first_name"] = person_data["first_name"]
    if person_data.get("last_name"):
        input_user_properties["last_name"] = person_data["last_name"]
    if person_data.get("linkedin_url"):
        input_user_properties["user_linkedin_url"] = person_data["linkedin_url"]

    if person_data.get("organization"):
        org_data = person_data["organization"] or {}
        if org_data.get("primary_domain"):
            input_user_properties["primary_domain_of_organization"] = org_data["primary_domain"]
        if org_data.get("name"):
            input_user_properties["organization_name"] = org_data["name"]
        if org_data.get("linkedin_url"):
            input_user_properties["organization_linkedin_url"] = org_data["linkedin_url"]
        if org_data.get("website_url"):
            input_user_properties["organization_website"] = org_data["website_url"]
        if org_data.get("keywords"):
            input_user_properties["keywords"] = ", ".join(org_data["keywords"])

    if person_data.get("title"):
        input_user_properties["job_title"] = person_data["title"]
    if person_data.get("headline"):
        input_user_properties["headline"] = person_data["headline"]
        # If there's no summary_about_lead, reuse the person's headline
        if not input_user_properties.get("summary_about_lead"):
            input_user_properties["summary_about_lead"] = person_data["headline"]

    # Derive location (avoid literal "None")
    city = person_data.get("city")
    state = person_data.get("state")
    parts = []
    for value in (city, state):
        if value is None:
            continue
        s = str(value).strip()
        if not s or s.lower() == "none":
            continue
        parts.append(s)
    lead_location = ", ".join(parts)
    if lead_location:
        input_user_properties["lead_location"] = lead_location

    # Verify name match
    first_matched = bool(
        input_user_properties.get("first_name")
        and person_data.get("first_name") == input_user_properties["first_name"]
    )
    last_matched = bool(
        input_user_properties.get("last_name")
        and person_data.get("last_name") == input_user_properties["last_name"]
    )
    if first_matched and last_matched:
        logger.info("Matching user found and data enriched from Apollo.")
        input_user_properties["found_user_in_apollo"] = True
    
    person_data = cleanup_properties(person_data)
    additional_props["apollo_person_data"] = json.dumps(person_data)
    input_user_properties["additional_properties"] = additional_props

    return input_user_properties


async def search_companies_with_apollo(
    tool_config: Optional[List[Dict[str, Any]]] = None,
    dynamic_payload: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Search for companies using Apollo's organizations/search endpoint.
    
    Args:
        tool_config: Apollo API configuration
        dynamic_payload: Search parameters for the API call
        
    Returns:
        List of company/organization dictionaries
    """
    logger.info("Entering search_companies_with_apollo")

    if not dynamic_payload:
        logger.warning("No payload given; returning empty result.")
        return []

    token, is_oauth = get_apollo_access_token(tool_config)
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
    }
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token

    url = "https://api.apollo.io/api/v1/organizations/search"
    logger.info(f"Sending payload to Apollo organizations endpoint (single page): {json.dumps(dynamic_payload, indent=2)}")

    async with aiohttp.ClientSession() as session:
        data = await fetch_apollo_data(session, url, headers, dynamic_payload)
        if not data:
            logger.error("No data returned from Apollo organizations search.")
            return []

        organizations = data.get("organizations", [])
        accounts = data.get("accounts", [])  # Apollo sometimes returns accounts as well
        return organizations + accounts


def fill_in_company_properties(company_data: dict) -> dict:
    """
    Convert Apollo company/organization data into a standardized format.
    
    Args:
        company_data: Raw company data from Apollo API
        
    Returns:
        Dictionary matching the SmartList `Account` schema shape.
    """
    def _parse_keywords(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if "," in text:
                return [part.strip() for part in text.split(",") if part.strip()]
            return [text]
        return [value]

    def _parse_compact_number(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        text = text.replace("$", "").replace(",", "").strip()
        multiplier = 1.0
        suffix = text[-1:].upper()
        if suffix in ("K", "M", "B"):
            multiplier = {"K": 1e3, "M": 1e6, "B": 1e9}[suffix]
            text = text[:-1].strip()
        try:
            return float(text) * multiplier
        except ValueError:
            return None

    annual_revenue = (
        company_data.get("organization_revenue")
        if company_data.get("organization_revenue") is not None
        else company_data.get("annual_revenue")
    )
    annual_revenue = _parse_compact_number(annual_revenue)
    if annual_revenue is None:
        annual_revenue = _parse_compact_number(company_data.get("organization_revenue_printed"))

    # Try multiple fields for company size/employee count
    company_size = (
        company_data.get("estimated_num_employees")
        or company_data.get("num_employees")
        or company_data.get("employee_count")
        or company_data.get("employees_count")
        or company_data.get("headcount")
    )
    if company_size is not None:
        try:
            company_size = int(company_size)
        except (TypeError, ValueError):
            company_size = None

    founded_year = company_data.get("founded_year")
    if founded_year is not None:
        try:
            founded_year = int(founded_year)
        except (TypeError, ValueError):
            founded_year = None

    primary_phone = company_data.get("primary_phone")
    primary_phone_number = None
    if isinstance(primary_phone, dict):
        primary_phone_number = primary_phone.get("number") or primary_phone.get(
            "sanitized_number"
        )

    phone = (
        primary_phone_number
        or company_data.get("phone")
        or company_data.get("primary_phone_number")
        or company_data.get("sanitized_phone")
    )

    # Try multiple fields for industry
    industry = company_data.get("industry")
    if not industry and isinstance(company_data.get("industries"), list):
        industries = [str(x).strip() for x in company_data["industries"] if str(x).strip()]
        industry = industries[0] if industries else None
    # Some Apollo responses have industry_tag_id but not industry name
    if not industry and company_data.get("industry_tag_id"):
        industry = company_data.get("industry_tag_id")

    billing_street = (
        company_data.get("street_address")
        or company_data.get("billing_street")
        or company_data.get("address")
        or company_data.get("raw_address")
    )

    # Determine ownership from publicly traded info
    ownership = company_data.get("ownership")
    if not ownership:
        if company_data.get("publicly_traded_symbol") or company_data.get("publicly_traded_exchange"):
            ownership = "public"

    # Parse market cap
    market_cap = _parse_compact_number(company_data.get("market_cap"))

    # Build account dictionary with ProxyCurl-compatible field names
    account: Dict[str, Any] = {
        # Primary identifiers - use ProxyCurl-compatible names
        "name": company_data.get("name"),  # Keep for backward compatibility
        "organization_name": company_data.get("name"),  # ProxyCurl-compatible
        "domain": company_data.get("primary_domain"),  # Keep for backward compatibility
        "primary_domain_of_organization": company_data.get("primary_domain"),  # ProxyCurl-compatible
        "website": company_data.get("website_url"),  # Keep for backward compatibility
        "organization_website": company_data.get("website_url"),  # ProxyCurl-compatible
        "organization_linkedin_url": company_data.get("linkedin_url"),
        
        # Contact info
        "phone": phone,
        "fax": company_data.get("fax") or company_data.get("fax_number"),
        
        # Business details - use ProxyCurl-compatible names
        "industry": industry,  # Keep for backward compatibility
        "organization_industry": industry,  # ProxyCurl-compatible
        "company_size": company_size,  # Keep for backward compatibility
        "organization_size": company_size,  # ProxyCurl-compatible
        "founded_year": founded_year,
        "annual_revenue": annual_revenue,
        "type": company_data.get("type") or company_data.get("organization_type"),
        "ownership": ownership,
        "description": company_data.get("description") or company_data.get("short_description"),
        
        # Address info
        "billing_street": billing_street,
        "billing_city": company_data.get("city"),
        "billing_state": company_data.get("state"),
        "billing_zip": company_data.get("postal_code")
        or company_data.get("zip")
        or company_data.get("zipcode"),
        "billing_country": company_data.get("country"),
        
        # Build organization_hq_location like ProxyCurl does
        "organization_hq_location": ", ".join(filter(None, [
            company_data.get("city"),
            company_data.get("state"),
            company_data.get("country")
        ])) or None,
        
        # Other fields
        "keywords": _parse_keywords(company_data.get("keywords")),
        "tags": [],
        "notes": [],
        "additional_properties": {
            "apollo_organization_id": company_data.get("id"),
            "logo_url": company_data.get("logo_url"),
            "facebook_url": company_data.get("facebook_url"),
            "twitter_url": company_data.get("twitter_url"),
            "angellist_url": company_data.get("angellist_url"),
            "crunchbase_url": company_data.get("crunchbase_url"),
            "blog_url": company_data.get("blog_url"),
            "funding_stage": company_data.get("latest_funding_stage"),
            "total_funding": company_data.get("total_funding"),
            "technology_names": company_data.get("technology_names"),
            "primary_phone": primary_phone if isinstance(primary_phone, dict) else None,
            "raw_address": company_data.get("raw_address"),
            "organization_revenue_printed": company_data.get("organization_revenue_printed"),
            "publicly_traded_symbol": company_data.get("publicly_traded_symbol"),
            "publicly_traded_exchange": company_data.get("publicly_traded_exchange"),
            "market_cap": market_cap,
            "market_cap_printed": company_data.get("market_cap"),
            "sic_codes": company_data.get("sic_codes"),
            "naics_codes": company_data.get("naics_codes"),
            "languages": company_data.get("languages"),
            "alexa_ranking": company_data.get("alexa_ranking"),
            "linkedin_uid": company_data.get("linkedin_uid"),
            "headcount_6_month_growth": company_data.get("organization_headcount_six_month_growth"),
            "headcount_12_month_growth": company_data.get("organization_headcount_twelve_month_growth"),
            "headcount_24_month_growth": company_data.get("organization_headcount_twenty_four_month_growth"),
            "apollo_organization_data": json.dumps(cleanup_properties(company_data)),
        },
        "research_summary": None,
        "enchrichment_status": None,
    }

    return account


@assistant_tool
async def search_companies_with_apollo_page(
    query: CompanyQueryFilters,
    page: Optional[int] = 1,
    per_page: Optional[int] = 25,
    example_url: Optional[str] = None,
    tool_config: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Fetch a single page of Apollo companies using ``page`` and ``per_page``.

    This helper performs one request to the Apollo API and returns the fetched
    companies along with comprehensive pagination metadata.

    Args:
        query: CompanyQueryFilters object containing search criteria
        page: Page number to fetch (1-indexed, defaults to 1)
        per_page: Number of results per page (defaults to 25)
        example_url: Optional URL to parse search parameters from
        tool_config: Optional tool configuration for API keys

    Returns:
        Dict containing:
        - current_page: The current page number
        - per_page: Number of results per page
        - total_entries: Total number of results available
        - total_pages: Total number of pages available
        - has_next_page: Boolean indicating if more pages exist
        - next_page: Next page number (None if no more pages)
        - results: List of company dictionaries for this page
    """
    logger.info("Entering search_companies_with_apollo_page")

    if example_url:
        parsed_url = urlparse(example_url)
        query_string = parsed_url.query

        if not query_string and "?" in parsed_url.fragment:
            fragment_query = parsed_url.fragment.split("?", 1)[1]
            query_string = fragment_query

        query_params = parse_qs(query_string)

        dynamic_payload: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        # Organization-specific URL parameter mapping
        mapping = {
            "organizationLocations": "organization_locations",
            "organizationNumEmployeesRanges": "organization_num_employees_ranges",
            "organizationIndustries": "organization_industries",
            "organizationIndustryTagIds": "organization_industry_tag_ids",
            "qKeywords": "q_keywords",
            "qOrganizationDomainsList": "q_organization_domains_list",
            "sortAscending": "sort_ascending",
            "sortByField": "sort_by_field",
            "organizationLatestFundingStageCd": "organization_latest_funding_stage_cd",
            "revenueRange[max]": "revenue_range_max",
            "revenueRange[min]": "revenue_range_min",
            "currentlyUsingAnyOfTechnologyUids": "currently_using_any_of_technology_uids",
            "organizationIds": "organization_ids",
            "notOrganizationIds": "not_organization_ids",
            "qOrganizationSearchListId": "q_organization_search_list_id",
            "qNotOrganizationSearchListId": "q_not_organization_search_list_id",
        }

        for raw_key, raw_value_list in query_params.items():
            if raw_key.endswith("[]"):
                key = raw_key[:-2]
            else:
                key = raw_key

            if raw_key in mapping:
                key = mapping[raw_key]
            elif key in mapping:
                key = mapping[key]
            else:
                key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()

            if len(raw_value_list) == 1:
                final_value: Union[str, List[str]] = raw_value_list[0]
            else:
                final_value = raw_value_list

            if key in ("sort_ascending",):
                val_lower = str(final_value).lower()
                final_value = val_lower in ("true", "1", "yes")

            if key in ("page", "per_page", "revenue_range_min", "revenue_range_max"):
                try:
                    final_value = int(final_value)
                except ValueError:
                    pass

            if key == "q_organization_keyword_tags":
                # Handle both string and list inputs, split by comma if string
                if isinstance(final_value, str):
                    # Split by comma and strip whitespace
                    final_value = [tag.strip() for tag in final_value.split(",") if tag.strip()]
                elif isinstance(final_value, list):
                    # If it's already a list, flatten any comma-separated items
                    flattened = []
                    for item in final_value:
                        if isinstance(item, str) and "," in item:
                            flattened.extend([tag.strip() for tag in item.split(",") if tag.strip()])
                        else:
                            flattened.append(item)
                    final_value = flattened

            if raw_key.endswith("[]"):
                if isinstance(final_value, str):
                    final_value = [final_value]
            else:
                if key in (
                    "organization_locations",
                    "organization_industries",
                    "organization_industry_tag_ids",
                    "q_organization_domains_list",
                    "q_organization_keyword_tags",
                    "organization_ids",
                    "not_organization_ids",
                    "organization_num_employees_ranges",
                    "currently_using_any_of_technology_uids",
                    "organization_latest_funding_stage_cd",
                ):
                    if isinstance(final_value, str):
                        final_value = [final_value]

            dynamic_payload[key] = final_value

        if dynamic_payload.get("sort_by_field") == "[none]":
            dynamic_payload.pop("sort_by_field")

    # -----------------------------------
    # B) No example_url -> build from `query`
    # -----------------------------------
    else:
        dynamic_payload = {}
         
        # Only add fields if they have values (Apollo doesn't like empty arrays)
        if query.organization_locations:
            dynamic_payload["organization_locations"] = query.organization_locations
        if query.organization_industries:
            dynamic_payload["organization_industries"] = query.organization_industries
        if query.organization_industry_tag_ids:
            dynamic_payload["organization_industry_tag_ids"] = query.organization_industry_tag_ids
            
        # Handle employee ranges
        employee_ranges = []
        if query.organization_num_employees_ranges:
            employee_ranges = query.organization_num_employees_ranges
        elif query.min_employees or query.max_employees:
            employee_ranges = [f"{query.min_employees or 1},{query.max_employees or 1000}"]
        
        if employee_ranges:
            dynamic_payload["organization_num_employees_ranges"] = employee_ranges

        # Add optional parameters only if they have values
        def _normalize_string_list(value: Any) -> List[str]:
            if value is None:
                return []
            if isinstance(value, str):
                return [part.strip() for part in value.split(",") if part.strip()]
            if isinstance(value, list):
                normalized: List[str] = []
                for item in value:
                    if item is None:
                        continue
                    text = str(item).strip()
                    if not text:
                        continue
                    normalized.extend([part.strip() for part in text.split(",") if part.strip()])
                return normalized
            text = str(value).strip()
            return [text] if text else []

        if query.q_keywords:
            keywords = _normalize_string_list(query.q_keywords)
            if keywords:
                dynamic_payload["q_keywords"] = " ".join(keywords)

        org_keyword_tags = _normalize_string_list(query.q_organization_keyword_tags)
        if org_keyword_tags:
            dynamic_payload["q_organization_keyword_tags"] = org_keyword_tags

        not_org_keyword_tags = _normalize_string_list(query.q_not_organization_keyword_tags)
        if not_org_keyword_tags:
            dynamic_payload["q_not_organization_keyword_tags"] = not_org_keyword_tags
         
        if query.q_organization_domains:
            dynamic_payload["q_organization_domains_list"] = query.q_organization_domains
        if query.revenue_range_min is not None:
            dynamic_payload["revenue_range_min"] = query.revenue_range_min
        if query.revenue_range_max is not None:
            dynamic_payload["revenue_range_max"] = query.revenue_range_max
        if query.organization_latest_funding_stage_cd:
            dynamic_payload["organization_latest_funding_stage_cd"] = query.organization_latest_funding_stage_cd
        if query.currently_using_any_of_technology_uids:
            dynamic_payload["currently_using_any_of_technology_uids"] = query.currently_using_any_of_technology_uids
        if query.organization_ids:
            dynamic_payload["organization_ids"] = query.organization_ids
        if query.not_organization_ids:
            dynamic_payload["not_organization_ids"] = query.not_organization_ids
        if query.q_organization_search_list_id:
            dynamic_payload["q_organization_search_list_id"] = query.q_organization_search_list_id
        if query.q_not_organization_search_list_id:
            dynamic_payload["q_not_organization_search_list_id"] = query.q_not_organization_search_list_id
        if query.sort_by_field is not None:
            dynamic_payload["sort_by_field"] = query.sort_by_field
        if query.sort_ascending is not None:
            dynamic_payload["sort_ascending"] = query.sort_ascending

    # Remove sorting parameters that may not be supported by organizations endpoint
    if "sort_by_field" in dynamic_payload:
        dynamic_payload.pop("sort_by_field")
    if "sort_ascending" in dynamic_payload:
        dynamic_payload.pop("sort_ascending")

    page_payload = dict(dynamic_payload)
    page_payload["page"] = page
    page_payload["per_page"] = per_page
    
    # Clean up the payload - remove empty arrays and None values that Apollo doesn't like
    cleaned_payload = {}
    for key, value in page_payload.items():
        if value is not None:
            if isinstance(value, list):
                # Only include non-empty lists
                if value:
                    cleaned_payload[key] = value
            else:
                cleaned_payload[key] = value
    
    # Ensure page and per_page are always included
    cleaned_payload["page"] = page
    cleaned_payload["per_page"] = per_page

    print(f"Fetching Apollo companies page {page} with per_page {per_page}..."
          f" Payload: {json.dumps(cleaned_payload, indent=2)}")

    # Get the full Apollo API response with pagination metadata
    token, is_oauth = get_apollo_access_token(tool_config)
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
    }
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token

    url = "https://api.apollo.io/api/v1/organizations/search"
    
    async with aiohttp.ClientSession() as session:
        apollo_response = await fetch_apollo_data(session, url, headers, cleaned_payload)
        if not apollo_response:
            return {
                "current_page": page, 
                "per_page": per_page, 
                "total_entries": 0, 
                "total_pages": 0, 
                "has_next_page": False, 
                "results": []
            }

        # Extract pagination metadata
        pagination = apollo_response.get("pagination", {})
        current_page = pagination.get("page", page)
        total_entries = pagination.get("total_entries", 0)
        total_pages = pagination.get("total_pages", 0)
        per_page_actual = pagination.get("per_page", per_page)
        
        # Determine if there are more pages
        has_next_page = current_page < total_pages
        
        # Extract organizations and accounts
        organizations = apollo_response.get("organizations", [])
        accounts = apollo_response.get("accounts", [])
        page_results = organizations + accounts

    companies: List[Dict[str, Any]] = []
    for company_data in page_results:
        company_properties = fill_in_company_properties(company_data)
        companies.append(company_properties)

    logger.info(f"Converted {len(companies)} Apollo company records into standardized dictionaries (single page mode). Page {current_page} of {total_pages}")
    
    return {
        "current_page": current_page,
        "per_page": per_page_actual,
        "total_entries": total_entries,
        "total_pages": total_pages,
        "has_next_page": has_next_page,
        "next_page": current_page + 1 if has_next_page else None,
        "results": companies
    }


def _extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from a URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        The extracted domain or None if extraction fails
    """
    if not url:
        return None
    
    try:
        # Handle URLs without scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain if domain else None
    except Exception:
        return None


def _extract_linkedin_company_identifier(linkedin_url: str) -> Optional[str]:
    """
    Extract the company identifier from a LinkedIn company URL.
    
    Args:
        linkedin_url: LinkedIn company URL (e.g., https://www.linkedin.com/company/microsoft)
        
    Returns:
        The company identifier (e.g., 'microsoft') or None if extraction fails
    """
    if not linkedin_url:
        return None
    
    try:
        # Normalize the URL
        url = linkedin_url.strip().rstrip('/')
        
        # Handle various LinkedIn URL formats
        # https://www.linkedin.com/company/microsoft
        # https://linkedin.com/company/microsoft/
        # linkedin.com/company/microsoft
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        # Look for 'company' in path and get the next segment
        if 'company' in path_parts:
            company_idx = path_parts.index('company')
            if company_idx + 1 < len(path_parts):
                return path_parts[company_idx + 1]
        
        return None
    except Exception:
        return None


@assistant_tool
@backoff.on_exception(
    backoff.expo,
    aiohttp.ClientResponseError,
    max_tries=2,
    giveup=lambda e: e.status != 429,
    factor=10,
)
async def search_organization_by_linkedin_or_domain(
    linkedin_url: Optional[str] = None,
    domain: Optional[str] = None,
    tool_config: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Search for an organization in Apollo using LinkedIn URL or domain and return
    standardized organization information.
    
    This function uses Apollo's mixed_companies/search endpoint to find companies
    by their LinkedIn URL or domain, then transforms the result into a standardized
    organization information format.
    
    Parameters:
    - **linkedin_url** (*str*, optional): LinkedIn company URL 
        (e.g., https://www.linkedin.com/company/microsoft)
    - **domain** (*str*, optional): Company domain (e.g., microsoft.com)
    
    At least one of linkedin_url or domain must be provided.
    
    Returns:
    - **dict**: Standardized organization information containing:
        - name: Company name
        - domain: Primary domain
        - website: Company website URL
        - phone: Primary phone number
        - industry: Primary industry
        - company_size: Number of employees
        - founded_year: Year company was founded
        - annual_revenue: Annual revenue
        - organization_linkedin_url: LinkedIn company URL
        - billing_street, billing_city, billing_state, billing_zip, billing_country: Address info
        - description: Company description
        - keywords: List of keywords/tags
        - additional_properties: Additional Apollo-specific data
        - error: Error message if search fails
    """
    logger.info("Entering search_organization_by_linkedin_or_domain")
    
    if not linkedin_url and not domain:
        logger.warning("No linkedin_url or domain provided. At least one is required.")
        return {'error': "At least one of linkedin_url or domain must be provided"}
    
    token, is_oauth = get_apollo_access_token(tool_config)
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }
    if is_oauth:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Api-Key"] = token
    
    # Build the search payload
    payload: Dict[str, Any] = {
        "page": 1,
        "per_page": 25,  # Get more results to improve matching
    }
    
    # Add LinkedIn URL filter if provided
    if linkedin_url:
        # Extract the company identifier for keyword search
        company_identifier = _extract_linkedin_company_identifier(linkedin_url)
        
        # Normalize the LinkedIn URL for matching
        normalized_linkedin = linkedin_url.strip().rstrip('/')
        if not normalized_linkedin.startswith(('http://', 'https://')):
            normalized_linkedin = 'https://' + normalized_linkedin
        
        # Use q_organization_name for better search results
        # The company identifier from LinkedIn URL is usually the company name
        if company_identifier:
            payload["q_organization_name"] = company_identifier
    
    # Add domain filter if provided
    if domain:
        # Clean the domain (remove http://, https://, www., etc.)
        clean_domain = _extract_domain_from_url(domain) or domain
        payload["q_organization_domains_list"] = [clean_domain]
    
    url = "https://api.apollo.io/api/v1/mixed_companies/search"
    logger.debug(f"Making POST request to Apollo organization search with payload: {json.dumps(payload, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                logger.debug(f"Received response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract organizations from response
                    organizations = result.get("organizations", [])
                    accounts = result.get("accounts", [])
                    all_results = organizations + accounts
                    
                    if not all_results:
                        logger.info("No organizations found matching the criteria.")
                        return {
                            'error': 'No organizations found matching the provided criteria',
                            'search_criteria': {
                                'linkedin_url': linkedin_url,
                                'domain': domain
                            }
                        }
                    
                    # Get the best matching organization with confidence tracking
                    best_match = None
                    match_confidence = None
                    match_reason = None
                    
                    # If we have a domain, try to find exact match first (highest confidence)
                    if domain:
                        clean_domain = _extract_domain_from_url(domain) or domain
                        for org in all_results:
                            org_domain = org.get("primary_domain", "")
                            if org_domain and org_domain.lower() == clean_domain.lower():
                                best_match = org
                                match_confidence = "high"
                                match_reason = f"exact_domain_match: {org_domain}"
                                logger.info(f"Found exact domain match: {org.get('name')} with domain {org_domain}")
                                break
                    
                    # If we have LinkedIn URL, try to find exact match
                    if not best_match and linkedin_url:
                        # Extract company identifier from the input URL
                        input_company_id = _extract_linkedin_company_identifier(linkedin_url)
                        
                        for org in all_results:
                            org_linkedin = org.get("linkedin_url", "")
                            org_name = org.get("name", "").lower()
                            org_domain = org.get("primary_domain", "")
                            
                            if org_linkedin:
                                # Extract company identifier from org's LinkedIn URL
                                org_company_id = _extract_linkedin_company_identifier(org_linkedin)
                                
                                # Match by company identifier (e.g., 'walmart' matches 'walmart')
                                if input_company_id and org_company_id:
                                    if input_company_id.lower() == org_company_id.lower():
                                        best_match = org
                                        match_confidence = "high"
                                        match_reason = f"linkedin_identifier_match: {org_company_id}"
                                        logger.info(f"Found LinkedIn identifier match: {org.get('name')} with identifier {org_company_id}")
                                        break
                                
                                # Also try direct URL comparison
                                normalized_input = linkedin_url.lower().rstrip('/').replace('www.', '')
                                normalized_org = org_linkedin.lower().rstrip('/').replace('www.', '')
                                if normalized_input in normalized_org or normalized_org in normalized_input:
                                    best_match = org
                                    match_confidence = "high"
                                    match_reason = f"linkedin_url_match: {org_linkedin}"
                                    logger.info(f"Found LinkedIn URL match: {org.get('name')}")
                                    break
                            
                            # Secondary match: company name contains the identifier
                            if not best_match and input_company_id:
                                # Check if the org name contains the identifier or vice versa
                                input_id_lower = input_company_id.lower().replace('-', ' ').replace('_', ' ')
                                org_name_normalized = org_name.replace('-', ' ').replace('_', ' ')
                                
                                if input_id_lower == org_name_normalized or input_id_lower in org_name_normalized:
                                    best_match = org
                                    match_confidence = "medium"
                                    match_reason = f"name_contains_identifier: {org_name}"
                                    logger.info(f"Found name match: {org.get('name')} matches identifier {input_company_id}")
                                    break
                    
                    # If still no match and we searched by LinkedIn, return error if no exact match found
                    if not best_match and linkedin_url and not domain:
                        input_company_id = _extract_linkedin_company_identifier(linkedin_url)
                        logger.warning(f"No organization found matching LinkedIn URL: {linkedin_url}")
                        # Log what we did find for debugging
                        found_orgs = [{"name": org.get("name"), "linkedin": org.get("linkedin_url"), "domain": org.get("primary_domain")} for org in all_results[:5]]
                        logger.debug(f"Found organizations (first 5): {found_orgs}")
                        return {
                            'error': f'No organization found matching LinkedIn company: {input_company_id or linkedin_url}',
                            'search_criteria': {
                                'linkedin_url': linkedin_url,
                                'domain': domain
                            },
                            'total_results_returned': len(all_results)
                        }
                    
                    # Fall back to first result only if we have other criteria (domain was provided)
                    if not best_match:
                        best_match = all_results[0]
                        match_confidence = "low"
                        match_reason = "fallback_to_first_result"
                        logger.warning(f"Using fallback match (first result): {best_match.get('name')}")
                    
                    # Get the organization ID to fetch full details
                    organization_id = best_match.get("id")
                    full_org_details = best_match  # Default to search result
                    
                    # Fetch full organization details using the organization ID
                    if organization_id:
                        logger.info(f"Fetching full organization details for ID: {organization_id}")
                        try:
                            full_details = await get_organization_details_from_apollo(
                                organization_id=organization_id,
                                tool_config=tool_config,
                            )
                            if full_details and not full_details.get("error"):
                                # Merge the full details with the search result
                                # Full details from organization endpoint has more data
                                full_org_details = full_details
                                logger.info(f"Successfully fetched full organization details for {full_org_details.get('name')}")
                            else:
                                logger.warning(f"Could not fetch full organization details: {full_details.get('error', 'Unknown error')}")
                        except Exception as e:
                            logger.warning(f"Error fetching full organization details: {e}")
                    
                    # Transform to standardized format using the full details
                    standardized_org = fill_in_company_properties(full_org_details)
                    
                    # Add logo_url to additional_properties if available
                    if full_org_details.get("logo_url"):
                        standardized_org["additional_properties"]["logo_url"] = full_org_details.get("logo_url")
                    
                    # Add search metadata
                    standardized_org['search_criteria'] = {
                        'linkedin_url': linkedin_url,
                        'domain': domain
                    }
                    standardized_org['total_matches_found'] = len(all_results)
                    standardized_org['match_confidence'] = match_confidence
                    standardized_org['match_reason'] = match_reason
                    
                    # Log the matched organization details for verification
                    logger.info(f"Successfully found organization: {standardized_org.get('name')} "
                               f"(domain: {standardized_org.get('domain')}, "
                               f"linkedin: {standardized_org.get('organization_linkedin_url')}, "
                               f"confidence: {match_confidence})")
                    return standardized_org
                    
                elif response.status == 429:
                    msg = "Rate limit exceeded"
                    logger.warning(msg)
                    await asyncio.sleep(30)
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=msg,
                        headers=response.headers
                    )
                else:
                    result = await response.json()
                    logger.warning(f"search_organization_by_linkedin_or_domain error: {result}")
                    return {'error': result}
                    
        except aiohttp.ClientResponseError:
            raise
        except Exception as e:
            logger.exception("Exception occurred while searching for organization in Apollo.")
            return {'error': str(e)}
