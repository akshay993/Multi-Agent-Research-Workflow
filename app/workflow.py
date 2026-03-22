import json
import logging

from sqlmodel import Session, select

from app.agents.editor_agent import EditorAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.researcher_agent import ResearcherAgent
from app.agents.writer_agent import WriterAgent
from app.database import engine
from app.enums import AgentType, Status
from app.models import Report, Step
from app.schemas import StepState
from app.state import active_reports, sse_queues, state_lock

logger = logging.getLogger(__name__)


def _push_state(report_id: int, sentinel: bool = False):
    """Push the current report state to the SSE queue for a given report.

    If `sentinel` is True, enqueues None to signal end-of-stream and close
    the SSE connection. Otherwise, enqueues a JSON snapshot of the current
    ReportState. No-ops if no SSE queue exists for the report.
    """
    with state_lock:
        q = sse_queues.get(report_id)
        state = active_reports.get(report_id)
    if q is None:
        return
    if sentinel:
        q.put(None)
    elif state:
        q.put(state.model_dump_json())


def _create_step(
    report_id: int, description: str, agent_type: AgentType, order: int
) -> None:
    """Append a new step to both the in-memory report state and the database.

    The step is initialised with PENDING status. After writing, the updated
    state is pushed to the SSE queue so the client sees the new step immediately.
    """
    with state_lock:
        if report_id in active_reports:
            active_reports[report_id].steps.append(
                StepState(description=description, agent_type=agent_type)
            )

    with Session(engine) as session:
        session.add(
            Step(
                report_id=report_id,
                description=description,
                agent_type=agent_type,
                order=order,
            )
        )
        session.commit()

    _push_state(report_id)


def _update_step(
    report_id: int,
    step_index: int,
    status: Status,
    output: str = None,
    error: str = None,
):
    """Update the status, output, and error of an existing step in both the
    in-memory report state and the database.

    Only `status` is required; `output` and `error` are written only when
    provided. After persisting, the updated state is pushed to the SSE queue.
    """
    with state_lock:
        if report_id in active_reports:
            active_reports[report_id].steps[step_index].status = status

    with Session(engine) as session:
        step = session.exec(
            select(Step).where(Step.report_id == report_id, Step.order == step_index)
        ).first()
        if step:
            step.status = status
            if output is not None:
                step.output = output
            if error is not None:
                step.error = error
            session.commit()

    _push_state(report_id)


def _update_report(
    report_id: int, status: Status, result: str = None, error: str = None
):
    """Update the status, result, and error of a report in both the in-memory
    state and the database.

    Only `status` is required; `result` and `error` are written only when
    provided. After persisting, the final state is pushed to the SSE queue
    followed by a sentinel to close the SSE connection.
    """
    with state_lock:
        if report_id in active_reports:
            active_reports[report_id].status = status

    with Session(engine) as session:
        report = session.get(Report, report_id)
        if report:
            report.status = status
            if result is not None:
                report.result = result
            if error is not None:
                report.error = error
            session.commit()

    _push_state(report_id)  # send final state before closing
    _push_state(
        report_id, sentinel=True
    )  # signal end-of-stream to close SSE connection


def execute_research_workflow(report_id: int, user_prompt: str):
    agent_map = {
        "researcher_agent": ResearcherAgent(),
        "writer_agent": WriterAgent(),
        "editor_agent": EditorAgent(),
    }

    order = 0

    try:
        # Planning for the research task
        _create_step(
            report_id, "Generate a step-by-step research plan", AgentType.PLANNER, order
        )
        _update_step(report_id, order, Status.RUNNING)
        planner = PlannerAgent()
        steps = planner.run(task=user_prompt)
        _update_step(report_id, order, Status.COMPLETED, output=json.dumps(steps))
        order += 1

        if not steps:
            raise ValueError("Planner returned no steps.")

        history = []
        result = ""

        # Executing each planned step by routing to the assigned agent
        for step in steps:
            agent_key = step["agent"]
            task = step["step"]

            logger.info("step: %s", task)

            if agent_key not in agent_map:
                raise ValueError(f"Unknown agent '{agent_key}' assigned by planner.")

            agent_type = AgentType(agent_key)

            _create_step(report_id, task, agent_type, order)
            _update_step(report_id, order, Status.RUNNING)

            if (
                agent_key == "editor_agent"
            ):  # editor only sees the last writer output, not full history
                writer_steps = [h for h in history if h["agent"] == "writer_agent"]
                agent_history = writer_steps[-1:] if writer_steps else history
            else:
                agent_history = history

            result = agent_map[agent_key].run(task, history=agent_history)
            _update_step(report_id, order, Status.COMPLETED, output=result)
            history.append({"step": task, "agent": agent_key, "result": result})
            order += 1

        # Research workflow completed, report updated with the final result
        _update_report(report_id, Status.COMPLETED, result=result)

    except Exception as e:
        logger.exception("Workflow failed for report %d", report_id)
        error_msg = str(e)
        # Guardrail: `order` may point to a step that was never created. This happens when
        # an exception is raised after `order` was incremented but before `create_step`
        # was called for the new index (e.g. "Planner returned no steps" raises after
        # the planning step increments order to 1, or an unknown-agent error raises
        # before create_step in the loop). Calling update_step on a missing index would
        # cause an IndexError on the in-memory steps list.
        with state_lock:
            step_count = (
                len(active_reports[report_id].steps)
                if report_id in active_reports
                else 0
            )
        if order < step_count:
            _update_step(report_id, order, Status.FAILED, error=error_msg)
        _update_report(report_id, Status.FAILED, error=error_msg)
