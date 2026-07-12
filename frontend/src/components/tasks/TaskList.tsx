import { useEffect, useState } from 'react'
import { CheckSquare, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useTaskStore } from '@/stores/useTaskStore'

export default function TaskList() {
  const { tasks, loading, error, list, add, toggleDone } = useTaskStore()
  const [title, setTitle] = useState('')
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
      await add(trimmed)
      setTitle('')
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
      <CardContent className="flex flex-col gap-3">
        <form onSubmit={handleAdd} className="flex gap-2">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Add a task…"
            aria-label="New task title"
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
          <ul className="flex flex-col gap-2">
            {tasks.map((task) => (
              <li key={task.id} className="flex items-center gap-2">
                <Checkbox
                  checked={task.done}
                  disabled={task.done}
                  onCheckedChange={() => void toggleDone(task.id)}
                  aria-label={`Mark "${task.title}" done`}
                />
                <span className={`text-sm ${task.done ? 'text-muted-foreground line-through' : ''}`}>
                  {task.title}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
