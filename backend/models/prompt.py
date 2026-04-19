# backend/models/prompt.py
import uuid
import json
from database import db
from models.prompt_tag import prompt_tags


class Prompt(db.Model):
    __tablename__ = "prompts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="TEXTO")
    subcategory = db.Column(db.String(100))
    meta = db.Column(db.Text)  # JSON as text
    image_url = db.Column(db.String(500))
    is_favorite = db.Column(db.Boolean, default=False)
    analysis_status = db.Column(db.String(20), default="PENDING")  # PENDING, COMPLETED, FAILED
    analysis_result = db.Column(db.Text)  # JSON as text
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    tags = db.relationship("Tag", secondary=prompt_tags, back_populates="prompts")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "category": self.category,
            "subcategory": self.subcategory,
            "metadata": json.loads(self.meta) if self.meta else None,
            "image_url": self.image_url,
            "is_favorite": self.is_favorite,
            "analysis_status": self.analysis_status,
            "analysis_result": json.loads(self.analysis_result) if self.analysis_result else None,
            "tags": [t.name for t in self.tags],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }