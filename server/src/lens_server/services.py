from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import choice, randint, random
from uuid import uuid4

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from lens_server.models import Trace
from lens_server.pricing import calculate_cost_usd
from lens_server.schemas import TraceCreate


def _normalize_timestamp(raw_timestamp: datetime | None) -> datetime:
    if raw_timestamp is None:
        return datetime.now(timezone.utc)
    if raw_timestamp.tzinfo is None:
        return raw_timestamp.replace(tzinfo=timezone.utc)
    return raw_timestamp.astimezone(timezone.utc)


def _is_empty_response(response_payload: dict[str, object] | None) -> bool:
    if response_payload in (None, {}, []):
        return True
    if isinstance(response_payload, dict):
        for key in ("content", "text", "output_text"):
            value = response_payload.get(key)
            if value == "":
                return True
    return False


def _derive_error_type(error_msg: str | None) -> str:
    if not error_msg:
        return "error"

    lowered = error_msg.lower()
    if "rate limit" in lowered or "429" in lowered:
        return "rate_limit"
    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"
    if "empty" in lowered:
        return "empty_response"
    return "error"


def _normalize_status(payload: TraceCreate) -> tuple[str, str | None, str | None]:
    status = payload.status
    error_msg = payload.error_msg

    if status == "success" and _is_empty_response(payload.response):
        return "empty_response", "empty_response", error_msg or "Model returned an empty response"

    if status == "success":
        return "success", None, error_msg

    if status in {"timeout", "rate_limit", "empty_response"}:
        return status, status, error_msg

    derived_error = _derive_error_type(error_msg)
    normalized_status = derived_error if derived_error in {"timeout", "rate_limit"} else "error"
    return normalized_status, derived_error, error_msg


def _apply_trace_filters(
    stmt: Select[tuple[Trace]],
    *,
    provider: str | None = None,
    model: str | None = None,
    status: str | None = None,
    session_id: str | None = None,
    days: int | None = None,
) -> Select[tuple[Trace]]:
    if provider:
        stmt = stmt.where(Trace.provider == provider)
    if model:
        stmt = stmt.where(Trace.model == model)
    if status:
        stmt = stmt.where(Trace.status == status)
    if session_id:
        stmt = stmt.where(Trace.session_id == session_id)
    if days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = stmt.where(Trace.timestamp >= since)
    return stmt


def create_trace(db: Session, payload: TraceCreate) -> Trace:
    total_tokens = payload.total_tokens or (payload.prompt_tokens + payload.completion_tokens)
    status, error_type, error_msg = _normalize_status(payload)
    cost_usd = calculate_cost_usd(
        provider=payload.provider,
        model=payload.model,
        prompt_tokens=payload.prompt_tokens,
        completion_tokens=payload.completion_tokens,
    )

    trace = Trace(
        trace_id=payload.trace_id or str(uuid4()),
        session_id=payload.session_id,
        user_id=payload.user_id,
        provider=payload.provider,
        model=payload.model,
        endpoint=payload.endpoint,
        request=payload.request,
        response=payload.response,
        metadata_json=payload.metadata,
        prompt_tokens=payload.prompt_tokens,
        completion_tokens=payload.completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        latency_ms=payload.latency_ms,
        status=status,
        error_type=error_type,
        error_msg=error_msg,
        timestamp=_normalize_timestamp(payload.timestamp),
    )

    db.add(trace)
    db.commit()
    db.refresh(trace)
    return trace


def list_traces(
    db: Session,
    *,
    provider: str | None = None,
    model: str | None = None,
    status: str | None = None,
    session_id: str | None = None,
    days: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Trace]:
    stmt = select(Trace).order_by(Trace.timestamp.desc())
    stmt = _apply_trace_filters(
        stmt,
        provider=provider,
        model=model,
        status=status,
        session_id=session_id,
        days=days,
    )
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt))


def get_trace_by_id(db: Session, trace_id: str) -> Trace | None:
    stmt = select(Trace).where(Trace.trace_id == trace_id)
    return db.scalar(stmt)


def list_sessions(db: Session, *, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    failure_case = case((Trace.status != "success", 1), else_=0)
    success_case = case((Trace.status == "success", 1), else_=0)

    stmt = (
        select(
            Trace.session_id.label("session_id"),
            func.count(Trace.id).label("trace_count"),
            func.sum(success_case).label("success_count"),
            func.sum(failure_case).label("failure_count"),
            func.coalesce(func.sum(Trace.cost_usd), 0.0).label("total_cost_usd"),
            func.min(Trace.timestamp).label("started_at"),
            func.max(Trace.timestamp).label("last_seen_at"),
        )
        .where(Trace.session_id.is_not(None))
        .group_by(Trace.session_id)
        .order_by(func.max(Trace.timestamp).desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(stmt).mappings().all()
    return [dict(row) for row in rows]


def get_session_detail(db: Session, session_id: str) -> dict[str, object] | None:
    summaries = list_sessions_for_ids(db, [session_id])
    if not summaries:
        return None

    traces = list(
        db.scalars(
            select(Trace)
            .where(Trace.session_id == session_id)
            .order_by(Trace.timestamp.asc(), Trace.id.asc())
        )
    )
    return {
        "session": summaries[0],
        "traces": traces,
    }


def list_sessions_for_ids(db: Session, session_ids: list[str]) -> list[dict[str, object]]:
    if not session_ids:
        return []

    failure_case = case((Trace.status != "success", 1), else_=0)
    success_case = case((Trace.status == "success", 1), else_=0)
    stmt = (
        select(
            Trace.session_id.label("session_id"),
            func.count(Trace.id).label("trace_count"),
            func.sum(success_case).label("success_count"),
            func.sum(failure_case).label("failure_count"),
            func.coalesce(func.sum(Trace.cost_usd), 0.0).label("total_cost_usd"),
            func.min(Trace.timestamp).label("started_at"),
            func.max(Trace.timestamp).label("last_seen_at"),
        )
        .where(Trace.session_id.in_(session_ids))
        .group_by(Trace.session_id)
    )
    rows = db.execute(stmt).mappings().all()
    return [dict(row) for row in rows]


def get_overview_stats(db: Session, *, days: int | None = None) -> dict[str, object]:
    base_stmt = select(Trace)
    base_stmt = _apply_trace_filters(base_stmt, days=days)
    subquery = base_stmt.subquery()

    failure_case = case((subquery.c.status != "success", 1), else_=0)
    success_case = case((subquery.c.status == "success", 1), else_=0)

    totals_stmt = select(
        func.count(subquery.c.id).label("total_traces"),
        func.coalesce(func.sum(success_case), 0).label("successful_traces"),
        func.coalesce(func.sum(failure_case), 0).label("failed_traces"),
        func.coalesce(func.sum(subquery.c.cost_usd), 0.0).label("total_cost_usd"),
        func.coalesce(func.avg(subquery.c.latency_ms), 0.0).label("average_latency_ms"),
    )
    totals = dict(db.execute(totals_stmt).mappings().one())

    provider_stmt = (
        select(
            subquery.c.provider.label("provider"),
            func.count(subquery.c.id).label("trace_count"),
            func.coalesce(func.sum(subquery.c.cost_usd), 0.0).label("total_cost_usd"),
        )
        .group_by(subquery.c.provider)
        .order_by(func.count(subquery.c.id).desc())
    )
    providers = [dict(row) for row in db.execute(provider_stmt).mappings().all()]
    totals["providers"] = providers
    return totals


def get_cost_buckets(
    db: Session,
    *,
    group_by: str,
    provider: str | None = None,
    model: str | None = None,
    session_id: str | None = None,
    days: int | None = 7,
) -> list[dict[str, object]]:
    if group_by == "day":
        bucket_key = func.date(Trace.timestamp)
    elif group_by == "provider":
        bucket_key = Trace.provider
    else:
        bucket_key = Trace.model

    stmt = select(
        bucket_key.label("key"),
        func.count(Trace.id).label("trace_count"),
        func.coalesce(func.sum(Trace.cost_usd), 0.0).label("cost_usd"),
        func.coalesce(func.sum(Trace.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(Trace.completion_tokens), 0).label("completion_tokens"),
    )
    stmt = _apply_trace_filters(
        stmt,
        provider=provider,
        model=model,
        session_id=session_id,
        days=days,
    )
    stmt = stmt.group_by(bucket_key).order_by(bucket_key.asc())
    rows = db.execute(stmt).mappings().all()
    return [dict(row) for row in rows]


def get_failure_stats(db: Session, *, limit: int = 25) -> dict[str, object]:
    failure_stmt = select(Trace).where(Trace.status != "success")
    total_failures = db.scalar(select(func.count()).select_from(failure_stmt.subquery())) or 0

    error_type_stmt = (
        select(
            func.coalesce(Trace.error_type, "error").label("key"),
            func.count(Trace.id).label("count"),
        )
        .where(Trace.status != "success")
        .group_by(func.coalesce(Trace.error_type, "error"))
        .order_by(func.count(Trace.id).desc())
    )
    provider_stmt = (
        select(
            Trace.provider.label("key"),
            func.count(Trace.id).label("count"),
        )
        .where(Trace.status != "success")
        .group_by(Trace.provider)
        .order_by(func.count(Trace.id).desc())
    )
    recent_stmt = (
        select(Trace)
        .where(Trace.status != "success")
        .order_by(Trace.timestamp.desc(), Trace.id.desc())
        .limit(limit)
    )
    return {
        "total_failures": total_failures,
        "by_error_type": [dict(row) for row in db.execute(error_type_stmt).mappings().all()],
        "by_provider": [dict(row) for row in db.execute(provider_stmt).mappings().all()],
        "recent_failures": list(db.scalars(recent_stmt)),
    }


def create_demo_trace(db: Session) -> Trace:
    provider, model = choice(
        [
            ("openai", "gpt-5.4"),
            ("anthropic", "claude-sonnet-4-6"),
            ("gemini", "gemini-2.5-pro"),
        ]
    )
    status = choice(["success", "success", "success", "timeout", "rate_limit"])
    prompt_tokens = randint(120, 1600)
    completion_tokens = randint(40, 360) if status == "success" else 0
    session_id = f"demo-session-{randint(1, 5)}"

    payload = TraceCreate(
        trace_id=f"demo-{provider}-{uuid4()}",
        session_id=session_id,
        user_id="demo-user",
        provider=provider,
        model=model,
        endpoint="demo.synthetic.generate",
        request={
            "messages": [{"role": "user", "content": "Show me a demo trace"}],
            "temperature": round(0.2 + random() * 0.8, 2),
        },
        response={"content": "Synthetic response from the local LENS demo flow."}
        if status == "success"
        else None,
        metadata={"session_id": session_id, "source": "demo-api"},
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=randint(180, 3200),
        status=status,
        error_msg=(
            "request timeout"
            if status == "timeout"
            else "rate limit exceeded"
            if status == "rate_limit"
            else None
        ),
        timestamp=datetime.now(timezone.utc),
    )
    return create_trace(db, payload)
