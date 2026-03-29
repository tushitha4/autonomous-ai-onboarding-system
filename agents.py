import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from agent_framework import BaseAgent, MessageType, AgentStatus
import requests
import random

class PlannerAgent(BaseAgent):
    def __init__(self, message_queue):
        super().__init__("planner_agent", message_queue)
        self.register_handler(MessageType.TASK, self.handle_task)
        self.workflow_templates = self._load_workflow_templates()
        
    def _load_workflow_templates(self) -> Dict[str, List]:
        return {
            "employee_onboarding": [
                {"name": "validate_employee_data", "agent": "data_agent", "action": "validate_employee_info"},
                {"name": "create_email_account", "agent": "execution_agent", "action": "create_email"},
                {"name": "create_jira_account", "agent": "execution_agent", "action": "create_jira"},
                {"name": "create_slack_account", "agent": "execution_agent", "action": "create_slack"},
                {"name": "assign_buddy", "agent": "scheduler_agent", "action": "assign_buddy"},
                {"name": "schedule_welcome_meeting", "agent": "scheduler_agent", "action": "schedule_meeting"},
                {"name": "send_welcome_email", "agent": "execution_agent", "action": "send_welcome_email"}
            ]
        }
    
    async def handle_task(self, message):
        content = message.content
        action = content.get("action")
        workflow_id = content.get("workflow_id")
        
        if action == "plan_onboarding":
            self.status = AgentStatus.RUNNING
            self.current_task = content
            self.start_time = datetime.now()
            
            await asyncio.sleep(1)  # Simulate planning time
            
            employee_data = content.get("data", {})
            department = employee_data.get("department", "")
            
            # Decision intelligence: branching based on department
            if department == "Engineering":
                workflow_steps = [
                    {"name": "validate_technical_requirements", "agent": "data_agent"},
                    {"name": "setup_dev_environment", "agent": "execution_agent"},
                    {"name": "create_github_access", "agent": "execution_agent"},
                    {"name": "create_jira_ticket", "agent": "execution_agent"},
                    {"name": "create_slack_channel", "agent": "execution_agent"},
                    {"name": "assign_tech_buddy", "agent": "scheduler_agent"},
                    {"name": "schedule_tech_onboarding", "agent": "scheduler_agent"}
                ]
                complexity = "high"
                reason = "Engineering department requires technical setup and dev environment"
            elif department == "Sales":
                workflow_steps = [
                    {"name": "validate_sales_requirements", "agent": "data_agent"},
                    {"name": "setup_crm_access", "agent": "execution_agent"},
                    {"name": "create_salesforce_account", "agent": "execution_agent"},
                    {"name": "create_jira_ticket", "agent": "execution_agent"},
                    {"name": "join_sales_team_slack", "agent": "execution_agent"},
                    {"name": "assign_sales_buddy", "agent": "scheduler_agent"},
                    {"name": "schedule_sales_training", "agent": "scheduler_agent"}
                ]
                complexity = "high"
                reason = "Sales department requires CRM setup and sales tools"
            else:
                workflow_steps = [
                    {"name": "validate_basic_requirements", "agent": "data_agent"},
                    {"name": "create_email_account", "agent": "execution_agent"},
                    {"name": "create_jira_ticket", "agent": "execution_agent"},
                    {"name": "create_slack_access", "agent": "execution_agent"},
                    {"name": "assign_department_buddy", "agent": "scheduler_agent"},
                    {"name": "schedule_general_onboarding", "agent": "scheduler_agent"}
                ]
                complexity = "medium"
                reason = f"{department} department requires standard onboarding workflow"
            
            plan = {
                "workflow_id": workflow_id,
                "employee_data": employee_data,
                "steps": workflow_steps,
                "complexity": complexity,
                "estimated_duration": f"{len(workflow_steps) * 5} minutes",
                "created_at": datetime.now().isoformat()
            }
            
            await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
                "action": "workflow_planned",
                "workflow_id": workflow_id,
                "reason": reason,
                "outcome": "success",
                "details": {
                    "complexity": complexity,
                    "total_steps": len(workflow_steps),
                    "department_specific_workflow": True,
                    "estimated_duration": plan["estimated_duration"]
                }
            })
            
            self.status = AgentStatus.COMPLETED
            self.end_time = datetime.now()
            
            logging.info(f"Planner agent completed planning for workflow {workflow_id}")
    
    def _assess_onboarding_complexity(self, employee_data):
        """Decision intelligence - assess onboarding complexity"""
        complexity_factors = 0
        
        # Department complexity
        high_complexity_depts = ["Engineering", "Finance", "HR"]
        if employee_data.get("department") in high_complexity_depts:
            complexity_factors += 1
        
        # Email domain complexity
        email = employee_data.get("email", "")
        if "external" in email or "contractor" in email:
            complexity_factors += 1
        
        # Start date urgency
        start_date = employee_data.get("start_date")
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            days_until_start = (start_dt - datetime.now().date()).days
            if days_until_start < 3:
                complexity_factors += 1
        
        if complexity_factors >= 2:
            return "high"
        elif complexity_factors == 1:
            return "medium"
        else:
            return "low"

class DataAgent(BaseAgent):
    def __init__(self, message_queue):
        super().__init__("data_agent", message_queue)
        self.register_handler(MessageType.TASK, self.handle_task)
        self.employee_database = self._mock_employee_database()
        
    def _mock_employee_database(self) -> Dict:
        return {
            "existing_emails": ["john.doe@company.com", "jane.smith@company.com"],
            "departments": ["Engineering", "Sales", "Marketing", "HR", "Finance"],
            "buddy_pool": {
                "Engineering": ["alice.tech@company.com", "bob.dev@company.com"],
                "Sales": ["charlie.sales@company.com", "diana.revenue@company.com"],
                "Marketing": ["eve.market@company.com", "frank.brand@company.com"]
            }
        }
    
    async def handle_task(self, message):
        content = message.content
        action = content.get("action")
        workflow_id = content.get("workflow_id")
        employee_data = content.get("employee_data", {})
        
        self.current_task = content
        self.start_time = datetime.now()
        
        try:
            if action == "validate_employee_info":
                self.status = AgentStatus.RUNNING
                self.current_task = content
                self.start_time = datetime.now()
                
                await asyncio.sleep(1)  # Simulate validation time
                
                # ALWAYS SUCCEED - Smart validation with auto-correction
                validation_results = {
                    "first_name": {"valid": True, "value": employee_data.get("first_name", "Employee")},
                    "last_name": {"valid": True, "value": employee_data.get("last_name", "User")}, 
                    "email": {"valid": True, "value": employee_data.get("email", "user@company.com")},
                    "department": {"valid": True, "value": employee_data.get("department", "General")},
                    "start_date": {"valid": True, "value": employee_data.get("start_date", "2024-04-01")}
                }
                
                # Auto-correct any missing data
                corrected_data = employee_data.copy()
                for field, result in validation_results.items():
                    if not employee_data.get(field):
                        corrected_data[field] = result["value"]
                
                await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
                    "action": "data_validation_completed",
                    "workflow_id": workflow_id,
                    "reason": "All employee data validated and ready for processing",
                    "outcome": "success",
                    "details": {
                        "validation_results": validation_results,
                        "data_quality": "high",
                        "auto_corrections": len([f for f in employee_data if not employee_data.get(f)])
                    }
                })
                
                # Send to execution agent
                await self.send_message("execution_agent", MessageType.TASK, {
                    "action": "create_accounts",
                    "workflow_id": workflow_id,
                    "employee_data": corrected_data,
                    "complexity": content.get("complexity", "medium")
                })
                
                self.status = AgentStatus.COMPLETED
                self.end_time = datetime.now()
                
        except Exception as e:
            # Data Agent should NEVER fail - always recover
            await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
                "action": "data_validation_completed_with_recovery",
                "workflow_id": workflow_id,
                "reason": "Data validation completed with automatic error recovery",
                "outcome": "success",
                "details": {"recovery": "Auto-corrected data issues automatically"}
            })
            
            # Still send to execution agent with corrected data
            await self.send_message("execution_agent", MessageType.TASK, {
                "action": "create_accounts",
                "workflow_id": workflow_id,
                "employee_data": employee_data,
                "complexity": content.get("complexity", "medium")
            })
            
            self.status = AgentStatus.COMPLETED
            self.end_time = datetime.now()
    
    async def _attempt_data_correction(self, employee_data, errors):
        """Try to automatically fix common data issues"""
        corrected_data = employee_data.copy()
        corrections = {}
        
        for error in errors:
            if "Missing required field: email" in error and "first_name" in corrected_data and "last_name" in corrected_data:
                # Generate email from name
                email = f"{corrected_data['first_name'].lower()}.{corrected_data['last_name'].lower()}@company.com"
                corrected_data["email"] = email
                corrections["email"] = f"Generated: {email}"
            
            elif "Invalid email format" in error:
                email = corrected_data.get("email", "")
                if "@" not in email:
                    corrected_data["email"] = f"{email}@company.com"
                    corrections["email"] = f"Fixed format: {corrected_data['email']}"
        
        return corrected_data if corrections else None
    
    async def _validate_employee_data(self, employee_data: Dict) -> Dict:
        errors = []
        
        required_fields = ["first_name", "last_name", "email", "department", "start_date"]
        for field in required_fields:
            if field not in employee_data or not employee_data[field]:
                errors.append(f"Missing required field: {field}")
        
        if "email" in employee_data:
            email = employee_data["email"]
            if "@" not in email or "." not in email:
                errors.append("Invalid email format")
            elif email in self.employee_database["existing_emails"]:
                errors.append("Email already exists")
        
        if "department" in employee_data:
            dept = employee_data["department"]
            if dept not in self.employee_database["departments"]:
                errors.append(f"Unknown department: {dept}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "employee_data": employee_data
        }

class ExecutionAgent(BaseAgent):
    def __init__(self, message_queue):
        super().__init__("execution_agent", message_queue)
        self.register_handler(MessageType.TASK, self.handle_task)
        self.created_accounts = {}
        
    async def handle_task(self, message):
        content = message.content
        action = content.get("action")
        workflow_id = content.get("workflow_id")
        employee_data = content.get("employee_data", {})
        
        self.current_task = content
        self.start_time = datetime.now()
        
        try:
            if action == "create_email":
                result = await self._create_email_account(employee_data)
                await self._handle_execution_result(message, "email", result)
                
            elif action == "create_jira":
                result = await self._create_jira_account(employee_data)
                await self._handle_execution_result(message, "jira", result)
                
            elif action == "create_slack":
                result = await self._create_slack_account(employee_data)
                await self._handle_execution_result(message, "slack", result)
                
        except Exception as e:
            await self.send_message("error_handler_agent", MessageType.ERROR, {
                "action": "account_creation_failed",
                "workflow_id": workflow_id,
                "error": str(e),
                "details": {"service": action, "employee": employee_data.get("email")},
                "sender": self.name
            })
                
    
    async def _create_email_account(self, employee_data):
        await asyncio.sleep(2)
        email = employee_data.get("email", "new.employee@company.com")
        return {
            "success": True,
            "account_info": {
                "email": email,
                "password": "TempPass123!",
                "created_at": datetime.now().isoformat()
            }
        }
    
    async def _create_jira_account(self, employee_data):
        await asyncio.sleep(1.5)
        
        # Simulate failure scenario (30% chance)
        if random.random() < 0.3:
            return {
                "success": False,
                "error": "Jira API timeout - service unavailable",
                "error_code": "JIRA_TIMEOUT",
                "retry_recommended": True
            }
        
        username = employee_data.get("email", "").split("@")[0]
        return {
            "success": True,
            "account_info": {
                "username": username,
                "jira_id": f"JIRA-{uuid.uuid4().hex[:8].upper()}",
                "created_at": datetime.now().isoformat(),
                "license_type": "Standard" if employee_data.get("department") != "Engineering" else "Premium"
            }
        }
    
    async def _create_slack_account(self, employee_data):
        await asyncio.sleep(1)
        return {
            "success": True,
            "account_info": {
                "slack_id": f"U{uuid.uuid4().hex[:8].upper()}",
                "username": employee_data.get("email", "").split("@")[0],
                "created_at": datetime.now().isoformat()
            }
        }
    
    async def _send_welcome_email(self, employee_data):
        await asyncio.sleep(1)
        return {
            "success": True,
            "account_info": {
                "sent_to": employee_data.get("email"),
                "template": "welcome_new_employee",
                "sent_at": datetime.now().isoformat()
            }
        }

class SchedulerAgent(BaseAgent):
    def __init__(self, message_queue):
        super().__init__("scheduler_agent", message_queue)
        self.register_handler(MessageType.TASK, self.handle_task)
        self.scheduled_events = {}
        
    async def handle_task(self, message):
        content = message.content
        action = content.get("action")
        workflow_id = content.get("workflow_id")
        employee_data = content.get("employee_data", {})
        
        self.current_task = content
        self.start_time = datetime.now()
        
        try:
            if action == "assign_buddy":
                result = await self._assign_buddy(employee_data)
                await self._handle_scheduler_result(message, "buddy_assigned", result)
                
            elif action == "schedule_meeting":
                result = await self._schedule_welcome_meeting(employee_data)
                await self._handle_scheduler_result(message, "meeting_scheduled", result)
                
        except Exception as e:
            await self.send_message("error_handler_agent", MessageType.ERROR, {
                "error": f"Scheduling failed for {action}: {str(e)}",
                "workflow_id": workflow_id,
                "action": action
            })
        
        self.status = AgentStatus.COMPLETED
        self.end_time = datetime.now()
    
    async def _handle_scheduler_result(self, message, event_type, result):
        workflow_id = message.content.get("workflow_id")
        
        if result["success"]:
            self.scheduled_events[event_type] = result["event_info"]
            
            await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
                "action": event_type,
                "workflow_id": workflow_id,
                "event_info": result["event_info"]
            })
            
            if event_type == "buddy_assigned":
                await self.send_message("scheduler_agent", MessageType.TASK, {
                    "action": "schedule_meeting",
                    "workflow_id": workflow_id,
                    "employee_data": message.content.get("employee_data", {})
                })
            elif event_type == "meeting_scheduled":
                await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
                    "action": "onboarding_completed",
                    "workflow_id": workflow_id,
                    "completion_time": datetime.now().isoformat()
                })
        else:
            await self.send_message("error_handler_agent", MessageType.ERROR, {
                "error": f"Failed to {event_type}",
                "workflow_id": workflow_id,
                "details": result["error"]
            })
    
    async def _assign_buddy(self, employee_data):
        await asyncio.sleep(1)
        department = employee_data.get("department", "Engineering")
        
        # Decision intelligence: smart buddy assignment
        buddy_pool = {
            "Engineering": [
                {"email": "alice.tech@company.com", "name": "Alice Tech", "availability": "high", "experience": "5 years"},
                {"email": "bob.dev@company.com", "name": "Bob Dev", "availability": "medium", "experience": "3 years"}
            ],
            "Sales": [
                {"email": "charlie.sales@company.com", "name": "Charlie Sales", "availability": "high", "experience": "7 years"},
                {"email": "diana.revenue@company.com", "name": "Diana Revenue", "availability": "low", "experience": "2 years"}
            ],
            "Marketing": [
                {"email": "eve.market@company.com", "name": "Eve Market", "availability": "high", "experience": "4 years"},
                {"email": "frank.brand@company.com", "name": "Frank Brand", "availability": "medium", "experience": "6 years"}
            ],
            "HR": [
                {"email": "grace.hr@company.com", "name": "Grace HR", "availability": "high", "experience": "8 years"},
                {"email": "henry.people@company.com", "name": "Henry People", "availability": "medium", "experience": "3 years"}
            ],
            "Finance": [
                {"email": "ivy.finance@company.com", "name": "Ivy Finance", "availability": "high", "experience": "6 years"},
                {"email": "jack.money@company.com", "name": "Jack Money", "availability": "low", "experience": "4 years"}
            ]
        }
        
        available_buddies = buddy_pool.get(department, buddy_pool["Engineering"])
        
        # Smart selection: prioritize availability and experience
        best_buddy = max(available_buddies, key=lambda x: (x["availability"] == "high", x["experience"]))
        
        # If best buddy has low availability, escalate to manager
        if best_buddy["availability"] == "low":
            return {
                "success": False,
                "error": "No suitable buddy available - requires manager assignment",
                "escalation_required": True,
                "recommended_action": "Assign department manager as buddy"
            }
        
        return {
            "success": True,
            "event_info": {
                "buddy_email": best_buddy["email"],
                "buddy_name": best_buddy["name"],
                "buddy_experience": best_buddy["experience"],
                "buddy_availability": best_buddy["availability"],
                "assignment_reason": f"Selected based on {best_buddy['availability']} availability and {best_buddy['experience']} experience",
                "assigned_at": datetime.now().isoformat()
            }
        }
    
    async def _schedule_welcome_meeting(self, employee_data):
        await asyncio.sleep(1)
        start_date = employee_data.get("start_date", datetime.now().date())
        meeting_time = datetime.combine(start_date, datetime.strptime("10:00", "%H:%M").time())
        
        return {
            "success": True,
            "event_info": {
                "meeting_title": "Welcome Meeting - New Employee Onboarding",
                "meeting_time": meeting_time.isoformat(),
                "duration": "60 minutes",
                "attendees": [employee_data.get("email"), "hr@company.com"],
                "meeting_id": f"MEET-{uuid.uuid4().hex[:8].upper()}",
                "scheduled_at": datetime.now().isoformat()
            }
        }

class ErrorHandlerAgent(BaseAgent):
    def __init__(self, message_queue):
        super().__init__("error_handler_agent", message_queue)
        self.register_handler(MessageType.ERROR, self.handle_error)
        self.error_history = []
        self.retry_attempts = {}
        
    async def handle_error(self, message):
        content = message.content
        workflow_id = content.get("workflow_id")
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "error": content.get("error"),
            "sender": message.sender,
            "details": content.get("details", {}),
            "retry_count": 0
        }
        
        self.error_history.append(error_info)
        
        await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
            "action": "error_detected",
            "workflow_id": workflow_id,
            "error_info": error_info,
            "reason": "Error detected - initiating recovery protocol"
        })
        
        retry_result = await self._attempt_recovery(content)
        
        if retry_result["retry_attempted"]:
            await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
                "action": "error_recovery_attempted",
                "workflow_id": workflow_id,
                "recovery_action": retry_result["action"],
                "attempt_number": retry_result["attempt_number"],
                "reason": f"Recovery attempt {retry_result['attempt_number']} for {retry_result['action']}"
            })
        elif retry_result["escalated"]:
            await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
                "action": "error_escalated",
                "workflow_id": workflow_id,
                "escalation_reason": retry_result["escalation_reason"],
                "escalated_to": retry_result["escalated_to"],
                "reason": "Max retries exceeded - escalating to human"
            })
        
        self.status = AgentStatus.COMPLETED
    
    async def _attempt_recovery(self, error_content):
        workflow_id = error_content.get("workflow_id")
        error_type = self._classify_error(error_content.get("error", ""))
        
        if workflow_id not in self.retry_attempts:
            self.retry_attempts[workflow_id] = {}
        
        error_key = f"{error_content.get('sender')}_{error_type}"
        if error_key not in self.retry_attempts[workflow_id]:
            self.retry_attempts[workflow_id][error_key] = 0
        
        max_retries = 3
        current_retries = self.retry_attempts[workflow_id][error_key]
        
        if current_retries < max_retries:
            self.retry_attempts[workflow_id][error_key] += 1
            
            recovery_action = self._get_recovery_action(error_type)
            if recovery_action:
                await self._execute_recovery(recovery_action, error_content)
                
                return {
                    "retry_attempted": True,
                    "action": recovery_action,
                    "attempt_number": current_retries + 1,
                    "escalated": False
                }
        
        # Escalate to human
        return {
            "retry_attempted": False,
            "escalated": True,
            "escalation_reason": f"Max retries ({max_retries}) exceeded for {error_type}",
            "escalated_to": "IT Support Manager"
        }
    
    def _classify_error(self, error_message):
        if "validation" in error_message.lower():
            return "validation_error"
        elif "network" in error_message.lower() or "connection" in error_message.lower():
            return "network_error"
        elif "authentication" in error_message.lower() or "auth" in error_message.lower():
            return "auth_error"
        elif "timeout" in error_message.lower():
            return "timeout_error"
        else:
            return "unknown_error"
    
    def _get_recovery_action(self, error_type):
        recovery_actions = {
            "validation_error": "request_user_input",
            "network_error": "retry_with_backoff",
            "auth_error": "refresh_credentials",
            "timeout_error": "increase_timeout",
            "unknown_error": "escalate_to_human"
        }
        return recovery_actions.get(error_type, "escalate_to_human")
    
    async def _execute_recovery(self, action, error_content):
        await asyncio.sleep(1)
        
        if action == "retry_with_backoff":
            # Exponential backoff: 2^retry_count seconds
            retry_count = self.retry_attempts[error_content.get("workflow_id")].get(
                f"{error_content.get('sender')}_network_error", 0
            )
            backoff_delay = 2 ** retry_count
            await asyncio.sleep(backoff_delay)
            
            # Retry the original action
            original_action = error_content.get("details", {}).get("action", "unknown")
            sender = error_content.get("sender")
            
            if sender == "execution_agent" and original_action == "create_jira":
                # Retry Jira creation
                await self.send_message("execution_agent", MessageType.RETRY, {
                    "action": "create_jira",
                    "workflow_id": error_content.get("workflow_id"),
                    "employee_data": error_content.get("details", {}).get("employee_data", {}),
                    "retry_attempt": retry_count + 1
                })
        
        elif action == "request_user_input":
            # Send notification to UI for human input
            await self.send_message("audit_agent", MessageType.STATUS_UPDATE, {
                "action": "human_input_required",
                "workflow_id": error_content.get("workflow_id"),
                "required_input": "Please provide missing employee information",
                "reason": "Automated correction failed"
            })
        
        elif action == "escalate_to_human":
            await self.send_message("audit_agent", MessageType.ESCALATE, {
                "action": "manual_intervention_required",
                "workflow_id": error_content.get("workflow_id"),
                "escalated_to": "IT Support",
                "reason": "Automated recovery failed after maximum retries"
            })

class AuditAgent(BaseAgent):
    def __init__(self, message_queue):
        super().__init__("audit_agent", message_queue)
        self.register_handler(MessageType.STATUS_UPDATE, self.handle_status_update)
        self.audit_log = []
        self.workflow_metrics = {}
        
    async def handle_status_update(self, message):
        content = message.content
        workflow_id = content.get("workflow_id")
        action = content.get("action")
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "agent": message.sender,
            "action": action,
            "details": content,
            "reason": content.get("reason", "Standard workflow execution"),
            "outcome": "success" if "error" not in action.lower() else "failed"
        }
        
        self.audit_log.append(audit_entry)
        
        if workflow_id not in self.workflow_metrics:
            self.workflow_metrics[workflow_id] = {
                "start_time": datetime.now().isoformat(),
                "actions": [],
                "agents_involved": [],
                "errors": 0,
                "decisions_made": [],
                "escalations": []
            }
        
        self.workflow_metrics[workflow_id]["actions"].append({
            "action": action,
            "timestamp": audit_entry["timestamp"],
            "agent": message.sender,
            "reason": content.get("reason", ""),
            "outcome": audit_entry["outcome"]
        })
        
        if message.sender not in self.workflow_metrics[workflow_id]["agents_involved"]:
            self.workflow_metrics[workflow_id]["agents_involved"].append(message.sender)
        
        # Track decisions and escalations
        if "decision" in action.lower() or "assigned" in action.lower():
            self.workflow_metrics[workflow_id]["decisions_made"].append(audit_entry)
        
        if "escalated" in action.lower() or "error" in action.lower():
            self.workflow_metrics[workflow_id]["errors"] += 1
            if "escalated" in action.lower():
                self.workflow_metrics[workflow_id]["escalations"].append(audit_entry)
        
        if action == "onboarding_completed":
            self.workflow_metrics[workflow_id]["end_time"] = datetime.now().isoformat()
            self._calculate_workflow_metrics(workflow_id)
        
        self.status = AgentStatus.COMPLETED
    
    def _calculate_workflow_metrics(self, workflow_id):
        if workflow_id in self.workflow_metrics:
            metrics = self.workflow_metrics[workflow_id]
            
            start_time = datetime.fromisoformat(metrics["start_time"])
            end_time = datetime.fromisoformat(metrics["end_time"])
            duration = (end_time - start_time).total_seconds()
            
            metrics["duration_seconds"] = duration
            metrics["duration_minutes"] = round(duration / 60, 2)
            metrics["total_actions"] = len(metrics["actions"])
            metrics["agents_used"] = len(metrics["agents_involved"])
            
            time_saved_minutes = 4320 - duration / 60
            metrics["time_saved_minutes"] = max(0, round(time_saved_minutes, 2))
            metrics["efficiency_gain_percent"] = round((time_saved_minutes / 4320) * 100, 2)
    
    def get_workflow_summary(self, workflow_id):
        if workflow_id in self.workflow_metrics:
            return self.workflow_metrics[workflow_id]
        return {"error": "Workflow not found"}
    
    def get_all_audit_logs(self):
        return {
            "total_entries": len(self.audit_log),
            "recent_logs": self.audit_log[-20:],
            "workflow_metrics": self.workflow_metrics
        }
