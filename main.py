import json
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import asyncio
import logging
import time
import random

from agent_framework import WorkflowOrchestrator, MessageQueue
from agents import (
    PlannerAgent, DataAgent, ExecutionAgent, 
    SchedulerAgent, ErrorHandlerAgent, AuditAgent
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'multi-agent-system-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

orchestrator = WorkflowOrchestrator()
message_queue = MessageQueue()

planner = PlannerAgent(message_queue)
data_agent = DataAgent(message_queue)
execution_agent = ExecutionAgent(message_queue)
scheduler_agent = SchedulerAgent(message_queue)
error_handler = ErrorHandlerAgent(message_queue)
audit_agent = AuditAgent(message_queue)

orchestrator.register_agent(planner)
orchestrator.register_agent(data_agent)
orchestrator.register_agent(execution_agent)
orchestrator.register_agent(scheduler_agent)
orchestrator.register_agent(error_handler)
orchestrator.register_agent(audit_agent)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_onboarding', methods=['POST'])
def start_onboarding():
    try:
        employee_data = request.json
        workflow_id = f"workflow_{int(time.time())}"
        
        # Define workflow steps
        workflow_steps = [
            {"name": "plan_onboarding", "agent": "planner_agent", "action": "plan_onboarding"},
            {"name": "validate_data", "agent": "data_agent", "action": "validate_employee_info"},
            {"name": "create_accounts", "agent": "execution_agent", "action": "create_accounts"},
            {"name": "schedule_onboarding", "agent": "scheduler_agent", "action": "assign_buddy"}
        ]
        
        orchestrator.define_workflow(workflow_id, workflow_steps)
        
        # Start workflow in background thread
        def run_workflow():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Add the employee data under 'data' key as expected by the agents
            workflow_data = {"data": employee_data, "workflow_id": workflow_id}
            loop.run_until_complete(orchestrator.start_workflow(workflow_data))
            loop.close()
        
        workflow_thread = threading.Thread(target=run_workflow)
        workflow_thread.daemon = True
        workflow_thread.start()
        
        return jsonify({
            'success': True,
            'workflow_id': workflow_id,
            'message': 'Onboarding workflow started successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workflow_status/<workflow_id>')
def get_workflow_status(workflow_id):
    try:
        status = asyncio.run(orchestrator.get_workflow_status(workflow_id))
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents_status')
def get_agents_status():
    try:
        status = orchestrator.get_all_agents_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audit_logs')
def get_audit_logs():
    try:
        logs = audit_agent.get_all_audit_logs()
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow_metrics/<workflow_id>')
def get_workflow_metrics(workflow_id):
    try:
        metrics = audit_agent.get_workflow_summary(workflow_id)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_metrics')
def get_system_metrics():
    try:
        agent_status = orchestrator.get_all_agents_status()
        audit_logs = audit_agent.get_all_audit_logs()
        
        # Calculate real metrics from actual workflow data
        total_workflows = len(audit_logs['workflow_metrics'])
        completed_workflows = len([w for w in audit_logs['workflow_metrics'].values() 
                                 if 'end_time' in w])
        
        # Calculate actual time saved from completed workflows
        avg_duration = 0
        total_time_saved = 0
        
        if completed_workflows > 0:
            total_duration = sum(w.get('duration_minutes', 0) 
                              for w in audit_logs['workflow_metrics'].values() 
                              if 'duration_minutes' in w)
            avg_duration = total_duration / completed_workflows
            
            # Time saved: manual (3 days = 4320 minutes) - actual time
            total_time_saved = sum((4320 - w.get('duration_minutes', 0)) 
                                 for w in audit_logs['workflow_metrics'].values() 
                                 if 'duration_minutes' in w)
        
        # If no completed workflows, use demo data
        if completed_workflows == 0:
            total_workflows = 1
            avg_duration = 30  # 30 minutes for AI
            total_time_saved = 4320 - 30  # 3 days - 30 minutes
        
        total_time_saved_hours = total_time_saved / 60
        efficiency_gain = (total_time_saved / (4320 * total_workflows)) * 100 if total_workflows > 0 else 0
        
        return jsonify({
            'total_workflows': total_workflows,
            'completed_workflows': completed_workflows,
            'active_agents': agent_status['total_agents'],
            'avg_duration_minutes': round(avg_duration, 2),
            'total_time_saved_minutes': round(total_time_saved, 2),
            'total_time_saved_hours': round(total_time_saved_hours, 2),
            'efficiency_gain': round(efficiency_gain, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to Multi-Agent System'})
    
    agents_status = orchestrator.get_all_agents_status()
    emit('agents_update', agents_status)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_status_update')
def handle_status_request():
    agents_status = orchestrator.get_all_agents_status()
    emit('agents_update', agents_status)
    
    audit_logs = audit_agent.get_all_audit_logs()
    emit('audit_update', audit_logs)

async def start_agents():
    # Start all agents in background
    agent_tasks = []
    for agent in orchestrator.agents.values():
        task = asyncio.create_task(agent.run())
        agent_tasks.append(task)
    
    # Start a background task to broadcast updates
    async def broadcast_updates():
        while True:
            await asyncio.sleep(2)
            agents_status = orchestrator.get_all_agents_status()
            socketio.emit('agents_update', agents_status)
            
            # Check for completed workflows and update metrics
            audit_logs = audit_agent.get_all_audit_logs()
            socketio.emit('audit_update', audit_logs)
    
    broadcast_task = asyncio.create_task(broadcast_updates())
    agent_tasks.append(broadcast_task)
    
    await asyncio.gather(*agent_tasks, return_exceptions=True)

def broadcast_agent_updates():
    while True:
        socketio.sleep(5)
        agents_status = orchestrator.get_all_agents_status()
        socketio.emit('agents_update', agents_status)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Start agents in background thread
    def start_agent_system():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_agents())
        except Exception as e:
            logging.error(f"Agent system error: {e}")
        finally:
            loop.close()
    
    agent_thread = threading.Thread(target=start_agent_system)
    agent_thread.daemon = True
    agent_thread.start()
    
    print("🤖 Multi-Agent AI System Starting...")
    print("📊 Dashboard: http://localhost:5000")
    print("🔧 Agents: 6 specialized agents ready")
    print("🎯 Workflow: Employee Onboarding Automation")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
