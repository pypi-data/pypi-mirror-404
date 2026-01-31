import csv
import io
import json
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel
from starlette.responses import StreamingResponse


def format_keycloack_error(data) -> dict:
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return json.loads(data)


def generate_document_name(type_: str, params: dict) -> str:
    match type_:
        case 'interval':
            formatted = params['from_date'].isoformat() + '_' + params['to_date'].isoformat()
            if params['from_date'] == params['to_date']:
                formatted = params['from_date'].isoformat()

            format_ = params['format']
            prefix = params['prefix']
            document_name = f'{prefix}{formatted}.{format_}'
        case _:
            format_ = params['format']
            prefix = params['prefix']
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            document_name = f'{prefix}{date_str}.{format_}'

    return document_name


def download_document(format_: str, result, params, type_: str | None = None):
    match format_:
        case 'csv':
            document_name = generate_document_name(type_, params)
            output = io.StringIO()
            dict_rows = [
                item.model_dump(mode='json') if isinstance(item, BaseModel) else item
                for item in result
            ]

            if not dict_rows:
                output.seek(0)
                return StreamingResponse(
                    output,
                    media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={document_name}'}
                )

            writer = csv.DictWriter(output, fieldnames=dict_rows[0].keys())
            writer.writeheader()
            writer.writerows(dict_rows)
            output.seek(0)

            return StreamingResponse(
                output,
                media_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename={document_name}'}
            )

        case _:
            return result


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])
