from typing import List
from app.domain.models import KGNodeCreate, KGEdgeCreate
from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
import logging

logger = logging.getLogger(__name__)

class KGService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def add_node(self, node: KGNodeCreate):
        record = self.pg_repo.add_kg_node(node)
        self.kafka.publish_event(
            topic="kg.updated",
            key=record.id,
            payload={"type": "node_added", "node_id": record.id}
        )
        return record

    def add_edge(self, edge: KGEdgeCreate):
        record = self.pg_repo.add_kg_edge(edge)
        self.kafka.publish_event(
            topic="kg.updated",
            key=record.id,
            payload={"type": "edge_added", "edge_id": record.id, "source": record.source_id, "target": record.target_id}
        )
        return record

    def get_related_nodes(self, node_id: str):
        edges = self.pg_repo.get_node_edges(node_id)
        # Note: A real implementation would do a recursive CTE search here
        return [{"source_id": e.source_id, "target_id": e.target_id, "relation": e.relation_type} for e in edges]
