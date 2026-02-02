from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from jinja2 import Template
from anti_sentinel.services.metrics import MetricsService

router = APIRouter()

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sentinel Dashboard</title>
    <style>
        body { font-family: sans-serif; padding: 2rem; background: #f4f4f9; }
        .card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85em; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>🛡️ Sentinel Dashboard</h1>
    
    <div class="card">
        <h2>App Health</h2>
        <p><strong>Average Latency:</strong> {{ stats.avg_latency }} ms</p>
    </div>

    <div style="margin-bottom: 20px;">
    <a href="/docs" target="_blank" class="badge">Swagger API</a>
    <a href="/framework-docs/" target="_blank" class="badge success">📖 Read the Docs</a>
    </div>

    <div class="card">
        <h2>Recent Activity</h2>
        <table>
            <thead>
                <tr>
                    <th>Method</th>
                    <th>Endpoint</th>
                    <th>Status</th>
                    <th>Latency (ms)</th>
                </tr>
            </thead>
            <tbody>
                {% for req in stats.recent_requests %}
                <tr>
                    <td><b>{{ req.method }}</b></td>
                    <td>{{ req.endpoint }}</td>
                    <td>
                        <span class="badge {{ 'success' if req.status_code == 200 else 'error' }}">
                            {{ req.status_code }}
                        </span>
                    </td>
                    <td>{{ "%.2f"|format(req.latency_ms) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

@router.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard():
    metrics = MetricsService.get_instance()
    stats = await metrics.get_stats()
    
    template = Template(DASHBOARD_TEMPLATE)
    return template.render(stats=stats)