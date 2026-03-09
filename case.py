"""
START_RESEARCH relay case.

Triggered when user intent is to research (find papers, gather info from web).
Runs ResearchAgent, chunks content, saves to brain_content_chunks, ingests into Brain G.
"""
from __future__ import annotations

from typing import Any, Dict

from qbrain.core.managers_context import get_orchestrator


def handle_start_research(data: Dict[str, Any], auth: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle START_RESEARCH: run deep research, chunk content, save to DB, ingest into Brain G.
    """
    print("handle_start_research...")
    user_id = (auth or {}).get("user_id", "")
    session_id = (auth or {}).get("session_id", "")
    prompt = (data or {}).get("prompt") or (data or {}).get("msg") or ""

    if not prompt:
        print("handle_start_research... done")
        return {
            "type": "START_RESEARCH",
            "status": {"state": "error", "code": 400, "msg": "prompt required"},
            "data": {"error": "prompt or msg required"},
        }

    orch = get_orchestrator()
    if not orch:
        print("handle_start_research... done")
        return {
            "type": "START_RESEARCH",
            "status": {"state": "error", "code": 500, "msg": "orchestrator not available"},
            "data": {"error": "orchestrator not available"},
        }

    try:
        result = orch.research_agent.start_research_for_session(
            user_id=user_id,
            session_id=session_id or f"research_{user_id}",
            prompt=prompt,
        )
        urls = result.get("urls") or []
        contents = result.get("contents") or []
        module_id = result.get("module_id", "")

        brain = getattr(orch, "g", None)
        if brain and brain.user_id == user_id:
            # Chunk and ingest into Brain G.
            for i, (url, content) in enumerate(zip(urls, contents)):
                try:
                    text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else str(content)
                    source = url or f"research_{module_id}_{i}"
                    brain.ingest_input(
                        content=text[:50000],
                        content_type="text",
                        source_file=source,
                    )
                except Exception as e:
                    print(f"handle_start_research: ingest chunk error: {e}")

            # Process file result for created components (params, fields, methods from extraction).
            try:
                file_result = {
                    "data": {"module_id": module_id},
                    "created_components": result.get("created_components", {}),
                }
                brain.process_file_result(
                    user_id=user_id,
                    file_result=file_result,
                    module_id=module_id,
                )
            except Exception as e:
                print(f"handle_start_research: process_file_result error: {e}")

        print("handle_start_research... done")
        return {
            "type": "START_RESEARCH",
            "status": {"state": "success", "code": 200, "msg": ""},
            "data": {
                "urls": urls,
                "module_id": module_id,
                "chunks_ingested": len(urls) if brain else 0,
            },
        }
    except Exception as e:
        print(f"handle_start_research: error: {e}")
        print("handle_start_research... done")
        return {
            "type": "START_RESEARCH",
            "status": {"state": "error", "code": 500, "msg": str(e)},
            "data": {"error": str(e)},
        }


START_RESEARCH_CASE: Dict[str, Any] = {
    "case": "START_RESEARCH",
    "desc": "Start research - find papers, retrieve content, chunk and ingest into Brain",
    "func": handle_start_research,
    "req_struct": {
        "auth": {"user_id": str, "session_id": str},
        "data": {"prompt": str, "msg": str},
    },
    "out_struct": {"type": "START_RESEARCH", "data": {"urls": list, "module_id": str, "chunks_ingested": int}},
}

RELAY_START_RESEARCH = [START_RESEARCH_CASE]
