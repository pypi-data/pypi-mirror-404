import json
from typing import Any

from fastapi.exceptions import RequestValidationError
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .exception import APIException


class APIRender:
    @staticmethod
    def display(message, code=200):
        message = APIRender.clean_message(message)
        response = message if isinstance(message, dict) else {'title': message}
        response = APIRender.format_message(response, code)
        return JSONResponse(
            status_code=code,
            content=response
        )

    @staticmethod
    def format_message(message: dict, code: int):
        formatted_message = {
            'title': '',
            'type': 'about:blank',
            'detail': None,
            'status': code,
            'instance': '',
        }

        if 'title' in message:
            formatted_message['title'] = message['title']

        if not formatted_message['title'] and 'message' in message:
            formatted_message['title']  = message['message']

        if 'type' in message:
            formatted_message['type'] = message['type']

        if 'detail' in message:
            # TSL Fix
            if 'title' not in message and isinstance(message['detail'], str):
                formatted_message['title'] = message['detail']
            else:
                formatted_message['detail'] = message['detail']

        if 'status' in message:
            formatted_message['status'] = message['status']

        if 'instance' in message:
            formatted_message['instance'] = message['instance']

        return formatted_message

    @staticmethod
    def clean_message(message) -> str|dict:
        # Check if empty
        if not message:
            return ''

        # Check if Dictionary
        if isinstance(message, dict):
            return message

        # Check if JSON String
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            return message

    @staticmethod
    def error(message=None, code=500):
        return APIRender.display(message, code)

    @staticmethod
    def get_plain_message(message=None, code=500) -> str:
        message = APIRender.clean_message(message)

        # RCP format 1
        if 'detail' in message:
            message = message['detail']

        # RCP format 2
        if 'message' in message:
            message = message['message']

        if not message:
            match code:
                case 401:
                    message = 'Unauthorized.'
                case _:
                    message = 'Unknown error.'

        return message

    @staticmethod
    def request_errors(e) -> JSONResponse:
        message = 'The given data was invalid.'
        formatted_errors = APIRender.clean_data(APIRender.process_errors(e))
        first_error = formatted_errors[0]
        if 'loc' in first_error and 'type' in first_error:
            loc = first_error['loc']
            type_ = first_error['type']

            if type_ == 'value_error' and 'Value error' in first_error['msg']:
                message = first_error['msg'].removeprefix("Value error, ")
            else:
                message = f'Field {loc} is {type_}.' if loc != 'body' else f'Body is {type_}.'

        return APIRender.display({'title': message, 'detail': ''}, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @staticmethod
    def pydantic_validation_handler(_: Request, e: ValidationError) -> JSONResponse:
        return APIRender.request_errors(e)

    @staticmethod
    def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return APIRender.request_errors(exc)

    @staticmethod
    def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        message = (exc.args[0] if exc.args else str(exc))
        return APIRender.display(message, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def http_exception_handler(request: Request, e: HTTPException) -> JSONResponse:
        if e.status_code == status.HTTP_401_UNAUTHORIZED and request.url.path in ['/docs', '/redoc', '/openapi.json']:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'message': 'Unauthorized'},
                headers={'WWW-Authenticate': 'Basic realm="docs"'},
            )

        message = APIRender.get_plain_message(e.detail, e.status_code)

        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            APIRender.display('Unauthorized.', status.HTTP_401_UNAUTHORIZED)

        return APIRender.display(message, e.status_code)

    @staticmethod
    def api_exception_handler(_: Request, e: APIException):
        return APIRender.display(e.get_error(), e.code)

    @staticmethod
    async def generic_exception_handler(_: Request, e: Exception) -> JSONResponse:
        message = f'{e}'
        return APIRender.display(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def not_found(resource):
        message = f'{resource} not found.'
        return APIRender.display(message, status.HTTP_404_NOT_FOUND)

    @staticmethod
    def loc_to_dot_sep(loc: tuple[str | int, ...]) -> str:
        path = ''
        for i, x in enumerate(loc):
            if isinstance(x, str):
                if i > 0:
                    path += '.'
                path += x
            elif isinstance(x, int):
                path += f'[{x}]'
            else:
                raise TypeError('Unexpected type')
        return path

    @staticmethod
    def process_errors(e: ValidationError) -> list[dict[str, Any]]:
        new_errors: list[dict[str, Any]] = e.errors()
        for error in new_errors:
            error['loc'] = APIRender.loc_to_dot_sep(error['loc'])
        return new_errors

    @staticmethod
    def clean_data(data):
        cleaned_data = []
        for item in data:
            cleaned_item = item.copy()
            if isinstance(cleaned_item.get('input'), type):
                cleaned_item['input'] = str(cleaned_item['input'])
            cleaned_data.append(cleaned_item)
        return cleaned_data