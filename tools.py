"""
Tool functions for the Leave Management System
"""
import os
from datetime import datetime
import uuid
from typing import Optional
from langchain_core.tools import tool
from models import EMPLOYEE_DATA


@tool
def calculate_leave_balance(employee_id: str, leave_type: str) -> str:
    """Calculate the leave balance for an employee."""
    leave_data = None
    employee_found = False
    
    for employee in EMPLOYEE_DATA["employees"]:
        if employee["employee_id"] == employee_id:
            employee_found = True
            # Convert leave_type to match the keys in data (replace spaces with underscores and lowercase)
            leave_type_key = leave_type.replace(" ", "_").lower()
            leave_data = employee["leave_balances"].get(leave_type_key)
            break
    
    if not employee_found:
        return f"Employee {employee_id} not found."
    if not leave_data:
        return f"Leave type '{leave_type}' not found for Employee {employee_id}. Available types: casual_leave, sick_leave, earned_leave."
    
    return f"Employee {employee_id} has {leave_data['remaining']} days of {leave_type} leave remaining (used: {leave_data['used']}, total: {leave_data['total_allocated']})."


@tool
def apply_leave(employee_id: str, leave_type: str, start_date: str, end_date: str, reason: str) -> str:
    """Apply for leave for an employee."""
    # Find employee
    employee_found = False
    for employee in EMPLOYEE_DATA["employees"]:
        if employee["employee_id"] == employee_id:
            employee_found = True
            
            # Convert leave_type to match the keys in data
            leave_type_key = leave_type.replace(" ", "_").lower()
            
            # Check if leave type exists
            if leave_type_key not in employee["leave_balances"]:
                return f"Invalid leave type '{leave_type}'. Available types: casual_leave, sick_leave, earned_leave."
            
            # Calculate days (simple implementation)
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                days = (end - start).days + 1
            except ValueError:
                return "Invalid date format. Please use YYYY-MM-DD format."
            
            # Check if enough leave balance
            remaining = employee["leave_balances"][leave_type_key]["remaining"]
            if days > remaining:
                return f"Insufficient {leave_type} balance. Requested: {days} days, Available: {remaining} days."

            # Check leave policy for max consecutive days
            max_consecutive = EMPLOYEE_DATA["leave_policies"][leave_type_key]["max_consecutive_days"]
            if days > max_consecutive:
                return f"Leave request exceeds maximum consecutive days allowed ({max_consecutive} days) for {leave_type}."

            # Check advance notice requirement
            advance_notice = EMPLOYEE_DATA["leave_policies"][leave_type_key]["advance_notice_days"]
            if (start - datetime.now()).days < advance_notice:
                return f"Leave request must be submitted at least {advance_notice} days in advance."

            # Generate application ID
            app_id = f"LA{len([h for emp in EMPLOYEE_DATA['employees'] for h in emp['leave_history']]) + 1:03d}"
            
            # Create leave application
            leave_application = {
                "application_id": app_id,
                "leave_type": leave_type_key,
                "start_date": start_date,
                "end_date": end_date,
                "days": days,
                "status": "pending",
                "reason": reason,
                "applied_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Add to leave history
            employee["leave_history"].append(leave_application)
            
            # Update leave balance (assume auto-approval for demo)
            employee["leave_balances"][leave_type_key]["used"] += days
            employee["leave_balances"][leave_type_key]["remaining"] -= days
            
            return f"Leave application {app_id} submitted successfully for Employee {employee_id}. {days} days of {leave_type} requested from {start_date} to {end_date}. Status: Pending approval."
    
    if not employee_found:
        return f"Employee {employee_id} not found."


@tool
def cancel_leave(employee_id: str, application_id: str) -> str:
    """Cancel a leave application for an employee."""
    # Find employee
    employee_found = False
    application_found = False
    
    for employee in EMPLOYEE_DATA["employees"]:
        if employee["employee_id"] == employee_id:
            employee_found = True
            
            # Find the leave application
            for leave_app in employee["leave_history"]:
                if leave_app["application_id"] == application_id:
                    application_found = True
                    
                    # Check if application can be cancelled
                    if leave_app["status"] == "cancelled":
                        return f"Leave application {application_id} is already cancelled."
                    
                    if leave_app["status"] == "approved":
                        # If approved, restore leave balance
                        leave_type_key = leave_app["leave_type"]
                        days = leave_app["days"]
                        
                        employee["leave_balances"][leave_type_key]["used"] -= days
                        employee["leave_balances"][leave_type_key]["remaining"] += days
                    
                    # Update status
                    leave_app["status"] = "cancelled"
                    
                    return f"Leave application {application_id} for Employee {employee_id} has been successfully cancelled. {leave_app['days']} days of {leave_app['leave_type']} restored to balance."
            
            if not application_found:
                return f"Leave application {application_id} not found for Employee {employee_id}."
    
    if not employee_found:
        return f"Employee {employee_id} not found."


@tool
def get_leave_history(employee_id: str, year: int) -> str:
    """Get the leave history for an employee."""
    # Find employee
    employee_found = False
    
    for employee in EMPLOYEE_DATA["employees"]:
        if employee["employee_id"] == employee_id:
            employee_found = True
            
            # Filter leave history by year
            year_history = []
            for leave_app in employee["leave_history"]:
                if leave_app["start_date"].startswith(str(year)):
                    year_history.append(leave_app)
            
            if not year_history:
                return f"No leave history found for Employee {employee_id} in {year}."
            
            # Format the history
            history_text = f"Leave history for Employee {employee_id} ({employee['name']}) in {year}:\n\n"
            
            # Calculate totals by leave type
            totals = {"casual_leave": 0, "sick_leave": 0, "earned_leave": 0}
            
            for i, leave_app in enumerate(year_history, 1):
                history_text += f"{i}. Application {leave_app['application_id']}:\n"
                history_text += f"   Type: {leave_app['leave_type'].replace('_', ' ').title()}\n"
                history_text += f"   Period: {leave_app['start_date']} to {leave_app['end_date']} ({leave_app['days']} days)\n"
                history_text += f"   Reason: {leave_app['reason']}\n"
                history_text += f"   Status: {leave_app['status'].title()}\n"
                history_text += f"   Applied: {leave_app['applied_date']}\n\n"
                
                # Add to totals if approved
                if leave_app['status'] == 'approved':
                    totals[leave_app['leave_type']] += leave_app['days']
            
            # Add summary
            history_text += "Summary:\n"
            for leave_type, days in totals.items():
                if days > 0:
                    history_text += f"- {leave_type.replace('_', ' ').title()}: {days} days\n"
            
            total_days = sum(totals.values())
            history_text += f"- Total approved leave: {total_days} days"
            
            return history_text
    
    if not employee_found:
        return f"Employee {employee_id} not found."


@tool
def query_leave_policy(question: str) -> str:
    """Query the TechCorp leave policy for specific information about leave rules, procedures, and policies."""
    try:
        # Fallback to simple text search when RAG system fails
        return simple_policy_search(question)
        
    except Exception as e:
        return f"Policy information system is not available: {str(e)}. Please contact HR for policy details."


def simple_policy_search(question: str) -> str:
    """Simple text-based search through the policy document as fallback."""
    try:
        # Read policy file
        policy_file = "techcorp_leave_policy.txt"
        if not os.path.exists(policy_file):
            return "Policy document not found. Please contact HR for policy information."
        
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy_text = f.read()
        
        # Extract keywords from question
        question_lower = question.lower()
        keywords = []
        
        # Define keyword mappings for different topics
        keyword_mappings = {
            'casual': ['casual leave', '2.1 casual leave', 'personal reasons'],
            'sick': ['sick leave', '2.2 sick leave', 'medical certificate'],
            'earned': ['earned leave', '2.3 earned leave', 'annual leave'],
            'balance': ['leave balance', '4. leave balance', 'remaining leave'],
            'application': ['application', '3. leave application procedures', 'apply'],
            'approval': ['approval', 'approval authority', 'supervisor'],
            'cancellation': ['cancel', 'cancellation', '5. leave cancellation'],
            'policy': ['policy', 'techcorp', 'leave management']
        }
        
        # Find relevant sections based on keywords
        relevant_sections = []
        
        for key, search_terms in keyword_mappings.items():
            if any(term in question_lower for term in [key, *[t.split()[-1] for t in search_terms]]):
                for term in search_terms:
                    # Find paragraphs containing these terms
                    paragraphs = policy_text.split('\n\n')
                    for para in paragraphs:
                        if term.lower() in para.lower() and len(para.strip()) > 50:
                            relevant_sections.append(para.strip())
                            break
        
        # If no specific matches, provide general policy info
        if not relevant_sections:
            # Extract first few sections as general info
            sections = policy_text.split('\n\n')[:5]
            relevant_sections = [s.strip() for s in sections if len(s.strip()) > 50]
        
        # Format response
        if relevant_sections:
            context = '\n\n---\n\n'.join(relevant_sections[:3])  # Limit to 3 sections
            if len(context) > 2000:  # Truncate if too long
                context = context[:1997] + "..."
            
            return f"Based on the TechCorp Leave Policy:\n\n{context}\n\nFor more detailed information, please refer to the complete policy document or contact HR."
        else:
            return "I couldn't find specific information about your question in the policy. Please contact HR for detailed clarification."
            
    except Exception as e:
        return f"Error accessing policy information: {str(e)}. Please contact HR for policy details."


# Tool function mapping for easy access
TOOL_FUNCTIONS = {
    "calculate_leave_balance": calculate_leave_balance.func,
    "apply_leave": apply_leave.func,
    "cancel_leave": cancel_leave.func,
    "get_leave_history": get_leave_history.func,
    "query_leave_policy": query_leave_policy.func
}

# List of all tools for binding to LLM
ALL_TOOLS = [
    calculate_leave_balance,
    apply_leave,
    cancel_leave,
    get_leave_history,
    query_leave_policy
]