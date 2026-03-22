import queue
import threading

from app.schemas import ReportState

active_reports: dict[int, ReportState] = {}

sse_queues: dict[int, queue.Queue] = {}

state_lock = threading.Lock()
