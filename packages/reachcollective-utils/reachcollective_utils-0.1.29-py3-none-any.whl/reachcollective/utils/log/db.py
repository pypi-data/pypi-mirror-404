import json
import uuid
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession


class AppDBLog:

    def __init__(self, db: AsyncSession, log_model, instance = None):
        self.db = db
        self.log_model = log_model
        self.instance = instance
        self.snapshot = {}
        self.changes = {}
        self.fields = []
        self.model_name = ''
        self.model_id = None
        self.status = 'active'

        # Init
        self.init(instance)

    def init(self, instance):
        if instance:
            self.fields = self.get_fields(instance)
            self.snapshot = self.get_snapshot(instance)

    async def crud(
        self,
        user_id,
        action,
        model_pk_name = 'id',
        status='active'
    ):
        self.model_name = self.get_table_name(self.instance)
        instance_id = getattr(self.instance, model_pk_name, None)
        self.model_id = str(instance_id)
        self.status = status

        match action:
            case 'create':
                description = self.get_description(action)
                await self.add(user_id, action, self.model_name, self.model_id, description)
            case 'update':
                await self.update(user_id)
            case 'delete':
                description = self.get_description(action)
                await self.add(user_id, action, self.model_name, self.model_id, description, self.snapshot)

    # pylint: disable=too-many-positional-arguments
    async def add(
        self,
        user_id=None,
        action=None,
        model_name=None,
        model_id=None,
        description=None,
        snapshot=None,
    ):
        data = {'user_id': user_id, 'action': action}
        if model_name:
            data['model'] = model_name
        if model_id:
            data['model_id'] =  str(model_id)
        if description:
            data['description'] = description
        if snapshot:
            data['snapshot'] = snapshot

        data['status'] = self.status

        log = self.log_model.model_validate(data)
        self.db.add(log)
        await self.db.commit()
        return log

    def get_changes(self):
        changes = []
        for field in self.fields:
            old_value = self.snapshot.get(field)
            if old_value is not None:
                new_value = self.safe_to_str(getattr(self.instance, field))
                if new_value != old_value:
                    change = {
                        'field': field,
                        'old_value': old_value,
                        'new_value': new_value,
                    }
                    changes.append(change)

        return changes

    async def update(self, user_id):
        self.changes = self.get_changes()
        action = 'update'
        for change in self.changes:
            description = self.get_description(action, change['field'], change['old_value'], change['new_value'])
            await self.add(user_id, action, self.model_name, self.model_id, description)

    @staticmethod
    def get_model_name(instance, capitalize=False):
        class_name = instance.__class__.__name__
        name = class_name.lower()
        return name.capitalize() if capitalize else name

    @staticmethod
    def get_table_name(instance):
        return instance.__table__.name

    @staticmethod
    def get_fields(instance):
        exclude = ['created_at', 'updated_at']
        columns = list(instance.__fields__.keys())
        fields = [col for col in columns if col not in exclude]
        return fields

    def get_snapshot(self, instance):
        snapshot = {}
        for field in self.fields:
            snapshot[field] = self.safe_to_str(getattr(instance, field))
        return snapshot

    def get_description(self, action, field='', old_value='', new_value=''):
        past_tense = {
            'create': 'created',
            'update': 'updated',
            'delete': 'deleted',
            'edit': 'edited'
        }

        past_action = past_tense.get(action, action)
        match action:
            case 'update':
                description = f'(field: {field}) changed from ' f'"{old_value}" to "{new_value}"'
            case _:
                title = self.model_name.capitalize()
                description = f'{title} (id: {self.model_id}) was {past_action}'

        return description

    @staticmethod
    def safe_to_str(value):
        if value is None:
            return None
        if isinstance(value, (int, float, bool, str, uuid.UUID)):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return json.dumps(value, sort_keys=True)
        if isinstance(value, list):
            return json.dumps(value, sort_keys=True)
        return str(value)
