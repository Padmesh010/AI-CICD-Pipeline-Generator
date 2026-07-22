from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    language = Column(String(64), nullable=False, index=True)
    framework = Column(String(64), nullable=False)
    target = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    pipelines = relationship("Pipeline", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "language": self.language,
            "framework": self.framework,
            "target": self.target,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(64), nullable=False, index=True)
    yaml_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="pipelines")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "platform": self.platform,
            "yaml_content": self.yaml_content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, index=True)
    platform = Column(String(64), nullable=False, index=True)
    language = Column(String(64), nullable=False, index=True)
    framework = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    is_custom = Column(Integer, default=0, index=True)
    version = Column(String(32), default="1.0.0")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "language": self.language,
            "framework": self.framework,
            "content": self.content,
            "is_custom": self.is_custom,
            "version": self.version
        }

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    details = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action,
            "status": self.status,
            "details": self.details
        }

# Index definitions for common query combinations
Index("idx_projects_lang_fw", Project.language, Project.framework)
Index("idx_templates_platform_lang", Template.platform, Template.language)
