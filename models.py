"""
Data models and structures for the Leave Management System
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LeaveBalance:
    """Leave balance information for a specific leave type"""
    total_allocated: int
    used: int
    remaining: int


@dataclass
class LeaveApplication:
    """Leave application details"""
    application_id: str
    leave_type: str
    start_date: str
    end_date: str
    days: int
    status: str  # pending, approved, cancelled
    reason: str
    applied_date: str


@dataclass
class Employee:
    """Employee information with leave data"""
    employee_id: str
    name: str
    department: str
    join_date: str
    leave_balances: Dict[str, LeaveBalance]
    leave_history: List[LeaveApplication] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Employee':
        """Create Employee instance from dictionary data"""
        leave_balances = {}
        for leave_type, balance_data in data['leave_balances'].items():
            leave_balances[leave_type] = LeaveBalance(**balance_data)
        
        leave_history = []
        for app_data in data.get('leave_history', []):
            leave_history.append(LeaveApplication(**app_data))
        
        return cls(
            employee_id=data['employee_id'],
            name=data['name'],
            department=data['department'],
            join_date=data['join_date'],
            leave_balances=leave_balances,
            leave_history=leave_history
        )


@dataclass
class LeavePolicy:
    """Leave policy configuration for a specific leave type"""
    annual_allocation: int
    max_consecutive_days: int
    advance_notice_days: int
    carry_forward: bool
    max_carry_forward: Optional[int] = None
    medical_certificate_required: Optional[int] = None


class UserSession:
    """User session management for maintaining conversation context"""
    
    def __init__(self):
        self.employee_id: Optional[str] = None
        self.name: Optional[str] = None
        self.current_leave_type: Optional[str] = None
        self.current_start_date: Optional[str] = None
        self.current_end_date: Optional[str] = None
        self.reason: Optional[str] = None
        self.conversation_history: List[Dict[str, str]] = []
    
    def update_info(self, **kwargs):
        """Update user information"""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None and value != "":
                setattr(self, key, value)
                #print(f"DEBUG - Updated session {key}: {value}")
            elif value == "" or value is None:
                pass  # Skip empty values
                #print(f"DEBUG - Skipped empty value for {key}: {repr(value)}")
            else:
                pass  # Attribute not found in UserSession class
                #print(f"DEBUG - Attribute {key} not found in UserSession class")
    
    def get_context(self) -> str:
        """Get user context for AI"""
        context = []
        if self.employee_id:
            context.append(f"Employee ID: {self.employee_id}")
        if self.name:
            context.append(f"Name: {self.name}")
        if self.current_leave_type:
            context.append(f"Current leave type: {self.current_leave_type}")
        if self.current_start_date:
            context.append(f"Current start date: {self.current_start_date}")
        if self.current_end_date:
            context.append(f"Current end date: {self.current_end_date}")
        if self.reason:
            context.append(f"Leave reason: {self.reason}")
        return "; ".join(context) if context else "No user context available"
    
    def get_missing_info(self) -> List[str]:
        """Get list of missing essential information"""
        missing = []
        if not self.employee_id:
            missing.append("Employee ID")
        if not self.name:
            missing.append("Name")
        return missing
    
    def is_complete_for_leave_operations(self) -> bool:
        """Check if session has enough info for leave operations"""
        return bool(self.employee_id and self.name)


# Sample employee data - In a real application, this would come from a database
EMPLOYEE_DATA = {
    "employees": [
        {
            "employee_id": "EMP001",
            "name": "John Doe",
            "department": "Engineering",
            "join_date": "2022-01-15",
            "leave_balances": {
                "casual_leave": {"total_allocated": 12, "used": 3, "remaining": 9},
                "sick_leave": {"total_allocated": 10, "used": 2, "remaining": 8},
                "earned_leave": {"total_allocated": 18, "used": 5, "remaining": 13}
            },
            "leave_history": [
                {
                    "application_id": "LA001",
                    "leave_type": "casual_leave",
                    "start_date": "2024-02-10",
                    "end_date": "2024-02-12",
                    "days": 3,
                    "status": "approved",
                    "reason": "Personal work",
                    "applied_date": "2024-02-08"
                },
                {
                    "application_id": "LA002",
                    "leave_type": "sick_leave",
                    "start_date": "2024-03-05",
                    "end_date": "2024-03-06",
                    "days": 2,
                    "status": "approved",
                    "reason": "Fever",
                    "applied_date": "2024-03-05"
                }
            ]
        },
        {
            "employee_id": "EMP002",
            "name": "Jane Smith",
            "department": "Marketing",
            "join_date": "2021-06-10",
            "leave_balances": {
                "casual_leave": {"total_allocated": 12, "used": 7, "remaining": 5},
                "sick_leave": {"total_allocated": 10, "used": 1, "remaining": 9},
                "earned_leave": {"total_allocated": 20, "used": 12, "remaining": 8}
            },
            "leave_history": [
                {
                    "application_id": "LA003",
                    "leave_type": "earned_leave",
                    "start_date": "2024-01-20",
                    "end_date": "2024-01-25",
                    "days": 6,
                    "status": "approved",
                    "reason": "Vacation",
                    "applied_date": "2024-01-10"
                },
                {
                    "application_id": "LA004",
                    "leave_type": "casual_leave",
                    "start_date": "2024-04-15",
                    "end_date": "2024-04-15",
                    "days": 1,
                    "status": "approved",
                    "reason": "Personal appointment",
                    "applied_date": "2024-04-14"
                }
            ]
        },
        {
            "employee_id": "EMP003",
            "name": "Raj Kumar",
            "department": "Finance",
            "join_date": "2023-03-20",
            "leave_balances": {
                "casual_leave": {"total_allocated": 12, "used": 4, "remaining": 8},
                "sick_leave": {"total_allocated": 10, "used": 0, "remaining": 10},
                "earned_leave": {"total_allocated": 18, "used": 3, "remaining": 15}
            },
            "leave_history": [
                {
                    "application_id": "LA005",
                    "leave_type": "casual_leave",
                    "start_date": "2024-05-10",
                    "end_date": "2024-05-11",
                    "days": 2,
                    "status": "pending",
                    "reason": "Family function",
                    "applied_date": "2024-05-08"
                }
            ]
        },
        {
            "employee_id": "EMP004",
            "name": "Priya Sharma",
            "department": "HR",
            "join_date": "2020-08-15",
            "leave_balances": {
                "casual_leave": {"total_allocated": 12, "used": 10, "remaining": 2},
                "sick_leave": {"total_allocated": 10, "used": 5, "remaining": 5},
                "earned_leave": {"total_allocated": 20, "used": 15, "remaining": 5}
            },
            "leave_history": [
                {
                    "application_id": "LA006",
                    "leave_type": "earned_leave",
                    "start_date": "2024-02-01",
                    "end_date": "2024-02-10",
                    "days": 10,
                    "status": "approved",
                    "reason": "Annual vacation",
                    "applied_date": "2024-01-15"
                },
                {
                    "application_id": "LA007",
                    "leave_type": "sick_leave",
                    "start_date": "2024-03-20",
                    "end_date": "2024-03-22",
                    "days": 3,
                    "status": "approved",
                    "reason": "Medical treatment",
                    "applied_date": "2024-03-20"
                }
            ]
        },
        {
            "employee_id": "EMP005",
            "name": "Michael Chen",
            "department": "Engineering",
            "join_date": "2023-11-01",
            "leave_balances": {
                "casual_leave": {"total_allocated": 12, "used": 2, "remaining": 10},
                "sick_leave": {"total_allocated": 10, "used": 1, "remaining": 9},
                "earned_leave": {"total_allocated": 18, "used": 0, "remaining": 18}
            },
            "leave_history": [
                {
                    "application_id": "LA008",
                    "leave_type": "casual_leave",
                    "start_date": "2024-04-22",
                    "end_date": "2024-04-23",
                    "days": 2,
                    "status": "approved",
                    "reason": "House relocation",
                    "applied_date": "2024-04-20"
                }
            ]
        },
        {
            "employee_id": "EMP006",
            "name": "Sarah Williams",
            "department": "Sales",
            "join_date": "2019-04-10",
            "leave_balances": {
                "casual_leave": {"total_allocated": 12, "used": 6, "remaining": 6},
                "sick_leave": {"total_allocated": 10, "used": 8, "remaining": 2},
                "earned_leave": {"total_allocated": 20, "used": 8, "remaining": 12}
            },
            "leave_history": [
                {
                    "application_id": "LA009",
                    "leave_type": "sick_leave",
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-19",
                    "days": 5,
                    "status": "approved",
                    "reason": "Flu",
                    "applied_date": "2024-01-15"
                },
                {
                    "application_id": "LA010",
                    "leave_type": "casual_leave",
                    "start_date": "2024-03-25",
                    "end_date": "2024-03-27",
                    "days": 3,
                    "status": "approved",
                    "reason": "Personal work",
                    "applied_date": "2024-03-23"
                }
            ]
        },
        {
            "employee_id": "EMP007",
            "name": "Ahmed Hassan",
            "department": "Operations",
            "join_date": "2022-07-01",
            "leave_balances": {
                "casual_leave": {"total_allocated": 12, "used": 5, "remaining": 7},
                "sick_leave": {"total_allocated": 10, "used": 3, "remaining": 7},
                "earned_leave": {"total_allocated": 18, "used": 10, "remaining": 8}
            },
            "leave_history": [
                {
                    "application_id": "LA011",
                    "leave_type": "earned_leave",
                    "start_date": "2024-06-01",
                    "end_date": "2024-06-07",
                    "days": 7,
                    "status": "pending",
                    "reason": "Travel plans",
                    "applied_date": "2024-05-20"
                },
                {
                    "application_id": "LA012",
                    "leave_type": "sick_leave",
                    "start_date": "2024-02-14",
                    "end_date": "2024-02-16",
                    "days": 3,
                    "status": "approved",
                    "reason": "Back pain",
                    "applied_date": "2024-02-14"
                }
            ]
        },
        {
            "employee_id": "EMP008",
            "name": "Lisa Anderson",
            "department": "Marketing",
            "join_date": "2021-09-15",
            "leave_balances": {
                "casual_leave": {"total_allocated": 12, "used": 8, "remaining": 4},
                "sick_leave": {"total_allocated": 10, "used": 4, "remaining": 6},
                "earned_leave": {"total_allocated": 20, "used": 6, "remaining": 14}
            },
            "leave_history": [
                {
                    "application_id": "LA013",
                    "leave_type": "casual_leave",
                    "start_date": "2024-01-08",
                    "end_date": "2024-01-10",
                    "days": 3,
                    "status": "approved",
                    "reason": "Wedding to attend",
                    "applied_date": "2024-01-05"
                },
                {
                    "application_id": "LA014",
                    "leave_type": "earned_leave",
                    "start_date": "2024-04-01",
                    "end_date": "2024-04-03",
                    "days": 3,
                    "status": "approved",
                    "reason": "Short trip",
                    "applied_date": "2024-03-25"
                },
                {
                    "application_id": "LA015",
                    "leave_type": "sick_leave",
                    "start_date": "2024-05-12",
                    "end_date": "2024-05-13",
                    "days": 2,
                    "status": "cancelled",
                    "reason": "Headache",
                    "applied_date": "2024-05-12"
                }
            ]
        }
    ],
    "leave_policies": {
        "casual_leave": {
            "annual_allocation": 12,
            "max_consecutive_days": 3,
            "advance_notice_days": 1,
            "carry_forward": False
        },
        "sick_leave": {
            "annual_allocation": 10,
            "max_consecutive_days": 7,
            "advance_notice_days": 0,
            "carry_forward": False,
            "medical_certificate_required": 3
        },
        "earned_leave": {
            "annual_allocation": 18,
            "max_consecutive_days": 15,
            "advance_notice_days": 7,
            "carry_forward": True,
            "max_carry_forward": 6
        }
    }
}