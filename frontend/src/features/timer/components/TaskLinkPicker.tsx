import { useTasks } from "@/features/tasks/hooks";

export function TaskLinkPicker({
  value,
  onChange,
  disabled,
}: {
  value: string | null;
  onChange: (taskId: string | null) => void;
  disabled?: boolean;
}) {
  const { data: tasks } = useTasks();
  const activeTasks = (tasks ?? []).filter(
    (t) => t.status === "todo" || t.status === "in_progress",
  );

  return (
    <div className="flex flex-col gap-2">
      <label
        htmlFor="focus-task-link"
        className="font-mono text-label-mono text-on-surface-variant uppercase"
      >
        Link to Quest (optional)
      </label>
      <select
        id="focus-task-link"
        value={value ?? ""}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value || null)}
        className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-mono text-label-mono text-on-surface outline-none focus:border-neon-lime disabled:cursor-not-allowed disabled:opacity-50"
      >
        <option value="">No linked quest</option>
        {activeTasks.map((task) => (
          <option key={task.id} value={task.id}>
            {task.title}
          </option>
        ))}
      </select>
    </div>
  );
}
