import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from dhisana.schemas.sales import (
    ContentGenerationContext,
    Lead,
    MessageItem,
    MessageResponse,
    MessageGenerationInstructions,
    SenderInfo
)
from dhisana.utils.assistant_tool_tag import assistant_tool
from dhisana.utils.generate_structured_output_internal import (
    get_structured_output_with_assistant_and_vector_store,
    get_structured_output_internal
)

# ---------------------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------------------
DEFAULT_TRIAGE_MODEL = "gpt-4.1"

# ---------------------------------------------------------------------------------------
# MODEL
# ---------------------------------------------------------------------------------------
class InboundEmailTriageResponse(BaseModel):
    """
    Model representing the structured response for an inbound email triage.
    - triage_status: "AUTOMATIC" or "END_CONVERSATION"
    - triage_reason: Reason text if triage_status == "END_CONVERSATION"
    - response_action_to_take: The recommended next action (e.g. SCHEDULE_MEETING, SEND_REPLY, etc.)
    - response_message: The actual body of the email response to be sent or used for approval.
    """
    triage_status: str  # "AUTOMATIC" or "END_CONVERSATION"
    triage_reason: Optional[str]
    response_action_to_take: str
    response_message: Optional[str]
    meeting_offer_sent: Optional[bool]


# ---------------------------------------------------------------------------------------
# HELPER FUNCTION TO CLEAN CONTEXT
# ---------------------------------------------------------------------------------------
def cleanup_reply_campaign_context(campaign_context: ContentGenerationContext) -> ContentGenerationContext:
    clone_context = campaign_context.copy(deep=True)
    if clone_context.lead_info is not None:
        clone_context.lead_info.task_ids = None
        clone_context.lead_info.email_validation_status = None
        clone_context.lead_info.linkedin_validation_status = None
        clone_context.lead_info.research_status = None
        clone_context.lead_info.enchrichment_status = None
    return clone_context


# ---------------------------------------------------------------------------------------
# GET INBOUND EMAIL TRIAGE ACTION (NO EMAIL TEXT)
# ---------------------------------------------------------------------------------------
async def get_inbound_email_triage_action(
    context: ContentGenerationContext,
    tool_config: Optional[List[Dict]] = None
) -> InboundEmailTriageResponse:
    """
    Analyzes the inbound email thread, and triage guidelines
    to determine triage status, reason, and the recommended action to take.
    DOES NOT generate the final email text.
    """
    allowed_actions = [
        "UNSUBSCRIBE",
        "NOT_INTERESTED",
        "SCHEDULE_MEETING",
        "SEND_REPLY",
        "OOF_MESSAGE",
        "FORWARD_TO_OTHER_USER",
        "NO_MORE_IN_ORGANIZATION",
        "OBJECTION_RAISED",
        "END_CONVERSATION",
    ]
    current_date_iso = datetime.datetime.now().isoformat()
    cleaned_context = cleanup_reply_campaign_context(context)
    if not cleaned_context.current_conversation_context.current_email_thread:
        cleaned_context.current_conversation_context.current_email_thread = []
    
    if not cleaned_context.campaign_context.email_triage_guidelines:
        cleaned_context.campaign_context.email_triage_guidelines = "No specific guidelines provided."

    triage_prompt = f"""
        You are a specialized email assistant.                          
        Your task is to analyze the inbound email thread and the triage
        guidelines below to determine the correct triage action.

        allowed_actions = 
        {allowed_actions}

        If you need more info, use SEND_REPLY and ask a short clarifying question.

        1. Email thread or conversation:
        {[thread_item.model_dump() for thread_item in cleaned_context.current_conversation_context.current_email_thread]}

        2. Triage Guidelines
        -----------------------------------------------------------------
        General flow
        ------------
        • If the request is routine, non-sensitive, and clearly actionable  
        → **triage_status = "AUTOMATIC"**.  
        • If the thread contains PII, legal, NSFW, or any sensitive content  
        → **triage_status = "END_CONVERSATION"** and set a short **triage_reason**.

        Meeting & next-step logic
        -------------------------
        • Define `meeting_offer_sent` = **true** if **any** prior assistant
        message in the current thread proposed a call or meeting.

        • **First positive but non-committal reply**  
        (e.g. “Thanks”, “Sounds good”, “Will review”) **AND**
        `meeting_offer_sent` is **false**  
        → **SEND_REPLY** asking for a 15-min call, ≤ 150 words, friendly tone.  

        • **Second non-committal reply** or “Will get back” **after**
        `meeting_offer_sent` already true  
        → **END_CONVERSATION** (stop the thread unless the prospect re-engages).

        • If the prospect explicitly **asks for times / suggests times /
        requests your scheduling link**  
        → **SCHEDULE_MEETING** and include a concise reply that
        (a) confirms time or provides link,  
        (b) thanks them, and  
        (c) ends with a forward-looking statement.

        Handling interest & objections
        ------------------------------
        • If the prospect asks for **pricing, docs, case studies, or more info**  
        → **SEND_REPLY** and ask a short clarifying question or promise a follow-up.

        • If they mention **budget, timing, or competitor concerns**  
        → **OBJECTION_RAISED** and reply with a brief acknowledgement
            + single clarifying question or value statement.

        • If they request to loop in a colleague (“Please include Sarah”)  
        → **FORWARD_TO_OTHER_USER** and draft a one-liner tee-up.

        Priority order for immediate triage
        -----------------------------------
        1. “Unsubscribe”, “Remove me”, CAN-SPAM language → **UNSUBSCRIBE**  
        2. Explicit lack of interest → **NOT_INTERESTED**  
        3. Auto OOO / vacation responder → **OOF_MESSAGE**  
        4. Explicit request to meet / suggested times → **SCHEDULE_MEETING**  
        5. Prospect asks questions or raises objection → as per rules above  
        6. Apply “Meeting & next-step logic”  
        7. Default → **END_CONVERSATION**

        Reply style (when SEND_REPLY or SCHEDULE_MEETING)
        -------------------------------------------------
        • Max 150 words, clear single CTA, no jargon.  
        • Start with a thank-you, mirror the prospect’s language briefly, then
        propose next step or answer question.  
        
        If you have not proposed a meeting even once in the thread, and the user response is polite acknowledgment then you MUST request for a meeting.
         
        • Meeting ask template (use *exact* placeholder, will be filled later):
        Hi {{first_name}}, would you be open to a quick 15-min call to
        understand your use-case and share notes?

        • Competitor-stack mention template:
        Hi {{first_name}}, thanks for sharing your current stack. Would you be
        open to a 15-min call to explore where we can add value?
        
       

        Custom triage guidelines provided by the user. This takes precedence over above guidelines:
        {cleaned_context.campaign_context.email_triage_guidelines}
        
        Guard-rails
        -----------
        • Only one unsolicited follow-up per thread. If no response, stop.  
        • Never disclose PII/financial data; instead **END_CONVERSATION**.  
        • Stay friendly, concise, and on topic.


        Required JSON output
        --------------------
        {{
        "triage_status": "...",
        "triage_reason": null or "<reason>",
        "response_action_to_take": "one of {allowed_actions}",
        "response_message": "<only if SEND_REPLY/SCHEDULE_MEETING/OBJECTION_RAISED, else empty>"
        }}

        Current date is: {current_date_iso}.
        -----------------------------------------------------------------
        """


    # If there's a vector store ID, use that approach
    if (
        cleaned_context.external_known_data
        and cleaned_context.external_known_data.external_openai_vector_store_id
    ):
        triage_only, status = await get_structured_output_with_assistant_and_vector_store(
            prompt=triage_prompt,
            response_format=InboundEmailTriageResponse,
            model=DEFAULT_TRIAGE_MODEL,
            vector_store_id=cleaned_context.external_known_data.external_openai_vector_store_id,
            tool_config=tool_config,
            use_cache=cleaned_context.message_instructions.use_cache if cleaned_context.message_instructions else True
        )
    else:
        triage_only, status = await get_structured_output_internal(
            prompt=triage_prompt,
            response_format=InboundEmailTriageResponse,
            model=DEFAULT_TRIAGE_MODEL,
            tool_config=tool_config,
            use_cache=cleaned_context.message_instructions.use_cache if cleaned_context.message_instructions else True
        )

    if status != "SUCCESS":
        campaign_id = context.campaign_context.campaign_id if context.campaign_context else 'N/A'
        if status == "CONTEXT_LENGTH_EXCEEDED":
            raise Exception(
                f"Email thread too long for model. Campaign ID: {campaign_id}. "
                f"Consider truncating thread or switching models."
            )
        elif status in ("API_ERROR", "ERROR"):
            raise Exception(
                f"Error in generating triage action. Status: {status}. "
                f"Campaign ID: {campaign_id}. Details: {triage_only}"
            )
        else:
            raise Exception(
                f"Error in generating triage action. Status: {status}. "
                f"Campaign ID: {campaign_id}"
            )
    return triage_only


# ---------------------------------------------------------------------------------------
# CORE FUNCTION TO GENERATE SINGLE RESPONSE (ONE VARIATION)
# ---------------------------------------------------------------------------------------
async def generate_inbound_email_response_copy(
    campaign_context: ContentGenerationContext,
    variation: str,
    tool_config: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Generate a single inbound email triage response based on the provided context and
    a specific variation prompt.
    """
    allowed_actions = [
        "SCHEDULE_MEETING",
        "SEND_REPLY",
        "UNSUBSCRIBE",
        "OOF_MESSAGE",
        "NOT_INTERESTED",
        "FORWARD_TO_OTHER_USER",
        "NO_MORE_IN_ORGANIZATION",
        "OBJECTION_RAISED",
        "END_CONVERSATION",
    ]
    current_date_iso = datetime.datetime.now().isoformat()
    cleaned_context = cleanup_reply_campaign_context(campaign_context)
    if not cleaned_context.current_conversation_context.current_email_thread:
        cleaned_context.current_conversation_context.current_email_thread = []
    
    lead_data = cleaned_context.lead_info or Lead()
    sender_data = cleaned_context.sender_info or SenderInfo()

    prompt = f"""
    You are a B2B account executive replying to warm inbound or engaged leads.

    Your goal is to sound natural, helpful, and human while following all triage,
    compliance, and action rules below.

    Write responses the way a strong AE would type them, not like a system message.

    =====================================================
    INPUT CONTEXT
    =====================================================

    1) Email thread to respond to:
    {[thread_item.model_dump() for thread_item in cleaned_context.current_conversation_context.current_email_thread]
        if cleaned_context.current_conversation_context.current_email_thread else []}

    2) Lead information:
    {lead_data.model_dump()}

    Sender information:
    - Full name: {sender_data.sender_full_name or ''}
    - First name: {sender_data.sender_first_name or ''}
    - Last name: {sender_data.sender_last_name or ''}
    - Bio: {sender_data.sender_bio or ''}
    - Appointment Booking URL: {sender_data.sender_appointment_booking_url or ''}

    3) Campaign-specific triage guidelines
    (User overrides always take priority):
    {cleaned_context.campaign_context.email_triage_guidelines}

    =====================================================
    TRIAGE DECISION LOGIC
    =====================================================

    Decide first. Write second.

    • Routine, non-sensitive, clearly actionable  
    → triage_status = "AUTOMATIC"

    • PII, finance, legal, contracts, compliance, NSFW,
    or document requests  
    → triage_status = "END_CONVERSATION"
    → Include a brief triage_reason

    =====================================================
    ACTION SELECTION
    =====================================================

    Choose exactly ONE action from:
    {allowed_actions}

    If you need more info, use SEND_REPLY and ask a short clarifying question.

    Priority order:
    1. UNSUBSCRIBE
    2. NOT_INTERESTED
    3. OOF_MESSAGE
    4. SCHEDULE_MEETING
    5. FORWARD_TO_OTHER_USER
    6. OBJECTION_RAISED
    7. SEND_REPLY
    8. END_CONVERSATION

    =====================================================
    HOW THE RESPONSE SHOULD SOUND
    =====================================================

    This is a warm lead. Assume positive intent.

    • Friendly, relaxed, and conversational
    • Short sentences. Natural pacing.
    • One clear idea per paragraph
    • No sales pressure. No hype. No buzzwords.
    • Helpful first. Next step second.

    Think:
    "Thanks for reaching out. Happy to help."
    Not:
    "Thank you for your inquiry regarding..."

    =====================================================
    RESPONSE STRUCTURE (LOOSE, NOT FORMAL)
    =====================================================

    Typical flow:
    1. Quick thank-you or acknowledgement
    2. Briefly mirror what they said or asked
    3. Answer or clarify in plain language
    4. Suggest a simple next step, if appropriate

    Do not force all steps if it feels unnatural.

    =====================================================
    HARD RULES
    =====================================================

    • Plain text only. No HTML.
    • Do not repeat previous messages verbatim.
    • Do not invent information, pricing, links, or docs.
    • If a link exists in the inbound email, reuse it exactly.
    • Do not add new links or attachments.
    • If documents are requested, END_CONVERSATION.
    • Never contradict or disparage {campaign_context.lead_info.organization_name}.
    • Do not spam or over-message.

    =====================================================
    NAMING AND STYLE
    =====================================================

    • Use conversational company name
    • Use conversational lead first name
    • Do not use special characters or spaces when referencing lead first name
    • Signature must include sender_first_name exactly as provided
    • Preserve clean spacing and newlines
    • Do NOT use em dash
    • Keep it human. Avoid templates.

    =====================================================
    OUTPUT FORMAT (STRICT JSON)
    =====================================================

    Return valid JSON only.

    {{
    "triage_status": "AUTOMATIC" or "END_CONVERSATION",
    "triage_reason": "<string if END_CONVERSATION, otherwise null>",
    "response_action_to_take": "one of {allowed_actions}",
    "response_message": "<reply body only if SEND_REPLY/SCHEDULE_MEETING/OBJECTION_RAISED, otherwise empty>"
    }}

    =====================================================
    SYSTEM CONTEXT
    =====================================================

    • Current date: {current_date_iso}
    • Use only provided context
    • If unsure, choose END_CONVERSATION
    """



    # If there's a vector store ID, use that approach
    if (
        cleaned_context.external_known_data
        and cleaned_context.external_known_data.external_openai_vector_store_id
    ):
        initial_response, status = await get_structured_output_with_assistant_and_vector_store(
            prompt=prompt,
            response_format=InboundEmailTriageResponse,
            model=DEFAULT_TRIAGE_MODEL,
            vector_store_id=cleaned_context.external_known_data.external_openai_vector_store_id,
            tool_config=tool_config
        )
    else:
        initial_response, status = await get_structured_output_internal(
            prompt=prompt,
            response_format=InboundEmailTriageResponse,
            model=DEFAULT_TRIAGE_MODEL,
            tool_config=tool_config
        )

    if status != "SUCCESS":
        campaign_id = (
            campaign_context.campaign_context.campaign_id 
            if campaign_context.campaign_context else 'N/A'
        )
        if status == "CONTEXT_LENGTH_EXCEEDED":
            raise Exception(
                f"Email thread too long for model. Campaign ID: {campaign_id}. "
                f"Consider truncating thread or switching models."
            )
        elif status in ("API_ERROR", "ERROR"):
            raise Exception(
                f"Error in generating inbound email triage response. Status: {status}. "
                f"Campaign ID: {campaign_id}. Details: {initial_response}"
            )
        else:
            raise Exception(
                f"Error in generating inbound email triage response. Status: {status}. "
                f"Campaign ID: {campaign_id}"
            )

    response_action = initial_response.response_action_to_take
    if response_action == "NEED_MORE_INFO":
        response_action = "SEND_REPLY"

    response_message = initial_response.response_message or ""

    response_item = MessageItem(
        message_id="",  # or generate one if appropriate
        thread_id="",
        sender_name=campaign_context.sender_info.sender_full_name or "",
        sender_email=campaign_context.sender_info.sender_email or "",
        receiver_name=campaign_context.lead_info.full_name or "",
        receiver_email=campaign_context.lead_info.email or "",
        iso_datetime=datetime.datetime.utcnow().isoformat(),
        subject="",  # or set some triage subject if needed
        body=response_message
    )

    # Build a MessageResponse that includes triage metadata plus your message item
    response_message = MessageResponse(
        triage_status=initial_response.triage_status,
        triage_reason=initial_response.triage_reason,
        message_item=response_item,
        response_action_to_take=response_action
    )
    return response_message.model_dump()


# ---------------------------------------------------------------------------------------
# MAIN ENTRY POINT - GENERATE MULTIPLE VARIATIONS
# ---------------------------------------------------------------------------------------
@assistant_tool
async def generate_inbound_email_response_variations(
    campaign_context: ContentGenerationContext,
    number_of_variations: int = 3,
    tool_config: Optional[List[Dict]] = None
) -> List[Dict[str, Any]]:
    """
    Generate multiple inbound email triage responses, each with a different 'variation'
    unless user instructions are provided. Returns a list of dictionaries conforming
    to InboundEmailTriageResponse.
    """
    # Default variation frameworks
    variation_specs = [
        "Short and friendly response focusing on quick resolution.",
        "More formal tone referencing user’s key points in the thread.",
        "Meeting-based approach if user needs further discussion or demo.",
        "Lean approach focusing on clarifying user’s questions or concerns.",
        "Solution-driven approach referencing a relevant product or case study."
    ]

    # Check if the user provided custom instructions
    message_instructions = campaign_context.message_instructions or MessageGenerationInstructions()
    user_instructions = (message_instructions.instructions_to_generate_message or "").strip()
    user_instructions_exist = bool(user_instructions)

    all_variations = []
    for i in range(number_of_variations):
        # If user instructions exist, use them for every variation
        if user_instructions_exist:
            variation_text = user_instructions
        else:
            # Otherwise, fallback to variation_specs
            variation_text = variation_specs[i % len(variation_specs)]

        try:
            triaged_response = await generate_inbound_email_response_copy(
                campaign_context=campaign_context,
                variation=variation_text,
                tool_config=tool_config
            )
            all_variations.append(triaged_response)
        except Exception as e:
            raise e

    return all_variations
