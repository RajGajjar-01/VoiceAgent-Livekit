import { useEffect, useState } from 'react'
import { CheckSquare, Plus, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useTaskStore } from '@/stores/useTaskStore'

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  not_started: { label: 'Not started', className: 'bg-gray-100 text-gray-700 hover:bg-gray-100' },
  in_progress: { label: 'In progress', className: 'bg-blue-100 text-blue-700 hover:bg-blue-100' },
  completed: { label: 'Completed', className: 'bg-green-100 text-green-700 hover:bg-green-100' },
}

export default function TaskList() {
  const { tasks, loading, error, list, add, setStatus, remove } = useTaskStore()
  const [title, setTitle] = useState('')
  const [duration, setDuration] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    void list()
  }, [list])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed || submitting) return
    setSubmitting(true)
    try {
      const dur = duration ? parseInt(duration, 10) : null
      await add(trimmed, dur)
      setTitle('')
      setDuration('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckSquare className="size-4" /> Tasks
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={handleAdd} className="flex gap-2">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Add a task…"
            aria-label="New task title"
            className="flex-1"
          />
          <Input
            type="number"
            min={1}
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            placeholder="Min"
            aria-label="Estimated duration in minutes"
            className="w-20"
          />
          <Button type="submit" size="icon" disabled={submitting || !title.trim()} aria-label="Add task">
            <Plus className="size-4" />
          </Button>
        </form>

        {loading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-3/4" />
          </div>
        )}

        {!loading && error && <p className="text-sm text-destructive">{error}</p>}

        {!loading && !error && tasks.length === 0 && (
          <p className="text-sm text-muted-foreground">No tasks yet.</p>
        )}

        {!loading && !error && tasks.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10 text-center">#</TableHead>
                <TableHead>Task</TableHead>
                <TableHead className="w-24">Duration</TableHead>
                <TableHead className="w-36">Status</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {tasks.map((task, idx) => (
                <TableRow key={task.id} className="group">
                  <TableCell className="text-center text-muted-foreground">{idx + 1}</TableCell>
                  <TableCell className={task.status === 'completed' ? 'text-muted-foreground line-through' : ''}>
                    {task.title}
                  </TableCell>
                  <TableCell>{task.duration_minutes ? `${task.duration_minutes} min` : '—'}</TableCell>
                  <TableCell>
                    <Select
                      value={task.status}
                      onValueChange={(val) => void setStatus(task.id, val)}
                    >
                      <SelectTrigger size="sm" className="border-none p-0 shadow-none hover:bg-transparent focus-visible:ring-0">
                        <Badge className={STATUS_CONFIG[task.status]?.className}>
                          {STATUS_CONFIG[task.status]?.label}
                        </Badge>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="not_started">Not started</SelectItem>
                        <SelectItem value="in_progress">In progress</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <button
                      className="opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive"
                      onClick={() => void remove(task.id)}
                      aria-label={`Delete "${task.title}"`}
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
