import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"

class MessageType(Enum):
    TASK = "task"
    RESPONSE = "response"
    ERROR = "error"
    STATUS_UPDATE = "status_update"
    RETRY = "retry"
    ESCALATE = "escalate"

@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.TASK
    sender: str = ""
    receiver: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3

class MessageQueue:
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.message_history: List[Message] = []
        self.lock = asyncio.Lock()
    
    def register_agent(self, agent_id: str):
        if agent_id not in self.queues:
            self.queues[agent_id] = asyncio.Queue()
    
    async def send(self, message: Message):
        async with self.lock:
            self.message_history.append(message)
        
        if message.receiver in self.queues:
            await self.queues[message.receiver].put(message)
        else:
            logging.warning(f"Agent {message.receiver} not found")
    
    async def receive(self, agent_id: str) -> Optional[Message]:
        if agent_id in self.queues:
            try:
                return await asyncio.wait_for(self.queues[agent_id].get(), timeout=1.0)
            except asyncio.TimeoutError:
                return None
        return None
    
    def get_messages_for_agent(self, agent_id: str) -> List[Message]:
        return [msg for msg in self.message_history if msg.receiver == agent_id]

class BaseAgent:
    def __init__(self, agent_id: str, message_queue: MessageQueue):
        self.agent_id = agent_id
        self.message_queue = message_queue
        self.status = AgentStatus.IDLE
        self.message_queue.register_agent(agent_id)
        self.handlers: Dict[MessageType, Callable] = {}
        self.current_task: Optional[Dict] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_log: List[str] = []
        
    def register_handler(self, message_type: MessageType, handler: Callable):
        self.handlers[message_type] = handler
    
    async def send_message(self, receiver: str, message_type: MessageType, content: Dict[str, Any], priority: int = 1):
        message = Message(
            sender=self.agent_id,
            receiver=receiver,
            type=message_type,
            content=content,
            priority=priority
        )
        await self.message_queue.send(message)
    
    async def process_message(self, message: Message):
        try:
            self.status = AgentStatus.RUNNING
            if message.type in self.handlers:
                await self.handlers[message.type](message)
            else:
                logging.warning(f"No handler for message type {message.type} in agent {self.agent_id}")
        except Exception as e:
            self.error_log.append(f"Error processing message: {str(e)}")
            await self.send_message(message.sender, MessageType.ERROR, 
                                 {"error": str(e), "original_message": message.content})
            self.status = AgentStatus.FAILED
        finally:
            if self.status != AgentStatus.FAILED:
                self.status = AgentStatus.IDLE
    
    async def run(self):
        while True:
            try:
                message = await self.message_queue.receive(self.agent_id)
                if message:
                    await self.process_message(message)
                await asyncio.sleep(0.1)
            except Exception as e:
                logging.error(f"Agent {self.agent_id} error: {str(e)}")
                self.error_log.append(f"Runtime error: {str(e)}")
    
    def get_status_info(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "current_task": self.current_task,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_count": len(self.error_log),
            "errors": self.error_log[-5:] if self.error_log else []
        }

class WorkflowOrchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue = MessageQueue()
        self.workflow_steps: List[Dict] = []
        self.current_workflow: Optional[str] = None
        self.workflow_history: List[Dict] = []
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
    def register_agent(self, agent: BaseAgent):
        self.agents[agent.agent_id] = agent
    
    def define_workflow(self, workflow_id: str, steps: List[Dict]):
        self.workflow_steps = steps
        self.current_workflow = workflow_id
        
        workflow_config = {
            "workflow_id": workflow_id,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }
        self.workflow_history.append(workflow_config)
    
    async def start_workflow(self, initial_data: Dict[str, Any]) -> str:
        workflow_id = str(uuid.uuid4())
        
        workflow_instance = {
            "workflow_id": workflow_id,
            "status": "running",
            "start_time": datetime.now(),
            "data": initial_data,
            "current_step": 0,
            "completed_steps": [],
            "failed_steps": [],
            "agents_involved": []
        }
        
        self.workflow_history.append(workflow_instance)
        
        if self.workflow_steps:
            first_step = self.workflow_steps[0]
            await self.execute_step(first_step, workflow_instance, initial_data)
        
        return workflow_id
    
    async def execute_step(self, step: Dict, workflow_instance: Dict, data: Dict[str, Any]):
        step_name = step["name"]
        agent_id = step["agent"]
        action = step["action"]
        
        try:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                await agent.send_message(agent_id, MessageType.TASK, {
                    "action": action,
                    "workflow_id": workflow_instance["workflow_id"],
                    "step_name": step_name,
                    "data": data
                })
                
                workflow_instance["agents_involved"].append(agent_id)
                logging.info(f"Executing step {step_name} with agent {agent_id}")
        except Exception as e:
            logging.error(f"Failed to execute step {step_name}: {str(e)}")
            workflow_instance["failed_steps"].append(step_name)
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        for workflow in self.workflow_history:
            if workflow.get("workflow_id") == workflow_id:
                return workflow
        return {"error": "Workflow not found"}
    
    def get_all_agents_status(self) -> Dict[str, Any]:
        return {
            "agents": {agent_id: agent.get_status_info() for agent_id, agent in self.agents.items()},
            "total_agents": len(self.agents),
            "active_workflows": len([w for w in self.workflow_history if w.get("status") == "running"])
        }
    
    async def start_all_agents(self):
        tasks = []
        for agent in self.agents.values():
            task = asyncio.create_task(agent.run())
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
