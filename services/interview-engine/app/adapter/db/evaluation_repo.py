# services/interview-engine/app/adapter/db/evaluation_repo.py
import logging
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class EvaluationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_evaluation(
        self,
        session_id: str,
        question_id: str,
        candidate_answer: str,
        overall_score: float
    ) -> orm.AnswerEvaluationORM:
        ev = orm.AnswerEvaluationORM(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            question_id=uuid.UUID(question_id),
            candidate_answer=candidate_answer,
            overall_score=overall_score
        )
        self.db.add(ev)
        self.db.flush()
        return ev

    def get_evaluation(self, eval_id: str) -> Optional[orm.AnswerEvaluationORM]:
        try:
            ev_uuid = uuid.UUID(eval_id)
            return self.db.query(orm.AnswerEvaluationORM).filter(orm.AnswerEvaluationORM.id == ev_uuid).first()
        except ValueError:
            return None

    def get_evaluation_by_session_question(self, session_id: str, question_id: str) -> Optional[orm.AnswerEvaluationORM]:
        try:
            sess_uuid = uuid.UUID(session_id)
            q_uuid = uuid.UUID(question_id)
            return self.db.query(orm.AnswerEvaluationORM).filter(
                orm.AnswerEvaluationORM.session_id == sess_uuid,
                orm.AnswerEvaluationORM.question_id == q_uuid
            ).first()
        except ValueError:
            return None

    def save_rubric(
        self,
        evaluation_id: str,
        accuracy_score: float,
        completeness_score: float,
        depth_score: float,
        clarity_score: float,
        accuracy_feedback: str,
        completeness_feedback: str,
        depth_feedback: str,
        clarity_feedback: str
    ) -> orm.EvaluationRubricORM:
        ev_uuid = uuid.UUID(evaluation_id)
        
        # Upsert
        rub = self.db.query(orm.EvaluationRubricORM).filter(orm.EvaluationRubricORM.evaluation_id == ev_uuid).first()
        if not rub:
            rub = orm.EvaluationRubricORM(id=uuid.uuid4(), evaluation_id=ev_uuid)
            self.db.add(rub)
            
        rub.accuracy_score = accuracy_score
        rub.completeness_score = completeness_score
        rub.depth_score = depth_score
        rub.clarity_score = clarity_score
        rub.accuracy_feedback = accuracy_feedback
        rub.completeness_feedback = completeness_feedback
        rub.depth_feedback = depth_feedback
        rub.clarity_feedback = clarity_feedback
        
        self.db.flush()
        return rub

    def get_rubric(self, evaluation_id: str) -> Optional[orm.EvaluationRubricORM]:
        try:
            ev_uuid = uuid.UUID(evaluation_id)
            return self.db.query(orm.EvaluationRubricORM).filter(orm.EvaluationRubricORM.evaluation_id == ev_uuid).first()
        except ValueError:
            return None

    def save_concept_coverage(
        self,
        evaluation_id: str,
        concept_name: str,
        coverage_status: str,
        relevance_score: float
    ) -> orm.ConceptCoverageORM:
        ev_uuid = uuid.UUID(evaluation_id)
        cc = orm.ConceptCoverageORM(
            id=uuid.uuid4(),
            evaluation_id=ev_uuid,
            concept_name=concept_name,
            coverage_status=coverage_status,
            relevance_score=relevance_score
        )
        self.db.add(cc)
        self.db.flush()
        return cc

    def get_concept_coverage(self, evaluation_id: str) -> List[orm.ConceptCoverageORM]:
        try:
            ev_uuid = uuid.UUID(evaluation_id)
            return self.db.query(orm.ConceptCoverageORM).filter(orm.ConceptCoverageORM.evaluation_id == ev_uuid).all()
        except ValueError:
            return []

    def save_reasoning_metrics(
        self,
        evaluation_id: str,
        logical_flow_score: float,
        decomposition_score: float,
        tradeoff_discussion_score: float,
        explanation: str
    ) -> orm.ReasoningMetricORM:
        ev_uuid = uuid.UUID(evaluation_id)
        
        rm = self.db.query(orm.ReasoningMetricORM).filter(orm.ReasoningMetricORM.evaluation_id == ev_uuid).first()
        if not rm:
            rm = orm.ReasoningMetricORM(id=uuid.uuid4(), evaluation_id=ev_uuid)
            self.db.add(rm)
            
        rm.logical_flow_score = logical_flow_score
        rm.decomposition_score = decomposition_score
        rm.tradeoff_discussion_score = tradeoff_discussion_score
        rm.explanation = explanation
        
        self.db.flush()
        return rm

    def get_reasoning_metrics(self, evaluation_id: str) -> Optional[orm.ReasoningMetricORM]:
        try:
            ev_uuid = uuid.UUID(evaluation_id)
            return self.db.query(orm.ReasoningMetricORM).filter(orm.ReasoningMetricORM.evaluation_id == ev_uuid).first()
        except ValueError:
            return None

    def save_similarity_score(
        self,
        evaluation_id: str,
        embedding_model: str,
        cosine_similarity: float
    ) -> orm.SimilarityScoreORM:
        ev_uuid = uuid.UUID(evaluation_id)
        
        sim = self.db.query(orm.SimilarityScoreORM).filter(orm.SimilarityScoreORM.evaluation_id == ev_uuid).first()
        if not sim:
            sim = orm.SimilarityScoreORM(id=uuid.uuid4(), evaluation_id=ev_uuid)
            self.db.add(sim)
            
        sim.embedding_model = embedding_model
        sim.cosine_similarity = cosine_similarity
        
        self.db.flush()
        return sim

    def get_similarity_score(self, evaluation_id: str) -> Optional[orm.SimilarityScoreORM]:
        try:
            ev_uuid = uuid.UUID(evaluation_id)
            return self.db.query(orm.SimilarityScoreORM).filter(orm.SimilarityScoreORM.evaluation_id == ev_uuid).first()
        except ValueError:
            return None

    def save_feedback(
        self,
        evaluation_id: str,
        strengths: str,
        weaknesses: str,
        improvements: str,
        learning_topics: str
    ) -> orm.EvaluationFeedbackORM:
        ev_uuid = uuid.UUID(evaluation_id)
        
        fb = self.db.query(orm.EvaluationFeedbackORM).filter(orm.EvaluationFeedbackORM.evaluation_id == ev_uuid).first()
        if not fb:
            fb = orm.EvaluationFeedbackORM(id=uuid.uuid4(), evaluation_id=ev_uuid)
            self.db.add(fb)
            
        fb.strengths = strengths
        fb.weaknesses = weaknesses
        fb.improvements = improvements
        fb.learning_topics = learning_topics
        
        self.db.flush()
        return fb

    def get_feedback(self, evaluation_id: str) -> Optional[orm.EvaluationFeedbackORM]:
        try:
            ev_uuid = uuid.UUID(evaluation_id)
            return self.db.query(orm.EvaluationFeedbackORM).filter(orm.EvaluationFeedbackORM.evaluation_id == ev_uuid).first()
        except ValueError:
            return None

    def log_score_change(
        self,
        evaluation_id: str,
        updated_score: float,
        changer_role: str,
        reason: str
    ) -> orm.ScoreHistoryORM:
        sh = orm.ScoreHistoryORM(
            id=uuid.uuid4(),
            evaluation_id=uuid.UUID(evaluation_id),
            updated_score=updated_score,
            changer_role=changer_role,
            reason=reason
        )
        self.db.add(sh)
        self.db.flush()
        return sh

    def get_score_history(self, evaluation_id: str) -> List[orm.ScoreHistoryORM]:
        try:
            ev_uuid = uuid.UUID(evaluation_id)
            return self.db.query(orm.ScoreHistoryORM).filter(
                orm.ScoreHistoryORM.evaluation_id == ev_uuid
            ).order_by(orm.ScoreHistoryORM.created_at.asc()).all()
        except ValueError:
            return []

    def commit(self):
        self.db.commit()
