try:
    from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
    from IPython.core.display import display, HTML
except ImportError:
    # Mock for non-IPython environments
    class Magics: pass
    def magics_class(cls): return cls
    def line_magic(func): return func
    def cell_magic(func): return func
    def line_cell_magic(func): return func

from dremioframe.client import DremioClient
from dremioframe.builder import DremioBuilder
import os

@magics_class
class DremioMagics(Magics):
    """
    Magics for DremioFrame.
    
    %dremio_connect: Connect to Dremio
    %%dremio_sql: Execute SQL query
    """
    
    def __init__(self, shell):
        super(DremioMagics, self).__init__(shell)
        self.client = None

    @line_magic
    def dremio_connect(self, line):
        """
        Connect to Dremio using environment variables or arguments.
        Usage: %dremio_connect [pat=...] [project_id=...]
        """
        args = line.split()
        kwargs = {}
        for arg in args:
            if '=' in arg:
                k, v = arg.split('=', 1)
                kwargs[k] = v
        
        try:
            self.client = DremioClient(**kwargs)
            print(f"Connected to Dremio: {self.client.base_url}")
            # Inject client into user namespace
            self.shell.user_ns['dremio_client'] = self.client
        except Exception as e:
            print(f"Connection failed: {e}")

    @cell_magic
    def dremio_sql(self, line, cell):
        """
        Execute SQL query against Dremio.
        Usage: 
        %%dremio_sql [variable_name]
        SELECT * FROM ...
        """
        if self.client is None:
            # Try to find client in user namespace
            if 'dremio_client' in self.shell.user_ns:
                self.client = self.shell.user_ns['dremio_client']
            else:
                # Try to initialize from env
                try:
                    self.client = DremioClient()
                except:
                    print("Please connect first using %dremio_connect or define dremio_client")
                    return

        variable_name = line.strip()
        sql = cell.strip()
        
        try:
            builder = DremioBuilder(self.client, sql=sql)
            # Default to pandas for display
            df = builder.collect(library='pandas', progress_bar=True)
            
            if variable_name:
                self.shell.user_ns[variable_name] = df
                print(f"Result saved to {variable_name}")
            
            return df
        except Exception as e:
            print(f"Query failed: {e}")

def load_ipython_extension(ipython):
    """
    Register the magics with IPython.
    """
    ipython.register_magics(DremioMagics)
    print("DremioFrame magics loaded: %dremio_connect, %%dremio_sql")
