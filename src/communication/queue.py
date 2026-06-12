"""
消息队列

提供 Agent 间通信的消息队列：
1. 异步消息传递
2. 发布/订阅模式
3. 消息持久化
4. 错误处理
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum


class MessageType(Enum):
    """消息类型"""
    DATA = "data"
    CONTROL = "control"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass
class Message:
    """消息"""
    id: str
    sender: str
    receiver: str
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "reply_to": self.reply_to,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建"""
        return cls(
            id=data["id"],
            sender=data["sender"],
            receiver=data["receiver"],
            type=MessageType(data["type"]),
            data=data["data"],
            timestamp=data.get("timestamp"),
            reply_to=data.get("reply_to"),
            metadata=data.get("metadata", {})
        )


class MessageQueue:
    """消息队列"""
    
    def __init__(self, persist_dir: str = None):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._persist_dir = Path(persist_dir) if persist_dir else None
        self._message_counter = 0
        
        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_id(self) -> str:
        """生成消息 ID"""
        self._message_counter += 1
        return f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._message_counter}"
    
    def _get_queue(self, agent_id: str) -> asyncio.Queue:
        """获取或创建队列"""
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()
        return self._queues[agent_id]
    
    async def publish(self, message: Message):
        """发布消息"""
        # 获取目标队列
        queue = self._get_queue(message.receiver)
        
        # 放入队列
        await queue.put(message)
        
        # 通知订阅者
        await self._notify_subscribers(message)
        
        # 持久化
        if self._persist_dir:
            await self._persist_message(message)
    
    async def subscribe(self, agent_id: str, callback: Callable[[Message], Awaitable[None]]):
        """订阅消息"""
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
        
        self._subscribers[agent_id].append(callback)
    
    async def _notify_subscribers(self, message: Message):
        """通知订阅者"""
        subscribers = self._subscribers.get(message.receiver, [])
        
        for callback in subscribers:
            try:
                await callback(message)
            except Exception as e:
                print(f"Subscriber error: {e}")
    
    async def _persist_message(self, message: Message):
        """持久化消息"""
        if not self._persist_dir:
            return
        
        # 按日期组织文件
        date_str = datetime.now().strftime("%Y%m%d")
        file_path = self._persist_dir / f"messages_{date_str}.jsonl"
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(message.to_dict(), ensure_ascii=False) + "\n")
    
    async def consume(self, agent_id: str, timeout: float = None) -> Optional[Message]:
        """消费消息"""
        queue = self._get_queue(agent_id)
        
        try:
            if timeout:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                message = await queue.get()
            return message
        except asyncio.TimeoutError:
            return None
    
    async def consume_all(self, agent_id: str) -> List[Message]:
        """消费所有可用消息"""
        queue = self._get_queue(agent_id)
        messages = []
        
        while not queue.empty():
            try:
                message = queue.get_nowait()
                messages.append(message)
            except asyncio.QueueEmpty:
                break
        
        return messages
    
    def get_queue_size(self, agent_id: str) -> int:
        """获取队列大小"""
        queue = self._queues.get(agent_id)
        return queue.qsize() if queue else 0
    
    def clear_queue(self, agent_id: str):
        """清空队列"""
        if agent_id in self._queues:
            self._queues[agent_id] = asyncio.Queue()


class MessageBroker:
    """消息代理
    
    提供高级消息路由功能：
    1. 点对点通信
    2. 发布/订阅
    3. 请求/响应
    """
    
    def __init__(self, persist_dir: str = None):
        self.queue = MessageQueue(persist_dir)
        self._response_futures: Dict[str, asyncio.Future] = {}
    
    async def send(self, sender: str, receiver: str, data: Dict[str, Any], 
                   msg_type: MessageType = MessageType.DATA) -> str:
        """发送消息"""
        message = Message(
            id=self.queue._generate_id(),
            sender=sender,
            receiver=receiver,
            type=msg_type,
            data=data
        )
        
        await self.queue.publish(message)
        return message.id
    
    async def request(self, sender: str, receiver: str, data: Dict[str, Any],
                     timeout: float = 30.0) -> Dict[str, Any]:
        """请求-响应模式"""
        # 创建 Future 用于等待响应
        request_id = self.queue._generate_id()
        future = asyncio.get_event_loop().create_future()
        self._response_futures[request_id] = future
        
        # 发送请求
        message = Message(
            id=request_id,
            sender=sender,
            receiver=receiver,
            type=MessageType.DATA,
            data=data,
            metadata={"expects_response": True}
        )
        
        await self.queue.publish(message)
        
        try:
            # 等待响应
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            raise TimeoutError(f"请求超时: {request_id}")
        finally:
            self._response_futures.pop(request_id, None)
    
    async def respond(self, original_message: Message, data: Dict[str, Any]):
        """响应请求"""
        if not original_message.metadata.get("expects_response"):
            return
        
        response = Message(
            id=self.queue._generate_id(),
            sender=original_message.receiver,
            receiver=original_message.sender,
            type=MessageType.DATA,
            data=data,
            reply_to=original_message.id
        )
        
        # 检查是否有等待的 Future
        future = self._response_futures.get(original_message.id)
        if future and not future.done():
            future.set_result(data)
        
        await self.queue.publish(response)
    
    async def broadcast(self, sender: str, receivers: List[str], data: Dict[str, Any]):
        """广播消息"""
        for receiver in receivers:
            await self.send(sender, receiver, data)


class AgentEndpoint:
    """Agent 端点
    
    封装 Agent 的消息收发功能
    """
    
    def __init__(self, agent_id: str, broker: MessageBroker):
        self.agent_id = agent_id
        self.broker = broker
        self._handlers: Dict[str, Callable] = {}
        self._running = False
    
    async def send(self, receiver: str, data: Dict[str, Any]) -> str:
        """发送消息"""
        return await self.broker.send(self.agent_id, receiver, data)
    
    async def request(self, receiver: str, data: Dict[str, Any], 
                     timeout: float = 30.0) -> Dict[str, Any]:
        """发送请求"""
        return await self.broker.request(self.agent_id, receiver, data, timeout)
    
    async def respond(self, original_message: Message, data: Dict[str, Any]):
        """响应请求"""
        await self.broker.respond(original_message, data)
    
    def on_message(self, msg_type: str, handler: Callable):
        """注册消息处理器"""
        self._handlers[msg_type] = handler
    
    async def start(self):
        """启动消息监听"""
        self._running = True
        
        await self.broker.queue.subscribe(self.agent_id, self._handle_message)
    
    async def stop(self):
        """停止消息监听"""
        self._running = False
    
    async def _handle_message(self, message: Message):
        """处理消息"""
        if not self._running:
            return
        
        msg_type = message.type.value
        handler = self._handlers.get(msg_type)
        
        if handler:
            try:
                await handler(message)
            except Exception as e:
                print(f"Handler error: {e}")
