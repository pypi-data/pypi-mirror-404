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
        from http.cookies import SimpleCookie
        
        for key, values in headers.items():
            if key.lower() == 'set-cookie':
                for value in values:
                    # value looks like "key=value; Path=/; ..."
                    # We use SimpleCookie to parse it easily like dremio-simple-query
                    try:
                        cookie = SimpleCookie()
                        cookie.load(value)
                        for name, morsel in cookie.items():
                            self.factory.cookies[name] = morsel.value
                    except Exception:
                        pass # Silently fail on cookie parsing

    def sending_headers(self):
        # Send Cookie header if we have cookies
        if self.factory.cookies:
            cookie_string = '; '.join([f"{k}={v}" for k, v in self.factory.cookies.items()])
            return {'Cookie': cookie_string} # Capitalized 'Cookie' to match standard
        return {}

class CookieMiddlewareFactory(flight.ClientMiddlewareFactory):
    """Factory for CookieMiddleware"""
    def __init__(self):
        self.cookies = {}

    def start_call(self, info):
        return CookieMiddleware(self)
