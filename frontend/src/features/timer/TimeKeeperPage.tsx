import { useState } from "react";
import { NeonPanel } from "@/components/ui";
import { FocusCalendar } from "./components/FocusCalendar";
import { MissionLog } from "./components/MissionLog";
import { TaskLinkPicker } from "./components/TaskLinkPicker";
import { TimerControls } from "./components/TimerControls";
import { TimerDisplay } from "./components/TimerDisplay";
import { useFocusCalendar, useMissionLog } from "./hooks";
import { useFocusTimer } from "./useFocusTimer";

function todayIsoDate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

export function TimeKeeperPage() {
  const timer = useFocusTimer();
  const [pendingTaskId, setPendingTaskId] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState(todayIsoDate());
  const [calendarCursor, setCalendarCursor] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() + 1 };
  });

  const { data: sessions, isLoading: sessionsLoading } = useMissionLog(selectedDate);
  const { data: calendar, isLoading: calendarLoading } = useFocusCalendar(
    calendarCursor.year,
    calendarCursor.month,
  );

  function goToPrevMonth() {
    setCalendarCursor((c) =>
      c.month === 1 ? { year: c.year - 1, month: 12 } : { ...c, month: c.month - 1 },
    );
  }
  function goToNextMonth() {
    setCalendarCursor((c) =>
      c.month === 12 ? { year: c.year + 1, month: 1 } : { ...c, month: c.month + 1 },
    );
  }

  return (
    <div className="mx-auto flex max-w-[1440px] flex-col gap-8 p-4 md:p-8 lg:p-16">
      <header className="flex flex-col gap-2 border-b border-surface-container-highest pb-4">
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          <span className="animate-pulse">[SYSTEM ONLINE]</span>
        </p>
        <h1 className="font-display text-headline-lg text-on-surface uppercase tracking-tight">
          Time Keeper
        </h1>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <section className="lg:col-span-8">
          <NeonPanel glow={timer.isRunning}>
            <TimerDisplay
              mode={timer.mode}
              remainingSeconds={timer.remainingSeconds}
              isPaused={timer.isPaused}
            />
            <div className="mb-6">
              <TaskLinkPicker
                value={pendingTaskId}
                onChange={setPendingTaskId}
                disabled={timer.isRunning}
              />
            </div>
            <TimerControls
              isRunning={timer.isRunning}
              isPaused={timer.isPaused}
              onReset={timer.reset}
              onTogglePause={timer.togglePause}
              onStop={timer.stop}
              onStart={() => timer.start("focus", pendingTaskId)}
            />
          </NeonPanel>
        </section>

        <aside className="lg:col-span-4">
          <MissionLog sessions={sessions} isLoading={sessionsLoading} />
        </aside>
      </div>

      <FocusCalendar
        year={calendarCursor.year}
        month={calendarCursor.month}
        days={calendar?.days}
        isLoading={calendarLoading}
        selectedDate={selectedDate}
        onSelectDate={setSelectedDate}
        onPrevMonth={goToPrevMonth}
        onNextMonth={goToNextMonth}
      />
    </div>
  );
}
