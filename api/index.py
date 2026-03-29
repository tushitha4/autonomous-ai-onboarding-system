import json
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import asyncio
import logging
import time
import random
import os

from agent_framework import WorkflowOrchestrator, MessageQueue
from agents import (
    PlannerAgent, DataAgent, ExecutionAgent, 
    SchedulerAgent, ErrorHandlerAgent, AuditAgent
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'multi-agent-system-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize agents and orchestrator
message_queue = MessageQueue()
orchestrator = WorkflowOrchestrator(message_queue)

# Register all agents
planner_agent = PlannerAgent("planner_agent", message_queue)
data_agent = DataAgent("data_agent", message_queue)
execution_agent = ExecutionAgent("execution_agent", message_queue)
scheduler_agent = SchedulerAgent("scheduler_agent", message_queue)
error_handler_agent = ErrorHandlerAgent("error_handler_agent", message_queue)
audit_agent = AuditAgent("audit_agent", message_queue)

orchestrator.register_agent(planner_agent)
orchestrator.register_agent(data_agent)
orchestrator.register_agent(execution_agent)
orchestrator.register_agent(scheduler_agent)
orchestrator.register_agent(error_handler_agent)
orchestrator.register_agent(audit_agent)

# Start agent system
def start_agent_system():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(orchestrator.start_all_agents())
    loop.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/agents/status')
def get_agents_status():
    agents_status = {}
    for agent in [planner_agent, data_agent, execution_agent, scheduler_agent, error_handler_agent, audit_agent]:
        agents_status[agent.name] = {
            'status': agent.status.value,
            'current_task': agent.current_task,
            'errors': len(agent.error_history),
            'start_time': agent.start_time.isoformat() if agent.start_time else None,
            'end_time': agent.end_time.isoformat() if agent.end_time else None
        }
    return jsonify(agents_status)

@app.route('/api/start_onboarding', methods=['POST'])
def start_onboarding():
    try:
        employee_data = request.json
        workflow_id = f"workflow_{int(time.time())}"
        
        # Define workflow steps
        workflow_steps = [
            {"name": "validate_employee_info", "agent": "data_agent"},
            {"name": "create_email_account", "agent": "execution_agent"},
            {"name": "create_jira_ticket", "agent": "execution_agent"},
            {"name": "create_slack_access", "agent": "execution_agent"},
            {"name": "assign_department_buddy", "agent": "scheduler_agent"},
            {"name": "schedule_general_onboarding", "agent": "scheduler_agent"}
        ]
        
        orchestrator.define_workflow(workflow_steps)
        
        # Start workflow in background thread
        def run_workflow():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator.start_workflow({"employee_data": employee_data}))
            loop.close()
        
        workflow_thread = threading.Thread(target=run_workflow)
        workflow_thread.daemon = True
        workflow_thread.start()
        
        return jsonify({"success": True, "workflow_id": workflow_id})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/audit/logs')
def get_audit_logs():
    return jsonify({"logs": orchestrator.get_audit_logs()})

# Vercel serverless handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

# Start agent system in background
agent_thread = threading.Thread(target=start_agent_system)
agent_thread.daemon = True
agent_thread.start()

if __name__ == '__main__':
    print("🤖 Multi-Agent AI System Starting...")
    print("📊 Dashboard: http://localhost:5000")
    print("🔧 Agents: 6 specialized agents ready")
    print("🎯 Workflow: Employee Onboarding Automation")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
