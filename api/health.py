from http.server import BaseHTTPRequestHandler

from fitkg_api_common import ROOT, handle_options, send_json
from fitkg_rag import llm_configured, llm_provider, load_dotenv


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        handle_options(self)

    def do_GET(self) -> None:
        load_dotenv()
        kg = ROOT / "outputs" / "fitkg_kg"
        send_json(
            self,
            200,
            {
                "server": "fitkg-vercel",
                "ok": True,
                "rag_index": (kg / "rag_index.json").is_file(),
                "graph": (kg / "graph.json").is_file(),
                "llm": llm_configured(),
                "llm_provider": llm_provider(),
            },
        )
