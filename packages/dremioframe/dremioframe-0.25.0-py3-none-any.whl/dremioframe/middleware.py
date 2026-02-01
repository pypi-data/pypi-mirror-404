import pyarrow.flight as flight

class CookieMiddleware(flight.ClientMiddleware):
    """
    Middleware to handle session cookies for Dremio Flight connections.
    Required for maintaining session context (like project_id) in Dremio Cloud.
    """
    def __init__(self, factory):
        self.factory = factory

    def received_headers(self, headers):
        # Capture Set-Cookie headers
        # headers is a dict-like object mapping keys to lists of values
        for key, values in headers.items():
            if key.lower() == 'set-cookie':
                for v in values:
                    # Simple parsing of cookie string
                    parts = v.split(';', 1)
                    if parts:
                        kv = parts[0].split('=', 1)
                        if len(kv) == 2:
                            self.factory.cookies[kv[0].strip()] = kv[1].strip()

    def sending_headers(self):
        # Send Cookie header if we have cookies
        if self.factory.cookies:
            cookie_string = '; '.join([f"{k}={v}" for k, v in self.factory.cookies.items()])
            return {'cookie': cookie_string}
        return {}

class CookieMiddlewareFactory(flight.ClientMiddlewareFactory):
    """Factory for CookieMiddleware"""
    def __init__(self):
        self.cookies = {}

    def start_call(self, info):
        return CookieMiddleware(self)
