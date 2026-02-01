import json
import pandas as pd
from typing import List, Dict, Any

class BaseExporter:
    def export(self, data: List[Dict[str, Any]], filename: str):
        raise NotImplementedError

class JSONExporter(BaseExporter):
    def export(self, data: List[Dict[str, Any]], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

class CSVExporter(BaseExporter):
    def export(self, data: List[Dict[str, Any]], filename: str):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)

class WebhookExporter(BaseExporter):
    def __init__(self, url: str):
        self.url = url

    def export(self, data: List[Dict[str, Any]], filename: str = None):
        import requests
        response = requests.post(self.url, json=data)
        response.raise_for_status()
        return response
