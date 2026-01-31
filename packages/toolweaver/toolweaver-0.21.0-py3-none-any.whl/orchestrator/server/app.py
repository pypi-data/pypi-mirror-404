"""
Skills Dashboard API - Exposes Phase 2 infrastructure through REST endpoints
Provides access to: Skills, Metrics, Collections, Marketplace

Phase 4.3 Observability Features:
- ExecutionContext tracking for all requests
- Request ID correlation and session tracking
- Automatic timing middleware and metrics collection
- Optional PII redaction in responses
- JSONL sink logging to STATISTICS/observability.jsonl
- API Key Authentication (X-API-Key header)
- Audit logging of all requests
- Rate limiting and input validation
"""

import time
import uuid
from datetime import datetime
from typing import Any

from flask import Flask, Response, g, jsonify, request
from flask_cors import CORS

from orchestrator.context import ExecutionContext, clear_context, get_context, set_context
from orchestrator.observability import get_observability, log_execution
from orchestrator.skills import (
    SkillRegistry,
    list_skills,
    load_skill,
)
from orchestrator.skills.discovery import QDRANT_AVAILABLE, SemanticSkillDiscovery
from orchestrator.skills.skill_collections import CollectionManager
from orchestrator.skills.skill_executor import get_executor
from orchestrator.skills.skill_memory import SkillMemory
from orchestrator.skills.skill_state import SkillState

# Import authentication and validation middleware
from .auth import require_api_key
from .rate_limit import rate_limit
from .response import init_app as init_response_envelope
from .validation import validate_input

app = Flask(__name__)
CORS(app)

# Initialize response envelope (request IDs, timing, error handlers)
init_response_envelope(app)

# Observability backends
_observability = get_observability()


@app.before_request
def _setup_execution_context() -> None:
    """Create ExecutionContext for each request with session tracking."""
    try:
        # Extract user info from headers (API key auth provides this)
        user_id = request.headers.get("X-User-ID")
        organization_id = request.headers.get("X-Organization-ID")

        # Generate request tracking IDs
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        session_id = request.headers.get("X-Session-ID")

        # Get or create context from global state
        parent_context = get_context()
        if parent_context and session_id and session_id == parent_context.session_id:
            # Use existing session but create new request context
            ctx = parent_context.create_child_context()
            ctx.request_id = request_id
        else:
            # Create new context
            ctx = ExecutionContext(
                session_id=session_id or str(uuid.uuid4()),
                request_id=request_id,
                user_id=user_id,
                organization_id=organization_id,
                task_description=f"{request.method} {request.path}",
                parent_request_id=None,
            )

        # Store in Flask g for access in route handlers
        g.execution_context = ctx
        g.request_start_time = time.time()
        g.request_id = request_id

        # Set as global context for nested calls
        set_context(ctx)

        # Mark as started
        if ctx.status == "pending":
            ctx.mark_started()

    except Exception as e:
        # Never block request due to observability
        import logging

        logging.getLogger(__name__).error(f"Error setting up ExecutionContext: {e}")
        # Create minimal context to continue
        g.execution_context = ExecutionContext(task_description=f"{request.method} {request.path}")
        g.request_start_time = time.time()


@app.after_request
def _finalize_execution_context(response: Response) -> Response:
    """Finalize ExecutionContext and log to observability."""
    try:
        ctx = getattr(g, "execution_context", None)
        if ctx is None:
            return response

        # Calculate duration
        start_time = getattr(g, "request_start_time", None)
        if start_time:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            ctx.metadata["request_duration_ms"] = duration_ms

        # Record response details
        ctx.metadata["http_status_code"] = response.status_code
        ctx.metadata["http_method"] = request.method
        ctx.metadata["http_path"] = request.path

        # Mark context as completed (unless already marked failed)
        if ctx.status == "running":
            if 400 <= response.status_code < 600:
                ctx.mark_failed(f"HTTP {response.status_code}: {response.status_code}")
            else:
                ctx.mark_completed(result={"http_status": response.status_code})

        # Log to observability backends
        log_execution(ctx)

    except Exception as e:
        # Never break response due to observability
        import logging

        logging.getLogger(__name__).error(f"Error finalizing ExecutionContext: {e}")
    finally:
        # Clear context from Flask g
        try:
            clear_context()
        except Exception:
            pass

    return response


# Initialize core services with graceful degradation (Redis optional)
registry = SkillRegistry()


def _safe_init_memory() -> SkillMemory | None:
    try:
        return SkillMemory(connect_timeout=0.2)
    except Exception as exc:
        print(f"Warning: SkillMemory unavailable (Redis?): {exc}")
        return None


def _safe_init_state() -> SkillState | None:
    try:
        return SkillState(connect_timeout=0.2)
    except Exception as exc:
        print(f"Warning: SkillState unavailable (Redis?): {exc}")
        return None


def _safe_init_semantic_search() -> SemanticSkillDiscovery | None:
    """Initialize semantic search with Qdrant."""
    if not QDRANT_AVAILABLE:
        print("Warning: Qdrant not available - semantic search disabled")
        return None

    try:
        import os

        from qdrant_client import QdrantClient

        # Get Qdrant config from env
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            print("Warning: QDRANT_URL not configured - semantic search disabled")
            return None

        # Connect to Qdrant
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=2)
        client.get_collections()  # Test connection

        discovery = SemanticSkillDiscovery(qdrant_client=client)

        # Skip startup indexing to avoid HuggingFace network timeouts
        # Skills will be indexed on first search request (lazy loading)
        # Model is already cached locally (~80MB in ~/.cache/huggingface/)

        print("✓ Semantic search ready (lazy indexing on first search)")
        return discovery
    except Exception as exc:
        print(f"Warning: Semantic search unavailable: {exc}")
        return None


memory = _safe_init_memory()
state = _safe_init_state()
collections = CollectionManager()
discovery = _safe_init_semantic_search()


# =============================================================================
# SKILLS ENDPOINTS
# =============================================================================


@app.route("/api/skills", methods=["GET"])
@rate_limit
def get_all_skills() -> tuple[Response, int]:
    """Get all discoverable skills from registry (rate limited)"""
    try:
        skills = list_skills()
        # Return a simple list of skill descriptors for tests
        skill_items: list[dict[str, Any]] = []
        for name in skills:
            meta = registry.get_skill_metadata(name)
            if meta:
                skill_items.append(
                    {
                        "id": meta.name,
                        "name": meta.name,
                        "description": meta.description,
                    }
                )
            else:
                skill_items.append({"id": name, "name": name})

        return jsonify(skill_items), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/skills/<skill_id>", methods=["GET"])
@rate_limit
def get_skill_details(skill_id: str) -> tuple[Response, int]:
    """Get detailed information about a specific skill"""
    try:
        # Get metadata first to check if skill exists
        skill_meta = registry.get_skill_metadata(skill_id)

        # Return 404 if skill does not exist
        if skill_meta is None:
            return jsonify({"success": False, "error": f"Skill {skill_id} not found"}), 404

        # Load skill only if it exists (optional)
        _ = load_skill(skill_id)

        # Keep response minimal for tests
        metrics = memory.get_skill_metrics(skill_id) if memory else {}
        return jsonify(
            {
                "id": skill_id,
                "name": skill_meta.name,
                "version": skill_meta.version,
                "metrics": metrics,
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404


@app.route("/api/skills/<skill_id>/execute", methods=["POST"])
@rate_limit
@require_api_key
@validate_input("execute_skill")
def execute_skill(skill_id: str) -> tuple[Response, int]:
    """Execute a skill capability (rate limited, requires API key, validated input)"""
    try:
        data = request.json
        capability = data.get("capability") if data else None
        parameters = data.get("parameters", {}) if data else {}

        if not capability:
            return jsonify({"success": False, "error": "capability required"}), 400

        # Get skill metadata to validate it exists
        skill_meta = registry.get_skill_metadata(skill_id)
        if not skill_meta:
            return jsonify({"success": False, "error": f"Skill {skill_id} not found"}), 404

        # Validate capability exists in metadata
        capability_found = None
        for cap in skill_meta.capabilities:
            if cap.name == capability:
                capability_found = cap
                break

        if not capability_found:
            return jsonify(
                {
                    "success": False,
                    "error": f"Capability {capability} not found in skill {skill_id}",
                }
            ), 400

        # Execute the skill using the executor
        executor = get_executor()
        result = executor.execute(skill_id, capability, parameters)

        if result.success:
            return jsonify(
                {
                    "success": True,
                    "execution_id": result.execution_id,
                    "skill_id": result.skill_id,
                    "capability": result.capability,
                    "result": result.result,
                    "duration_ms": result.duration_ms,
                    "timestamp": result.timestamp,
                }
            ), 200
        else:
            return jsonify(
                {
                    "success": False,
                    "execution_id": result.execution_id,
                    "skill_id": result.skill_id,
                    "capability": result.capability,
                    "error": result.error,
                    "timestamp": result.timestamp,
                }
            ), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# SEMANTIC SEARCH ENDPOINTS
# =============================================================================


@rate_limit
@app.route("/api/search", methods=["GET", "POST"])
def api_search() -> tuple[Response, int]:
    """Semantic search for skills (fallback to text search if semantic fails)"""
    try:
        if request.method == "POST":
            data = request.json
            query = data.get("query") or data.get("q") if data else None
        else:
            query = request.args.get("query") or request.args.get("q")

        if not query:
            return jsonify({"success": False, "error": "query parameter required"}), 400

        # Try semantic search first, fallback to text search
        try:
            if discovery and discovery.enabled:
                results = discovery.search(query, limit=10)
                results_data = [r.to_dict() if hasattr(r, "to_dict") else r for r in results]
            else:
                raise ValueError("Semantic search not available")
        except Exception as semantic_error:
            # Fallback to text search on any semantic search failure
            print(f"Semantic search failed ({semantic_error}), using text search")
            results = registry.search(query, limit=10)
            results_data = [r.to_dict() if hasattr(r, "to_dict") else r for r in results]

        return jsonify(results_data), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@rate_limit
@app.route("/api/search/capabilities", methods=["GET", "POST"])
def search_by_capability() -> tuple[Response, int]:
    """Search for skills by capability (what you want to do)"""
    try:
        if request.method == "POST":
            data = request.json
            capability_query = data.get("capability") if data else None
        else:
            capability_query = request.args.get("capability")

        if not capability_query:
            return jsonify({"success": False, "error": "capability parameter required"}), 400

        if discovery:
            results = discovery.search_by_capability(capability_query, limit=10)
            results_data = [r.to_dict() if hasattr(r, "to_dict") else r for r in results]
            backend = "semantic"
        else:
            # Fallback to text search
            results = registry.search(capability_query, limit=10)
            results_data = [r.to_dict() if hasattr(r, "to_dict") else r for r in results]
            backend = "text"

        return jsonify(
            {
                "success": True,
                "capability": capability_query,
                "backend": backend,
                "count": len(results_data),
                "results": results_data,
                "timestamp": datetime.now().isoformat(),
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# METRICS ENDPOINTS
# =============================================================================


@rate_limit
@app.route("/api/metrics", methods=["GET"])
def get_metrics() -> tuple[Response, int]:
    """Get system-wide metrics"""
    try:
        if not memory:
            return jsonify([]), 200

        all_skills = list_skills()
        metrics_list: list[dict[str, Any]] = []
        for skill_id in all_skills:
            try:
                metrics = memory.get_skill_metrics(skill_id) or {}
                metrics_list.append({"skill_id": skill_id, **metrics})
            except Exception:
                metrics_list.append({"skill_id": skill_id, "metrics": {}, "error": "unavailable"})

        return jsonify(metrics_list), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/metrics/<skill_id>", methods=["GET"])
@rate_limit
def get_skill_metrics(skill_id: str) -> tuple[Response, int]:
    """Get metrics for a specific skill"""
    if not memory:
        return jsonify([]), 200
    try:
        metrics = memory.get_skill_metrics(skill_id)
        return jsonify(metrics or {}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404


@rate_limit
@app.route("/api/metrics/<skill_id>/history", methods=["GET"])
def get_metrics_history(skill_id: str) -> tuple[Response, int]:
    """Get metric history for a skill"""
    if not memory:
        return jsonify([]), 200
    try:
        limit = request.args.get("limit", 100, type=int)
        history = memory.get_metrics_history(skill_id, limit=limit)
        return jsonify(history or []), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404


# =============================================================================
# COLLECTIONS ENDPOINTS
# =============================================================================


@rate_limit
@app.route("/api/collections", methods=["GET"])
def list_collections() -> tuple[Response, int]:
    """List all skill collections"""
    try:
        colls = collections.list_collections()
        # Add id field to each collection (use name as id)
        result: list[dict[str, Any]] = []
        for coll in colls or []:
            coll_dict = coll.to_dict() if hasattr(coll, "to_dict") else vars(coll)
            coll_dict["id"] = coll.name
            result.append(coll_dict)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@rate_limit
@app.route("/api/collections/<collection_id>", methods=["GET"])
def get_collection(collection_id: str) -> tuple[Response, int]:
    """Get details of a collection"""
    try:
        coll = collections.get_collection(collection_id)
        if not coll:
            return jsonify(
                {"success": False, "error": f"Collection {collection_id} not found"}
            ), 404

        # Convert to plain dict for safe JSON serialization
        coll_dict = coll.to_dict() if hasattr(coll, "to_dict") else vars(coll)

        skills_in_coll = collections.get_collection_skills(collection_id)

        return jsonify(
            {
                "success": True,
                "id": collection_id,
                "collection": coll_dict,
                "skills": skills_in_coll,
                "skill_count": len(skills_in_coll),
                "timestamp": datetime.now().isoformat(),
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404


@app.route("/api/collections", methods=["POST"])
@rate_limit
@require_api_key
@validate_input("create_collection")
def create_collection() -> tuple[Response, int]:
    """Create a new collection (rate limited, requires API key, validated input)"""
    try:
        data = request.json
        name = data.get("name") if data else None
        description = data.get("description", "") if data else ""

        if not name:
            return jsonify({"success": False, "error": "name required"}), 400

        coll_id = collections.create_collection(name, description)

        return jsonify(
            {"success": True, "id": coll_id, "name": name, "timestamp": datetime.now().isoformat()}
        ), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/collections/<collection_id>/skills/<skill_id>", methods=["POST"])
@rate_limit
@require_api_key
def add_skill_to_collection(collection_id: str, skill_id: str) -> tuple[Response, int]:
    """Add a skill to a collection (rate limited, requires API key)"""
    try:
        collections.add_skill_to_collection(collection_id, skill_id)

        return jsonify(
            {
                "success": True,
                "collection_id": collection_id,
                "skill_id": skill_id,
                "timestamp": datetime.now().isoformat(),
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# MARKETPLACE ENDPOINTS
# =============================================================================


@rate_limit
@app.route("/api/marketplace", methods=["GET"])
def list_marketplace_skills() -> tuple[Response, int]:
    """List all skills with marketplace information"""
    try:
        all_skills = list_skills()
        marketplace_info: list[dict[str, Any]] = []

        for skill_id in all_skills:
            try:
                metrics = memory.get_skill_metrics(skill_id) if memory else {}
                marketplace_info.append(
                    {
                        "id": skill_id,
                        "downloads": metrics.get("usage_count", 0) if metrics else 0,
                        "rating": metrics.get("avg_rating", 0) if metrics else 0,
                    }
                )
            except Exception:
                marketplace_info.append({"id": skill_id, "downloads": 0, "rating": 0})

        return jsonify(marketplace_info), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/marketplace/<skill_id>/download", methods=["POST"])
@rate_limit
@require_api_key
def download_skill(skill_id: str) -> tuple[Response, int]:
    """Record skill download (rate limited, requires API key)"""
    try:
        # Record metric if backend available, otherwise skip gracefully
        if memory:
            memory.record_skill_download(skill_id)

        return jsonify(
            {
                "success": True,
                "skill_id": skill_id,
                "message": (
                    "Download recorded"
                    if memory
                    else "Download recorded (metrics unavailable)"
                ),
                "timestamp": datetime.now().isoformat(),
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/marketplace/<skill_id>/rate", methods=["POST"])
@rate_limit
@require_api_key
@validate_input("rate_skill")
def rate_skill(skill_id: str) -> tuple[Response, int]:
    """Rate a skill (1-5) (rate limited, requires API key, validated input)"""
    try:
        data = request.json
        rating = data.get("rating") if data else None

        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"success": False, "error": "rating must be 1-5"}), 400

        # Record metric if backend available, otherwise skip gracefully
        if memory:
            memory.record_skill_rating(skill_id, rating)

        return jsonify(
            {
                "success": True,
                "skill_id": skill_id,
                "rating": rating,
                "message": (
                    "Rating recorded"
                    if memory
                    else "Rating recorded (metrics unavailable)"
                ),
                "timestamp": datetime.now().isoformat(),
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================

# =============================================================================
# SYSTEM ENDPOINTS
# =============================================================================


@rate_limit
@app.route("/api/health", methods=["GET"])
def health_check() -> tuple[Response, int]:
    """Health check endpoint"""
    try:
        # Test core services
        skills_count = len(list_skills())
        memory_ok = memory is not None
        state_ok = state is not None

        return jsonify(
            {
                "success": True,
                "status": "healthy",
                "skills_discoverable": skills_count,
                "metrics_backend": "available" if memory_ok else "unavailable",
                "state_backend": "available" if state_ok else "unavailable",
                "timestamp": datetime.now().isoformat(),
            }
        ), 200
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ), 500


@rate_limit
@app.route("/api/system/info", methods=["GET"])
def system_info() -> tuple[Response, int]:
    """Get system information"""
    try:
        all_skills = list_skills()
        return jsonify(
            {
                "version": "1.0",
                "skills_count": len(all_skills),
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================


@app.errorhandler(404)
def not_found(error: Any) -> tuple[Response, int]:
    return jsonify({"success": False, "error": "endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error: Any) -> tuple[Response, int]:
    return jsonify({"success": False, "error": "internal server error"}), 500


if __name__ == "__main__":
    print("=" * 80)
    print("Skills Dashboard API - Phase 3.2")
    print("=" * 80)
    print("\nAPI Endpoints:")
    print("  Skills:       GET  /api/skills")
    print("                GET  /api/skills/<id>")
    print("                POST /api/skills/<id>/execute")
    print("\n  Metrics:      GET  /api/metrics")
    print("                GET  /api/metrics/<id>")
    print("                GET  /api/metrics/<id>/history")
    print("\n  Collections:  GET  /api/collections")
    print("                GET  /api/collections/<id>")
    print("                POST /api/collections")
    print("                POST /api/collections/<id>/skills/<skill_id>")
    print("\n  Marketplace:  GET  /api/marketplace")
    print("                POST /api/marketplace/<id>/download")
    print("                POST /api/marketplace/<id>/rate")
    print("\n  Search:       GET  /api/search?q=<query>")
    print("\n  System:       GET  /api/health")
    print("                GET  /api/system/info")
    print("\n" + "=" * 80)
    print("Starting server on http://localhost:5000")
    print("=" * 80 + "\n")

    app.run(debug=True, host="0.0.0.0", port=5000)
