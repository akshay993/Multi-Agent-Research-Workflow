import asyncio
import json
import queue as _queue
from threading import Thread

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlmodel import Session

from app.database import get_session
from app.enums import Status
from app.models import Report
from app.schemas import (CreateReportRequest, CreateReportResponse,
                         GetReportResponse, ReportState)
from app.state import active_reports, sse_queues, state_lock
from app.workflow import execute_research_workflow

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def index():
    with open("index.html") as f:
        return f.read()


@router.post(
    "/reports",
    status_code=201,
    response_model=CreateReportResponse,
    summary="Create a report",
    description="Submit a research prompt. Starts the multi-agent workflow in the background and returns the report ID immediately.",
)
def create_report(
    request_body: CreateReportRequest, session: Session = Depends(get_session)
):
    user_prompt = request_body.prompt
    report = Report(prompt=user_prompt, status=Status.RUNNING)

    session.add(report)
    session.commit()
    session.refresh(report)

    with state_lock:
        active_reports[report.id] = ReportState(status=Status.RUNNING, steps=[])
        sse_queues[report.id] = _queue.Queue()

    Thread(
        target=execute_research_workflow, args=(report.id, user_prompt), daemon=True
    ).start()

    return CreateReportResponse(report_id=report.id)


@router.get(
    "/reports/{report_id}/stream",
    summary="Stream report progress",
    description=(
        "Opens a Server-Sent Events (SSE) stream for a report. "
        "Each event is a JSON payload with `status` and `steps[]`. "
        "The stream closes when status reaches `completed` or `failed`."
    ),
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "SSE stream of workflow step updates",
        },
        404: {"description": "Report not found"},
    },
)
async def stream_report(report_id: int, session: Session = Depends(get_session)):
    if not session.get(Report, report_id):
        raise HTTPException(status_code=404, detail="Report not found")

    async def event_generator():
        q = sse_queues.get(report_id)
        if q is None:
            yield 'data: {"error": "Stream unavailable — server restarted after report was created"}\n\n'
            return

        loop = asyncio.get_running_loop()
        while True:
            try:
                data = await loop.run_in_executor(None, lambda: q.get(timeout=30))
            except _queue.Empty:
                yield 'data: {"ping": true}\n\n'
                continue

            if data is None:  # sentinel: stream finished
                break

            yield f"data: {data}\n\n"

            state = json.loads(data)
            if state.get("status") in ("completed", "failed"):
                break

        with state_lock:
            sse_queues.pop(report_id, None)
            active_reports.pop(report_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get(
    "/reports/{report_id}",
    response_model=GetReportResponse,
    summary="Get a report",
    description="Returns the status and final Markdown result of a completed report.",
    responses={
        200: {"description": "Report status and result"},
        404: {"description": "Report not found"},
    },
)
def get_report(report_id: int, session: Session = Depends(get_session)):
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return GetReportResponse(status=report.status, result=report.result)
