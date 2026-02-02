import http.server
import socketserver
import json
import threading
import os
from typing import Optional
from .backend import BaseBackend

import http.server
import socketserver
import json
import threading
import os
import base64
from typing import Optional
from dataclasses import asdict
from .backend import BaseBackend

class OrchestrationHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, backend: BaseBackend, pipelines: dict, username: str = None, password: str = None, *args, **kwargs):
        self.backend = backend
        self.pipelines = pipelines # dict of name -> Pipeline object
        self.username = username
        self.password = password
        super().__init__(*args, **kwargs)

    def _check_auth(self):
        if not self.username or not self.password:
            return True
            
        auth_header = self.headers.get("Authorization")
        if not auth_header:
            return False
            
        try:
            auth_type, encoded = auth_header.split(" ", 1)
            if auth_type.lower() != "basic":
                return False
            decoded = base64.b64decode(encoded).decode("utf-8")
            u, p = decoded.split(":", 1)
            return u == self.username and p == self.password
        except Exception:
            return False

    def _send_auth_challenge(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="DremioFrame Orchestration"')
        self.end_headers()
        self.wfile.write(b"Authentication required")

    def do_GET(self):
        if not self._check_auth():
            self._send_auth_challenge()
            return

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self._get_html().encode("utf-8"))
        elif self.path == "/api/runs":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            runs = self.backend.list_runs(limit=50)
            runs_data = [asdict(r) for r in runs]
            self.wfile.write(json.dumps(runs_data).encode("utf-8"))
        elif self.path.startswith("/api/pipelines"):
            # List pipelines
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            pipelines_list = list(self.pipelines.keys())
            self.wfile.write(json.dumps(pipelines_list).encode("utf-8"))
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        if not self._check_auth():
            self._send_auth_challenge()
            return

        if self.path.startswith("/api/pipelines/") and self.path.endswith("/trigger"):
            # /api/pipelines/{name}/trigger
            pipeline_name = self.path.split("/")[3]
            pipeline = self.pipelines.get(pipeline_name)
            
            if pipeline:
                # Trigger in a separate thread to not block UI
                threading.Thread(target=pipeline.run).start()
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "triggered", "pipeline": pipeline_name}).encode("utf-8"))
            else:
                self.send_error(404, f"Pipeline {pipeline_name} not found")
        else:
            self.send_error(404, "Endpoint not found")

    def _get_html(self):
        return """
<!DOCTYPE html>
<html>
<head>
    <title>DremioFrame Orchestration</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f9; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background-color: #3f51b5; color: white; padding: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        header h1 { margin: 0; padding-left: 20px; font-size: 24px; }
        .card { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
        th { background-color: #f8f9fa; font-weight: 600; color: #555; }
        tr:hover { background-color: #f1f1f1; }
        .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .SUCCESS { background-color: #e8f5e9; color: #2e7d32; }
        .FAILED { background-color: #ffebee; color: #c62828; }
        .RUNNING { background-color: #e3f2fd; color: #1565c0; }
        .PENDING { background-color: #fff3e0; color: #ef6c00; }
        .SKIPPED { background-color: #f5f5f5; color: #757575; }
        button { background-color: #3f51b5; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; transition: background 0.3s; }
        button:hover { background-color: #303f9f; }
        button:disabled { background-color: #ccc; cursor: not-allowed; }
        .controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .refresh-toggle { display: flex; align-items: center; gap: 10px; }
    </style>
</head>
<body>
    <div id="app">
        <header>
            <div class="container">
                <h1>DremioFrame Orchestration</h1>
            </div>
        </header>
        
        <div class="container">
            <div class="card">
                <h2>Pipelines</h2>
                <div class="controls">
                    <div>
                        <span v-for="p in pipelines" :key="p" style="margin-right: 10px;">
                            <strong>{{ p }}</strong>
                            <button @click="triggerPipeline(p)" style="margin-left: 5px;">Run Now</button>
                        </span>
                    </div>
                    <div class="refresh-toggle">
                        <label>
                            <input type="checkbox" v-model="autoRefresh"> Auto-refresh (5s)
                        </label>
                        <button @click="fetchRuns">Refresh</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Recent Runs</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Pipeline</th>
                            <th>Run ID</th>
                            <th>Start Time</th>
                            <th>Duration</th>
                            <th>Status</th>
                            <th>Tasks</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="run in runs" :key="run.run_id">
                            <td>{{ run.pipeline_name }}</td>
                            <td><small>{{ run.run_id.substring(0, 8) }}...</small></td>
                            <td>{{ formatDate(run.start_time) }}</td>
                            <td>{{ formatDuration(run.start_time, run.end_time) }}</td>
                            <td><span :class="['status-badge', run.status]">{{ run.status }}</span></td>
                            <td>
                                <div v-for="(status, name) in run.tasks" :key="name" style="margin-bottom: 2px;">
                                    <span :class="['status-badge', status]" style="font-size: 10px;">{{ name }}</span>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const { createApp, ref, onMounted, watch } = Vue;

        createApp({
            setup() {
                const runs = ref([]);
                const pipelines = ref([]);
                const autoRefresh = ref(true);
                let intervalId = null;

                const fetchRuns = async () => {
                    try {
                        const res = await fetch('/api/runs');
                        runs.value = await res.json();
                    } catch (e) {
                        console.error(e);
                    }
                };

                const fetchPipelines = async () => {
                    try {
                        const res = await fetch('/api/pipelines');
                        pipelines.value = await res.json();
                    } catch (e) {
                        console.error(e);
                    }
                };

                const triggerPipeline = async (name) => {
                    if (!confirm(`Run pipeline ${name}?`)) return;
                    try {
                        await fetch(`/api/pipelines/${name}/trigger`, { method: 'POST' });
                        setTimeout(fetchRuns, 500); // Quick refresh
                    } catch (e) {
                        alert('Failed to trigger pipeline');
                    }
                };

                const formatDate = (ts) => {
                    return new Date(ts * 1000).toLocaleString();
                };

                const formatDuration = (start, end) => {
                    if (!end) return 'Running...';
                    const diff = end - start;
                    return diff.toFixed(2) + 's';
                };

                onMounted(() => {
                    fetchPipelines();
                    fetchRuns();
                    startInterval();
                });

                const startInterval = () => {
                    if (intervalId) clearInterval(intervalId);
                    intervalId = setInterval(() => {
                        if (autoRefresh.value) fetchRuns();
                    }, 5000);
                };

                watch(autoRefresh, (newVal) => {
                    if (newVal) startInterval();
                    else clearInterval(intervalId);
                });

                return {
                    runs,
                    pipelines,
                    autoRefresh,
                    fetchRuns,
                    triggerPipeline,
                    formatDate,
                    formatDuration
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
        """

def start_ui(backend: BaseBackend, pipelines: dict = None, port: int = 8080, username: str = None, password: str = None):
    """
    Starts the Orchestration UI server.
    
    Args:
        backend: The backend to read history from.
        pipelines: A dict of {name: PipelineObject} to allow manual triggering.
        port: Port to serve on.
        username: Optional username for Basic Auth.
        password: Optional password for Basic Auth.
    """
    from dataclasses import asdict # Import here to ensure availability
    
    # Factory to pass backend and pipelines to handler
    def handler_factory(*args, **kwargs):
        return OrchestrationHandler(backend, pipelines or {}, username, password, *args, **kwargs)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler_factory) as httpd:
        print(f"Serving UI at http://localhost:{port}")
        if username and password:
            print("Basic Authentication enabled.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping UI server.")
            httpd.server_close()
