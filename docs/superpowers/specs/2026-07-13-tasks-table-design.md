# Tasks table — design

## Problem

The Tasks page currently renders a checklist (title + done checkbox). The user wants a
table with a row number, task name, estimated duration to complete, and a richer status
than a boolean — and both backend and frontend need to support it.

## Data model

`Task` ([backend/app/models/task.py](../../../backend/app/models/task.py)) changes:

- Remove `done: bool`.
- Add `status: str`, one of `not_started` / `in_progress` / `completed`, default
  `not_started`.
- Add `duration_minutes: int | None` — an estimate the user (or the voice agent on
  their behalf) sets when creating a task, not a measured/tracked time.

### Migration

Single Alembic migration:

1. Add `status` (default `not_started`) and `duration_minutes` (nullable) columns.
2. Backfill `status` from the existing `done` column: `true → completed`,
   `false → not_started`. No existing row can retroactively become `in_progress`.
3. Drop the `done` column.

## Backend API (`/api/v1/tasks`, [tasks.py](../../../backend/app/api/v1/tasks.py))

- `POST /` — `CreateTaskRequest{title: str, duration_minutes: int | None = None}`.
  Creates with `status=not_started`.
- `GET /` — `TaskResponse{id, title, status, duration_minutes, created_at}`. Ordering
  unchanged (newest first, `created_at desc`).
- `PATCH /{id}/status` — replaces `PATCH /{id}/toggle-done`. Body
  `{status: "not_started" | "in_progress" | "completed"}`, sets it directly (no
  toggling/cycling server-side).
- `DELETE /{id}` — unchanged.

`TaskRepository` ([task_repository.py](../../../backend/app/repositories/task_repository.py)):

- `create(user_id, title, duration_minutes=None)`.
- `toggle_done` → `set_status(task_id, user_id, status)`.
- `find_by_title`: ordering that currently prefers not-done tasks
  (`Task.done.asc()`) switches to preferring non-completed tasks
  (`Task.status != "completed"` first), since `complete_task` should still resolve to
  the open task when titles are ambiguous.

## Voice agent tools ([tools.py](../../../backend/app/agent/tools.py))

- `create_task(title, duration_minutes: int | None = None)` — agent may state a
  duration when the user gives one ("that'll take about 20 minutes").
- `complete_task(title)` — unchanged signature; now sets `status=completed` via
  `set_status`.
- `list_tasks()` — include duration in the per-task summary line when set (e.g.
  `"Write report (in progress, 45 min)"`).

No agent tool is added for setting `in_progress` — that stays a UI-only action via the
status dropdown, since voice control of that intermediate state wasn't requested.

## Frontend

- Add shadcn `table` and `select` components via the CLI (`npx shadcn add table
  select`), consistent with the existing base-nova shadcn setup — not hand-rolled.
- `useTaskStore` ([useTaskStore.ts](../../../frontend/src/stores)): `Task{id, title,
  status, duration_minutes, created_at}`. Replace `toggleDone(id)` with
  `setStatus(id, status)`. `add(title, durationMinutes?)`.
- `TaskList.tsx` becomes a table with columns:
  - **#** — row position in current (newest-first) display order, not a stored value.
  - **Task** — title.
  - **Duration** — `"{n} min"` or `"—"` if unset.
  - **Status** — a per-row `<Select>` with the three states; changing it calls
    `setStatus`.
  - Delete action (unchanged, icon button).
  - The add-task form gains an optional numeric duration input next to the title
    input.

## Out of scope

- Editing duration after creation (only settable at creation time, via UI or voice).
- Sorting/filtering the table by column.
- An `in_progress` voice command.
