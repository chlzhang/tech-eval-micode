"""
消息队列单元测试
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from src.communication.queue import (
    MessageQueue,
    MessageBroker,
    AgentEndpoint,
    Message,
    MessageType
)


class TestMessage:
    """消息测试"""
    
    def test_create_message(self):
        """测试创建消息"""
        msg = Message(
            id="test_1",
            sender="agent1",
            receiver="agent2",
            type=MessageType.DATA,
            data={"key": "value"}
        )
        
        assert msg.id == "test_1"
        assert msg.sender == "agent1"
        assert msg.receiver == "agent2"
        assert msg.type == MessageType.DATA
        assert msg.data == {"key": "value"}
    
    def test_message_to_dict(self):
        """测试消息转字典"""
        msg = Message(
            id="test_1",
            sender="agent1",
            receiver="agent2",
            type=MessageType.DATA,
            data={"key": "value"}
        )
        
        data = msg.to_dict()
        
        assert data["id"] == "test_1"
        assert data["sender"] == "agent1"
        assert data["type"] == "data"
    
    def test_message_from_dict(self):
        """测试从字典创建消息"""
        data = {
            "id": "test_1",
            "sender": "agent1",
            "receiver": "agent2",
            "type": "data",
            "data": {"key": "value"},
            "timestamp": "2024-01-01T00:00:00"
        }
        
        msg = Message.from_dict(data)
        
        assert msg.id == "test_1"
        assert msg.type == MessageType.DATA


class TestMessageQueue:
    """消息队列测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.queue = MessageQueue(self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_publish_and_consume(self):
        """测试发布和消费"""
        msg = Message(
            id="test_1",
            sender="agent1",
            receiver="agent2",
            type=MessageType.DATA,
            data={"key": "value"}
        )
        
        await self.queue.publish(msg)
        
        consumed = await self.queue.consume("agent2", timeout=1.0)
        
        assert consumed is not None
        assert consumed.id == "test_1"
        assert consumed.data == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_consume_timeout(self):
        """测试消费超时"""
        result = await self.queue.consume("agent2", timeout=0.1)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_multiple_messages(self):
        """测试多条消息"""
        for i in range(5):
            msg = Message(
                id=f"test_{i}",
                sender="agent1",
                receiver="agent2",
                type=MessageType.DATA,
                data={"index": i}
            )
            await self.queue.publish(msg)
        
        # 消费所有消息
        messages = await self.queue.consume_all("agent2")
        assert len(messages) == 5
    
    @pytest.mark.asyncio
    async def test_subscribe(self):
        """测试订阅"""
        received_messages = []
        
        async def handler(message):
            received_messages.append(message)
        
        await self.queue.subscribe("agent2", handler)
        
        msg = Message(
            id="test_1",
            sender="agent1",
            receiver="agent2",
            type=MessageType.DATA,
            data={"key": "value"}
        )
        
        await self.queue.publish(msg)
        
        assert len(received_messages) == 1
        assert received_messages[0].id == "test_1"
    
    def test_queue_size(self):
        """测试队列大小"""
        assert self.queue.get_queue_size("agent1") == 0
    
    @pytest.mark.asyncio
    async def test_persistence(self):
        """测试持久化"""
        msg = Message(
            id="test_1",
            sender="agent1",
            receiver="agent2",
            type=MessageType.DATA,
            data={"key": "value"}
        )
        
        await self.queue.publish(msg)
        
        # 检查持久化文件
        date_str = datetime.now().strftime("%Y%m%d")
        persist_file = Path(self.temp_dir) / f"messages_{date_str}.jsonl"
        assert persist_file.exists()


class TestMessageBroker:
    """消息代理测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.broker = MessageBroker(self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_send(self):
        """测试发送"""
        msg_id = await self.broker.send("agent1", "agent2", {"key": "value"})
        
        assert msg_id is not None
        
        # 消费消息
        msg = await self.broker.queue.consume("agent2", timeout=1.0)
        assert msg is not None
        assert msg.data == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """测试广播"""
        await self.broker.broadcast("agent1", ["agent2", "agent3", "agent4"], {"key": "value"})
        
        # 每个接收者都应该收到消息
        for agent_id in ["agent2", "agent3", "agent4"]:
            msg = await self.broker.queue.consume(agent_id, timeout=1.0)
            assert msg is not None


class TestAgentEndpoint:
    """Agent 端点测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.broker = MessageBroker(self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """测试发送消息"""
        agent1 = AgentEndpoint("agent1", self.broker)
        agent2 = AgentEndpoint("agent2", self.broker)
        
        await agent1.send("agent2", {"key": "value"})
        
        msg = await self.broker.queue.consume("agent2", timeout=1.0)
        assert msg is not None
        assert msg.data == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_message_handler(self):
        """测试消息处理器"""
        agent2 = AgentEndpoint("agent2", self.broker)
        
        received_messages = []
        
        async def handler(message):
            received_messages.append(message)
        
        agent2.on_message("data", handler)
        await agent2.start()
        
        # 发送消息
        agent1 = AgentEndpoint("agent1", self.broker)
        await agent1.send("agent2", {"key": "value"})
        
        # 等待处理
        await asyncio.sleep(0.1)
        
        assert len(received_messages) == 1
        assert received_messages[0].data == {"key": "value"}
        
        await agent2.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
