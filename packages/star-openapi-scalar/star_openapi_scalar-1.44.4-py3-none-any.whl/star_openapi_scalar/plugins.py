import os.path

from jinja2 import Template
from star_openapi.plugins import BasePlugin
from starlette.responses import HTMLResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from .templates import scalar_html_string


class RegisterPlugin(BasePlugin):
    def __init__(self):
        self.name = "scalar"
        self.display_name = "Scalar"
        self.doc_url = "/openapi.json"

    def scalar_endpoint(self, request):
        template = Template(request.app.config.get("SCALAR_HTML_STRING") or scalar_html_string)
        return HTMLResponse(
            content=template.render(
                {
                    "doc_url": self.doc_url,
                    "scalar_config": request.app.config.get("SCALAR_CONFIG")
                }
            )
        )

    def register(self, doc_url: str) -> list[Route]:
        self.doc_url = doc_url
        static_folder = os.path.join(os.path.dirname(__file__), "templates", "scalar")

        routes = [
            Route(
                f"/{self.name}",
                endpoint=self.scalar_endpoint
            ),
            Mount("/scalar", app=StaticFiles(directory=static_folder), name="static"),
        ]

        return routes
