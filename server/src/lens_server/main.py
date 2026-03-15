from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from lens_server.config import get_settings
from lens_server.database import get_db, init_db
from lens_server.schemas import (
    CostsResponse,
    FailureStats,
    HealthResponse,
    OverviewStats,
    SessionDetail,
    SessionSummary,
    TraceCreate,
    TraceRead,
)
from lens_server.serializers import trace_to_dict
from lens_server.services import (
    create_demo_trace,
    create_trace,
    get_cost_buckets,
    get_failure_stats,
    get_overview_stats,
    get_session_detail,
    get_trace_by_id,
    list_sessions,
    list_traces,
)
from lens_server.websocket import manager

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(status="ok", database_path=str(settings.database_path))


@app.get(f"{settings.api_v1_prefix}/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", database_path=str(settings.database_path))


@app.post(
    f"{settings.api_v1_prefix}/traces",
    response_model=TraceRead,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_trace(payload: TraceCreate, db: Session = Depends(get_db)) -> TraceRead:
    try:
        trace = create_trace(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trace with this trace_id already exists",
        ) from exc
    trace_response = TraceRead.model_validate(trace_to_dict(trace))
    await manager.broadcast(
        {
            "event": "trace.created",
            "data": trace_response.model_dump(mode="json"),
        }
    )
    return trace_response


@app.get(f"{settings.api_v1_prefix}/traces", response_model=list[TraceRead])
def get_traces(
    provider: str | None = None,
    model: str | None = None,
    status: str | None = None,
    session_id: str | None = None,
    days: int | None = Query(default=None, ge=1, le=3650),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[TraceRead]:
    traces = list_traces(
        db,
        provider=provider,
        model=model,
        status=status,
        session_id=session_id,
        days=days,
        limit=limit,
        offset=offset,
    )
    return [TraceRead.model_validate(trace_to_dict(trace)) for trace in traces]


@app.get(f"{settings.api_v1_prefix}/traces/{{trace_id}}", response_model=TraceRead)
def get_trace(trace_id: str, db: Session = Depends(get_db)) -> TraceRead:
    trace = get_trace_by_id(db, trace_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    return TraceRead.model_validate(trace_to_dict(trace))


@app.get(f"{settings.api_v1_prefix}/sessions", response_model=list[SessionSummary])
def get_sessions(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[SessionSummary]:
    return [
        SessionSummary.model_validate(row) for row in list_sessions(db, limit=limit, offset=offset)
    ]


@app.get(f"{settings.api_v1_prefix}/sessions/{{session_id}}", response_model=SessionDetail)
def get_single_session(session_id: str, db: Session = Depends(get_db)) -> SessionDetail:
    detail = get_session_detail(db, session_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return SessionDetail(
        session=SessionSummary.model_validate(detail["session"]),
        traces=[TraceRead.model_validate(trace_to_dict(trace)) for trace in detail["traces"]],
    )


@app.get(f"{settings.api_v1_prefix}/stats/overview", response_model=OverviewStats)
def get_overview(
    days: int | None = Query(default=None, ge=1, le=3650),
    db: Session = Depends(get_db),
) -> OverviewStats:
    return OverviewStats.model_validate(get_overview_stats(db, days=days))


@app.get(f"{settings.api_v1_prefix}/stats/costs", response_model=CostsResponse)
def get_costs(
    group_by: Literal["day", "provider", "model"] = "day",
    provider: str | None = None,
    model: str | None = None,
    session_id: str | None = None,
    days: int | None = Query(default=7, ge=1, le=3650),
    db: Session = Depends(get_db),
) -> CostsResponse:
    buckets = get_cost_buckets(
        db,
        group_by=group_by,
        provider=provider,
        model=model,
        session_id=session_id,
        days=days,
    )
    return CostsResponse(group_by=group_by, buckets=buckets)


@app.get(f"{settings.api_v1_prefix}/stats/failures", response_model=FailureStats)
def get_failures(
    limit: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
) -> FailureStats:
    payload = get_failure_stats(db, limit=limit)
    return FailureStats(
        total_failures=payload["total_failures"],
        by_error_type=payload["by_error_type"],
        by_provider=payload["by_provider"],
        recent_failures=[
            TraceRead.model_validate(trace_to_dict(trace)) for trace in payload["recent_failures"]
        ],
    )


@app.post(
    f"{settings.api_v1_prefix}/demo/trace",
    response_model=TraceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_demo_trace_endpoint(db: Session = Depends(get_db)) -> TraceRead:
    trace = create_demo_trace(db)
    trace_response = TraceRead.model_validate(trace_to_dict(trace))
    await manager.broadcast(
        {
            "event": "trace.created",
            "data": trace_response.model_dump(mode="json"),
        }
    )
    return trace_response


@app.websocket("/ws/traces")
async def traces_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await websocket.send_json(
        {"event": "connected", "data": {"message": "LENS trace stream ready"}}
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
