from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import ReportRequest, ReportResponse

class ReportingService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def generate_report(self, req: ReportRequest) -> ReportResponse:
        # Mock report generation
        content = {
            "summary": f"Report generated for {req.report_type}",
            "data_points": 42,
            "insights": ["Candidate showed strong adaptability.", "Excellent technical communication."]
        }
        
        record = self.pg_repo.save_report(req.recruiter_id, req.report_type, content)
        
        self.kafka.publish_event(
            topic="recruiter.report_generated",
            key=record.id,
            payload={"report_id": record.id, "recruiter_id": req.recruiter_id}
        )
        
        return ReportResponse(
            report_id=record.id,
            report_type=record.report_type,
            content=record.content,
            created_at=record.created_at
        )
