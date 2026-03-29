#!/usr/bin/env python3
"""
🎬 Multi-Agent AI System Demo Script
Demonstrates the complete employee onboarding workflow
"""

import asyncio
import json
import time
from datetime import datetime
from agent_framework import WorkflowOrchestrator, MessageQueue
from agents import (
    PlannerAgent, DataAgent, ExecutionAgent, 
    SchedulerAgent, ErrorHandlerAgent, AuditAgent
)

class DemoRunner:
    def __init__(self):
        self.orchestrator = WorkflowOrchestrator()
        self.message_queue = MessageQueue()
        self.setup_agents()
        
    def setup_agents(self):
        """Initialize all agents"""
        self.planner = PlannerAgent(self.message_queue)
        self.data_agent = DataAgent(self.message_queue)
        self.execution_agent = ExecutionAgent(self.message_queue)
        self.scheduler_agent = SchedulerAgent(self.message_queue)
        self.error_handler = ErrorHandlerAgent(self.message_queue)
        self.audit_agent = AuditAgent(self.message_queue)
        
        # Register agents with orchestrator
        self.orchestrator.register_agent(self.planner)
        self.orchestrator.register_agent(self.data_agent)
        self.orchestrator.register_agent(self.execution_agent)
        self.orchestrator.register_agent(self.scheduler_agent)
        self.orchestrator.register_agent(self.error_handler)
        self.orchestrator.register_agent(self.audit_agent)
    
    async def run_demo(self):
        """Run complete demo workflow"""
        print("🤖 Multi-Agent AI System Demo Starting...")
        print("=" * 60)
        
        # Sample employee data
        employee_data = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson@company.com",
            "department": "Engineering",
            "start_date": "2024-04-01"
        }
        
        print(f"👤 New Employee: {employee_data['first_name']} {employee_data['last_name']}")
        print(f"📧 Email: {employee_data['email']}")
        print(f"🏢 Department: {employee_data['department']}")
        print(f"📅 Start Date: {employee_data['start_date']}")
        print("=" * 60)
        
        # Start workflow
        start_time = time.time()
        workflow_id = await self.orchestrator.start_workflow(employee_data)
        
        print(f"🔄 Workflow Started: {workflow_id}")
        print("⏳ Processing...")
        
        # Simulate agent processing
        await self.simulate_agent_processing()
        
        # Wait for completion
        await asyncio.sleep(15)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 60)
        print("✅ Workflow Completed!")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        # Show results
        await self.show_results(workflow_id, duration)
        
        # Calculate business impact
        self.calculate_impact(duration)
    
    async def simulate_agent_processing(self):
        """Simulate the agent processing workflow"""
        steps = [
            ("🧠 Planner Agent", "Creating onboarding plan..."),
            ("🔍 Data Agent", "Validating employee data..."),
            ("⚙️ Execution Agent", "Creating email account..."),
            ("⚙️ Execution Agent", "Creating Jira account..."),
            ("⚙️ Execution Agent", "Creating Slack account..."),
            ("📅 Scheduler Agent", "Assigning onboarding buddy..."),
            ("📅 Scheduler Agent", "Scheduling welcome meeting..."),
            ("⚙️ Execution Agent", "Sending welcome email..."),
            ("📋 Audit Agent", "Logging completion..."),
        ]
        
        for agent, action in steps:
            print(f"  {agent}: {action}")
            await asyncio.sleep(1.5)
    
    async def show_results(self, workflow_id, duration):
        """Display workflow results"""
        print("\n📊 Workflow Results:")
        print("-" * 40)
        
        # Get workflow status
        status = await self.orchestrator.get_workflow_status(workflow_id)
        
        if "error" not in status:
            print("✅ All tasks completed successfully")
            print(f"🤖 Agents involved: {len(status.get('agents_involved', []))}")
            print(f"📋 Total steps: {len(status.get('completed_steps', []))}")
        else:
            print("❌ Workflow encountered errors")
        
        # Get audit logs
        audit_data = self.audit_agent.get_all_audit_logs()
        print(f"📝 Audit entries: {audit_data['total_entries']}")
        
        # Show recent actions
        recent_logs = audit_data['recent_logs'][-5:]
        print("\n🔄 Recent Actions:")
        for log in recent_logs:
            timestamp = datetime.fromisoformat(log['timestamp']).strftime("%H:%M:%S")
            print(f"  {timestamp} - {log['agent']}: {log['action']}")
    
    def calculate_impact(self, duration):
        """Calculate and display business impact"""
        print("\n💰 Business Impact Analysis:")
        print("-" * 40)
        
        # Manual process time (3 days = 4320 minutes)
        manual_time_minutes = 4320
        ai_time_minutes = duration / 60
        
        time_saved = manual_time_minutes - ai_time_minutes
        efficiency_gain = (time_saved / manual_time_minutes) * 100
        
        print(f"⏰ Manual Process: {manual_time_minutes} minutes (3 days)")
        print(f"🤖 AI Process: {ai_time_minutes:.2f} minutes")
        print(f"💾 Time Saved: {time_saved:.2f} minutes")
        print(f"🚀 Efficiency Gain: {efficiency_gain:.1f}%")
        
        # Cost savings (assuming $50/hour for HR staff)
        hourly_rate = 50
        cost_saved = (time_saved / 60) * hourly_rate
        print(f"💵 Cost Savings: ${cost_saved:.2f} per employee")
        
        # Annual impact (assuming 100 new employees)
        annual_employees = 100
        annual_time_saved = (time_saved / 60) * annual_employees
        annual_cost_saved = cost_saved * annual_employees
        
        print(f"\n📈 Annual Impact (100 employees):")
        print(f"  ⏰ Time Saved: {annual_time_saved:.1f} hours")
        print(f"  💵 Cost Saved: ${annual_cost_saved:,.2f}")
        print(f"  👥 Productivity Gain: {annual_time_saved / 8:.1f} workdays")

async def main():
    """Main demo function"""
    demo = DemoRunner()
    await demo.run_demo()
    
    print("\n🎉 Demo Complete!")
    print("🌐 Start the web interface: python main.py")
    print("📊 Access dashboard: http://localhost:5000")

if __name__ == "__main__":
    print("🎬 Starting Multi-Agent AI System Demo...")
    print("This demo showcases the complete employee onboarding workflow")
    print("using 6 specialized AI agents working together.\n")
    
    asyncio.run(main())
