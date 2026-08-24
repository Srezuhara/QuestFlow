import { useState } from "react";
import { Modal, NeonButton } from "@/components/ui";
import { useCreateHabit } from "../hooks";
import type { HabitCadence } from "../api";
import type { components } from "@/types/api";

type SkillBranch = components["schemas"]["SkillBranch"];

const CADENCES: HabitCadence[] = ["daily", "weekly"];
const SKILL_BRANCHES: SkillBranch[] = ["focus", "health", "discipline", "growth", "wealth"];

export function NewHabitModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cadence, setCadence] = useState<HabitCadence>("daily");
  const [targetPerPeriod, setTargetPerPeriod] = useState(1);
  const [skillBranch, setSkillBranch] = useState<SkillBranch>("focus");
  const [xpValue, setXpValue] = useState(50);
  const createHabit = useCreateHabit();

  function reset() {
    setName("");
    setDescription("");
    setCadence("daily");
    setTargetPerPeriod(1);
    setSkillBranch("focus");
    setXpValue(50);
    createHabit.reset();
  }

  function handleClose() {
    reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    createHabit.mutate(
      {
        name: name.trim(),
        description: description.trim() || null,
        cadence,
        target_per_period: targetPerPeriod,
        skill_branch: skillBranch,
        xp_value: xpValue,
      },
      { onSuccess: handleClose },
    );
  }

  return (
    <Modal open={open} onClose={handleClose} title="New Habit">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label
            htmlFor="habit-name"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Name
          </label>
          <input
            id="habit-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Morning Run"
            autoFocus
            required
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label
            htmlFor="habit-description"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Description (optional)
          </label>
          <input
            id="habit-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        <div className="flex flex-col gap-2">
          <span className="font-mono text-label-mono text-on-surface-variant uppercase">
            Cadence
          </span>
          <div className="flex gap-2">
            {CADENCES.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setCadence(c)}
                className={`clip-chamfer border px-3 py-1.5 font-mono text-label-mono uppercase ${
                  cadence === c
                    ? "border-neon-lime text-neon-lime"
                    : "border-outline-variant text-on-surface-variant"
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <label
              htmlFor="habit-target"
              className="font-mono text-label-mono text-on-surface-variant uppercase"
            >
              Target / Period
            </label>
            <input
              id="habit-target"
              type="number"
              min={1}
              value={targetPerPeriod}
              onChange={(e) => setTargetPerPeriod(Math.max(1, Number(e.target.value)))}
              className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
            />
          </div>
          <div className="flex flex-col gap-2">
            <label
              htmlFor="habit-xp"
              className="font-mono text-label-mono text-on-surface-variant uppercase"
            >
              XP Value
            </label>
            <input
              id="habit-xp"
              type="number"
              min={0}
              value={xpValue}
              onChange={(e) => setXpValue(Math.max(0, Number(e.target.value)))}
              className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label
            htmlFor="habit-branch"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Skill Branch
          </label>
          <select
            id="habit-branch"
            value={skillBranch}
            onChange={(e) => setSkillBranch(e.target.value as SkillBranch)}
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-mono text-label-mono text-on-surface outline-none focus:border-neon-lime"
          >
            {SKILL_BRANCHES.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </div>

        {createHabit.isError && (
          <p className="font-mono text-label-mono text-neon-pink">
            Failed to create the habit. Please try again.
          </p>
        )}

        <div className="mt-2 flex justify-end gap-3">
          <NeonButton type="button" variant="ghost" onClick={handleClose}>
            Cancel
          </NeonButton>
          <NeonButton type="submit" disabled={createHabit.isPending}>
            {createHabit.isPending ? "Deploying..." : "Create Habit"}
          </NeonButton>
        </div>
      </form>
    </Modal>
  );
}
