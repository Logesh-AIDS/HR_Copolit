import logging
from typing import Dict, Any, List, Optional
from elasticsearch import Elasticsearch
from .config import settings

logger = logging.getLogger(__name__)

class ElasticSearchClient:
    """Adapter for interacting with ElasticSearch."""

    def __init__(self):
        # Allow disabling SSL verification for local single-node dev setups
        self.es = Elasticsearch(
            hosts=[settings.ELASTICSEARCH_URL],
            verify_certs=False
        )

    def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Indexes a JSON document."""
        try:
            res = self.es.index(index=index_name, id=doc_id, document=document)
            return res['result'] in ['created', 'updated']
        except Exception as e:
            logger.error(f"Failed to index document {doc_id} in {index_name}: {e}")
            return False

    def search(self, index_name: str, query: Dict[str, Any], size: int = 10) -> List[Dict[str, Any]]:
        """Executes a search query."""
        try:
            res = self.es.search(index=index_name, body=query, size=size)
            hits = res.get('hits', {}).get('hits', [])
            return [hit['_source'] for hit in hits]
        except Exception as e:
            logger.error(f"Failed to execute search on {index_name}: {e}")
            return []

    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """Deletes a document from the index."""
        try:
            res = self.es.delete(index=index_name, id=doc_id)
            return res['result'] == 'deleted'
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id} from {index_name}: {e}")
            return False

def get_search_client() -> ElasticSearchClient:
    return ElasticSearchClient()
