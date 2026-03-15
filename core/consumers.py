import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Project, Story

class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'project_{self.project_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def save_project_content(self, project_id, payload):
        Project.objects.filter(id=project_id).update(content=payload)

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        payload = data.get('payload')

        if message_type == 'project_update':
            await self.save_project_content(self.project_id, payload)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'project_message',
                'message_type': message_type,
                'payload': payload,
                'sender_channel_name': self.channel_name,
            }
        )

    # Receive message from room group
    async def project_message(self, event):
        message_type = event['message_type']
        payload = event['payload']
        sender_channel_name = event.get('sender_channel_name')

        # Prevent echoing back to the sender
        if self.channel_name != sender_channel_name:
            await self.send(text_data=json.dumps({
                'type': message_type,
                'payload': payload
            }))

class StoryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.story_id = self.scope['url_route']['kwargs']['story_id']
        self.room_group_name = f'story_{self.story_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def save_story_content(self, story_id, payload):
        Story.objects.filter(id=story_id).update(content=payload)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        payload = data.get('payload')

        if message_type == 'story_update':
            await self.save_story_content(self.story_id, payload)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'story_message',
                'message_type': message_type,
                'payload': payload,
                'sender_channel_name': self.channel_name,
            }
        )

    async def story_message(self, event):
        if self.channel_name != event.get('sender_channel_name'):
            await self.send(text_data=json.dumps({
                'type': event['message_type'],
                'payload': event['payload']
            }))
