/** Placeholder for screens whose real implementation lands in a later phase
 * (Dashboard/Habits/Timer/Notes/Reminders/Settings — phases 2-7). Keeps the
 * route tree and AppShell navigable end-to-end in phase 1 without faking
 * data that doesn't exist yet. */
export function ComingSoonScreen({ title }: { title: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 px-6 text-center">
      <p className="font-mono text-label-mono text-neon-lime uppercase">&gt;&gt; module offline</p>
      <h1 className="font-display text-headline-lg-mobile text-on-surface">{title}</h1>
      <p className="max-w-md font-body text-body-md text-on-surface-variant">
        This screen lands in a later build phase. Auth and navigation are live now.
      </p>
    </div>
  );
}
