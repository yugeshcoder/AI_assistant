"""
Main chatbot logic for the Leave Management System
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import GOOGLE_API_KEY, GEMINI_MODEL, LEAVE_TYPES, SYSTEM_MESSAGE_TEMPLATE, DEFAULT_SESSION_ID
from tools import ALL_TOOLS, TOOL_FUNCTIONS
from session import (
    get_or_create_session, user_sessions, stringify, 
    update_session_from_tool_args, extract_and_parse_info, clean_response
)


class LeaveManagementChatbot:
    """Main chatbot class for leave management operations"""
    
    def __init__(self):
        """Initialize the chatbot with LLM and tools"""
        if GOOGLE_API_KEY == 'your-api-key-here':
            raise ValueError("Please set your Google API key in config.py or environment variable GOOGLE_API_KEY")
        
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY
        )
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
    
    def process_user_message(self, user_input: str, session_id: str = DEFAULT_SESSION_ID) -> str:
        """Process a user message and return the AI response with user context"""
        # Get or create user session
        session = get_or_create_session(session_id)
        
        # Add user context to system message
        user_context = session.get_context()
        #print(f"DEBUG - Current user context: {stringify(user_context)}")
        
        # Get recent conversation history for context
        recent_history = []
        if session.conversation_history:
            # Get last 4 messages to provide context
            for msg in session.conversation_history[-4:]:
                recent_history.append(f"{msg['type'].title()}: {msg['content']}")
        
        conversation_context = "\n".join(recent_history) if recent_history else "No previous conversation"
        
        # Create dynamic system message based on missing information
        missing_info = []
        if not session.employee_id:
            missing_info.append("Employee ID (e.g., EMP001)")
        if not session.name:
            missing_info.append("employee name")
        
        guidance = ""
        if missing_info:
            guidance = f"\n\nIMPORTANT: The user hasn't provided their {' and '.join(missing_info)}. When appropriate, politely ask for this information during the conversation. For example: 'Could you please provide your Employee ID?' or 'What's your name?'"
        
        # Check if user has provided complete information for leave application
        has_leave_request_info = bool(
            session.employee_id and 
            session.current_leave_type and 
            session.current_start_date and 
            session.current_end_date and
            session.reason
        )
        
        # Enhanced system message with combined extraction and processing
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        day_after_tomorrow = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        
        system_content = SYSTEM_MESSAGE_TEMPLATE.format(
            today=today,
            tomorrow=tomorrow,
            day_after_tomorrow=day_after_tomorrow,
            user_context=user_context,
            conversation_context=conversation_context,
            leave_types=LEAVE_TYPES,
            status='READY TO APPLY LEAVE - All info available' if has_leave_request_info else 'Missing info for leave application',
            guidance=guidance
        )
        
        system_msg = SystemMessage(content=system_content)
        user_msg = HumanMessage(content=user_input)
        
        # Add to conversation history
        session.conversation_history.append({"type": "user", "content": user_input})
        
        # Single API call for both extraction and processing
        ai_msg = self.llm_with_tools.invoke([system_msg, user_msg])
        
        # Extract information from AI response if present
        ai_content = ai_msg.content if hasattr(ai_msg, 'content') else ""
        extracted_info = extract_and_parse_info(ai_content)
        
        if extracted_info:
            #print(f"DEBUG - AI extracted info from combined call: {extracted_info}")
            session.update_info(**extracted_info)
            
            # Update user context after extraction
            user_context = session.get_context()
            #print(f"DEBUG - Updated user context: {stringify(user_context)}")
        
        # Process tool calls if any
        if ai_msg.tool_calls:
            final_response = self._process_tool_calls(ai_msg, system_msg, user_msg, session)
        else:
            final_response = ai_msg.content
        
        # Clean up the response
        final_response = clean_response(final_response)
        
        # Ensure we have a response
        if not final_response:
            final_response = "I apologize, but I encountered an issue processing your request. Please try again."
        
        # Add to conversation history
        session.conversation_history.append({"type": "assistant", "content": final_response})
        
        return final_response
    
    def _process_tool_calls(self, ai_msg, system_msg, user_msg, session) -> str:
        """Process tool calls and return the final response"""
        # Get the tool call details
        tool_call = ai_msg.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Update session with information from tool calls
        update_session_from_tool_args(session, tool_args)
        
        # Run the appropriate tool
        if tool_name in TOOL_FUNCTIONS:
            tool_result = TOOL_FUNCTIONS[tool_name](**tool_args)
        else:
            tool_result = f"Unknown tool: {tool_name}"
        
        #print(f"Tool executed: {tool_name}")
        #print(f"Tool result: {tool_result}")
        
        # Wrap as ToolMessage
        tool_msg = ToolMessage(
            content=tool_result,
            tool_call_id=tool_call["id"]
        )
        
        # Continue conversation: pass [system, user, ai, tool]
        try:
            response = self.llm_with_tools.invoke([system_msg, user_msg, ai_msg, tool_msg])
            final_response = response.content if response and hasattr(response, 'content') else tool_result
            #print(f"DEBUG - LLM final response: {final_response}")
            return final_response
        except Exception as e:
            #print(f"DEBUG - Error in LLM final response: {e}")
            # Fallback to tool result if LLM response fails
            return tool_result


# Initialize global chatbot instance
chatbot = LeaveManagementChatbot()


def process_user_message(user_input: str, session_id: str = DEFAULT_SESSION_ID) -> str:
    """Convenience function to process user message"""
    return chatbot.process_user_message(user_input, session_id)


def chatbot_api(user_message: str, session_id: str = DEFAULT_SESSION_ID, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    API function that can be called from frontend
    
    Args:
        user_message (str): The user's message
        session_id (str): Unique session identifier for the user
        user_info (dict): Optional user information containing:
            - employee_id: Employee ID
            - name: Employee name
            - current_leave_type: Current leave type being discussed
            - current_start_date: Current start date being discussed
            - current_end_date: Current end date being discussed
    
    Returns: dict with response, status, and user session info
    """
    try:
        # Update session with provided user info if available
        if user_info:
            session = get_or_create_session(session_id)
            session.update_info(**user_info)
        
        response = process_user_message(user_message, session_id)
        #print(f"DEBUG - Final response from process_user_message: {response}")
        
        # Get updated session info
        session = user_sessions.get(session_id)
        session_info = {
            "employee_id": session.employee_id,
            "name": session.name,
            "current_leave_type": session.current_leave_type,
            "current_start_date": session.current_start_date,
            "current_end_date": session.current_end_date,
            "reason": session.reason
        } if session else {}
        
        # Add missing information prompts
        missing_info = session.get_missing_info() if session else []
        
        return {
            "status": "success" if response else "error",
            "response": response,
            "session_info": session_info,
            "total_sessions": len(user_sessions),
            "session_id": session_id,
            "missing_info": missing_info,
            "info_complete": session.is_complete_for_leave_operations() if session else False,
            "error": "No response generated" if not response else None
        }
    except Exception as e:
        return {
            "status": "error",
            "response": None,
            "session_info": {},
            "error": str(e)
        }


def simple_chatbot_interface():
    """Enhanced command-line chatbot interface with user info collection"""
    print("=== Leave Management Chatbot ===")
    print("Commands: 'quit' to exit, 'info' to update info, 'sessions' to view all sessions")
    
    # Collect initial user info
    session_id = "test_session"
    print("\n=== User Information Setup ===")
    employee_id = input("Enter your Employee ID (e.g., EMP001): ").strip()
    name = input("Enter your name: ").strip()
    
    user_info = {}
    if employee_id:
        user_info['employee_id'] = employee_id
    if name:
        user_info['name'] = name
    
    # Initialize session with collected user info
    session = get_or_create_session(session_id)
    if user_info:
        session.update_info(**user_info)
        #print(f"DEBUG - Session initialized with: {user_info}")
    
    print(f"\nHello {name}! Your session is ready.")
    print("\nExample queries:")
    print("- 'Check my casual leave balance'")
    print("- 'I want to apply for 2 days sick leave from 2024-12-10 to 2024-12-11'")
    print("- 'Show me my leave history for 2024'")
    print("- 'Cancel my leave application LA005'")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        if user_input.lower() == 'sessions':
            from session import get_all_sessions
            print("\n=== Current Sessions ===")
            all_sessions = get_all_sessions()
            if all_sessions:
                for sid, sinfo in all_sessions.items():
                    print(f"Session {sid}:")
                    print(f"  Employee: {sinfo['employee_id']} - {sinfo['name']}")
                    print(f"  Leave Type: {sinfo['current_leave_type']}")
                    print(f"  Dates: {sinfo['current_start_date']} to {sinfo['current_end_date']}")
                    print(f"  Conversations: {sinfo['conversation_count']}")
                    print()
            else:
                print("No active sessions found.")
            continue
        
        if user_input.lower() == 'info':
            session = get_or_create_session(session_id)
            print("\n=== Update User Information ===")
            new_employee_id = input(f"Employee ID ({session.employee_id or 'Not set'}): ").strip()
            new_name = input(f"Name ({session.name or 'Not set'}): ").strip()
            new_leave_type = input(f"Current leave type ({session.current_leave_type or 'Not set'}): ").strip()
            new_start_date = input(f"Start date ({session.current_start_date or 'Not set'}): ").strip()
            new_end_date = input(f"End date ({session.current_end_date or 'Not set'}): ").strip()
            
            update_info = {}
            if new_employee_id:
                update_info['employee_id'] = new_employee_id
            if new_name:
                update_info['name'] = new_name
            if new_leave_type:
                update_info['current_leave_type'] = new_leave_type
            if new_start_date:
                update_info['current_start_date'] = new_start_date
            if new_end_date:
                update_info['current_end_date'] = new_end_date
            
            session.update_info(**update_info)
            print("Information updated!")
            continue
        
        if user_input:
            try:
                response = process_user_message(user_input, session_id)
                print(f"\nBot: {response}")
            except Exception as e:
                print(f"\nError: {str(e)}")