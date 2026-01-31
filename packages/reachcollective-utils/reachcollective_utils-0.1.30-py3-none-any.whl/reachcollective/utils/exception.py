class APIException(Exception):
    def __init__(self,  message: str|None, code: int, detail: dict = None):
        self.message = message
        self.code = code
        self.detail = detail or {}

    def get_error(self) -> str|dict:
        if self.detail:
            # Check if resposne from External API attribute (response)
            if 'response' in self.detail:
                if self.detail['response']:
                    return self.detail['response']
                else:
                    return self.message

            return self.detail

        return self.message
