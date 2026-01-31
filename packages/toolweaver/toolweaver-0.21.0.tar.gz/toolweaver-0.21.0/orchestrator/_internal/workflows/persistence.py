"""
Workflow State Persistence (Phase 8.3)
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from .workflow import WorkflowContext, WorkflowTemplate

logger = logging.getLogger(__name__)


class WorkflowStateStore(ABC):
    """Abstract interface for storing workflow state"""

    @abstractmethod
    def save_state(self, workflow_id: str, context: WorkflowContext) -> None:
        """Save workflow context"""
        pass

    @abstractmethod
    def load_state(self, workflow_id: str) -> WorkflowContext | None:
        """Load workflow context"""
        pass

    @abstractmethod
    def save_template(self, workflow_id: str, template: WorkflowTemplate) -> None:
        """Save workflow template"""
        pass

    @abstractmethod
    def load_template(self, workflow_id: str) -> WorkflowTemplate | None:
        """Load workflow template"""
        pass

    @abstractmethod
    def delete_state(self, workflow_id: str) -> None:
        """Delete workflow state"""
        pass


class FileWorkflowStore(WorkflowStateStore):
    """File-based implementation of workflow state store"""

    def __init__(self, storage_dir: str | Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, workflow_id: str, suffix: str = "") -> Path:
        # Sanitize ID to prevent path traversal
        clean_id = "".join(c for c in workflow_id if c.isalnum() or c in "-_")
        return self.storage_dir / f"{clean_id}{suffix}.json"

    def save_state(self, workflow_id: str, context: WorkflowContext) -> None:
        file_path = self._get_path(workflow_id)
        try:
            data = context.to_dict()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved state for workflow '{workflow_id}' to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save state for '{workflow_id}': {e}")
            raise

    def load_state(self, workflow_id: str) -> WorkflowContext | None:
        file_path = self._get_path(workflow_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return WorkflowContext.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load state for '{workflow_id}': {e}")
            return None

    def save_template(self, workflow_id: str, template: WorkflowTemplate) -> None:
        file_path = self._get_path(workflow_id, suffix="_template")
        try:
            data = template.to_dict()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved template for workflow '{workflow_id}' to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save template for '{workflow_id}': {e}")
            raise

    def load_template(self, workflow_id: str) -> WorkflowTemplate | None:
        file_path = self._get_path(workflow_id, suffix="_template")
        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return WorkflowTemplate.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load template for '{workflow_id}': {e}")
            return None

    def delete_state(self, workflow_id: str) -> None:
        file_path = self._get_path(workflow_id)
        template_path = self._get_path(workflow_id, suffix="_template")

        for path in [file_path, template_path]:
            if path.exists():
                try:
                    path.unlink()
                    logger.info(f"Deleted {path}")
                except Exception as e:
                    logger.error(f"Failed to delete {path}: {e}")
