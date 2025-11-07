"""
Session management for the Leave Management System
"""
from typing import Dict, Any, Optional
from models import UserSession
import json


# User session storage
user_sessions: Dict[str, UserSession] = {}


def get_or_create_session(session_id: str) -> UserSession:
    """Get existing session or create new one"""
    if session_id not in user_sessions:
        user_sessions[session_id] = UserSession()
    return user_sessions[session_id]


def get_all_sessions() -> Dict[str, Dict[str, Any]]:
    """Get all active user sessions"""
    return {
        session_id: {
            "employee_id": session.employee_id,
            "name": session.name,
            "current_leave_type": session.current_leave_type,
            "current_start_date": session.current_start_date,
            "current_end_date": session.current_end_date,
            "conversation_count": len(session.conversation_history)
        } for session_id, session in user_sessions.items()
    }


def clear_session(session_id: str) -> str:
    """Clear a specific user session"""
    if session_id in user_sessions:
        del user_sessions[session_id]
        return f"Session {session_id} cleared successfully"
    return f"Session {session_id} not found"


def clear_all_sessions() -> str:
    """Clear all user sessions"""
    count = len(user_sessions)
    user_sessions.clear()
    return f"Cleared {count} sessions"


def debug_session(session_id: str) -> None:
    """Debug function to show complete session state"""
    if session_id in user_sessions:
        session = user_sessions[session_id]
        print(f"\n=== DEBUG SESSION {session_id} ===")
        print(f"employee_id: {repr(session.employee_id)}")
        print(f"name: {repr(session.name)}")
        print(f"current_leave_type: {repr(session.current_leave_type)}")
        print(f"current_start_date: {repr(session.current_start_date)}")
        print(f"current_end_date: {repr(session.current_end_date)}")
        print(f"conversation_count: {len(session.conversation_history)}")
        print("=" * 30)
    else:
        print(f"Session {session_id} not found")


def stringify(obj: Any, indent: int = 2) -> str:
    """Python equivalent of JSON.stringify with pretty printing"""
    try:
        # Convert object to dict if it has a dict method
        if hasattr(obj, 'dict'):
            obj_dict = obj.dict()
        elif hasattr(obj, '__dict__'):
            obj_dict = obj.__dict__
        else:
            obj_dict = obj
        return json.dumps(obj_dict, indent=indent, default=str)
    except Exception as e:
        return str(obj)


def update_session_from_tool_args(session: UserSession, tool_args: Dict[str, Any]) -> None:
    """Update session with information from tool calls"""
    if "employee_id" in tool_args and not session.employee_id:
        session.employee_id = tool_args["employee_id"]
        #print(f"DEBUG - Auto-updated employee_id: {session.employee_id}")
    
    if "leave_type" in tool_args and not session.current_leave_type:
        session.current_leave_type = tool_args["leave_type"]
        #print(f"DEBUG - Auto-updated leave_type: {session.current_leave_type}")

    if "start_date" in tool_args and not session.current_start_date:
        session.current_start_date = tool_args["start_date"]
        #print(f"DEBUG - Auto-updated start_date: {session.current_start_date}")

    if "end_date" in tool_args and not session.current_end_date:
        session.current_end_date = tool_args["end_date"]
        #print(f"DEBUG - Auto-updated end_date: {session.current_end_date}")


def extract_and_parse_info(ai_content: str) -> Optional[Dict[str, Any]]:
    """Extract and parse information from AI response"""
    if "EXTRACTED_INFO:" not in ai_content:
        return None
    
    try:
        # Find and parse the extracted info JSON
        start_marker = "EXTRACTED_INFO:"
        start_pos = ai_content.find(start_marker) + len(start_marker)
        
        # Find the JSON part (look for opening brace)
        json_start = ai_content.find("{", start_pos)
        if json_start != -1:
            # Find matching closing brace
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(ai_content[json_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = json_start + i + 1
                        break
            
            # Extract and parse JSON
            json_str = ai_content[json_start:json_end]
            extracted_info = json.loads(json_str)
            return extracted_info
            
    except (json.JSONDecodeError, ValueError) as e:
        print(f"DEBUG - Failed to parse extracted info: {e}")
        return None


def clean_response(response: str) -> str:
    """Clean up the response by removing EXTRACTED_INFO marker if present"""
    if not response or "EXTRACTED_INFO:" not in response:
        return response
    
    # Remove the EXTRACTED_INFO section from the response
    marker_pos = response.find("EXTRACTED_INFO:")
    if marker_pos != -1:
        # Find the end of the JSON (look for the closing brace and newline)
        json_start = response.find("{", marker_pos)
        if json_start != -1:
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(response[json_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = json_start + i + 1
                        break
            
            # Remove the entire EXTRACTED_INFO section
            before_extract = response[:marker_pos].strip()
            after_extract = response[json_end:].strip()
            response = (before_extract + "\n\n" + after_extract).strip()
    
    return response