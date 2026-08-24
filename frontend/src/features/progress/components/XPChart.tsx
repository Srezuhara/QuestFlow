import { NeonPanel } from "@/components/ui";
import { useXPSummary } from "../hooks";

const CHART_VIEW_HEIGHT = 100;
const BAR_GAP = 0.4;

/**
 * Hand-rolled SVG bar chart (no charting library, per §6.11) over the last
 * `days` of `xp-summary`. A visually-hidden `<table>` mirrors the same data
 * for screen readers — the SVG itself is `aria-hidden`, so nothing is lost,
 * not just decorated redundantly.
 */
export function XPChart({ days = 30 }: { days?: number }) {
  const { data, isLoading, isError } = useXPSummary(days);

  if (isLoading) {
    return (
      <NeonPanel>
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt;&gt; loading xp history...
        </p>
      </NeonPanel>
    );
  }
  if (isError || !data) {
    return (
      <NeonPanel>
        <p className="font-mono text-label-mono text-neon-pink uppercase">
          &gt;&gt; connection to mainframe failed
        </p>
      </NeonPanel>
    );
  }

  const maxXp = Math.max(1, ...data.days.map((d) => d.xp));
  const barWidth = 100 / Math.max(1, data.days.length);

  return (
    <NeonPanel>
      <h2 className="mb-4 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
        XP — Last {days} Days
      </h2>

      <svg
        viewBox={`0 0 100 ${CHART_VIEW_HEIGHT}`}
        preserveAspectRatio="none"
        className="h-40 w-full"
        aria-hidden="true"
      >
        {data.days.map((d, i) => {
          const barHeight = (d.xp / maxXp) * (CHART_VIEW_HEIGHT - 6);
          return (
            <rect
              key={d.date}
              data-testid="xp-chart-bar"
              x={i * barWidth + BAR_GAP / 2}
              y={CHART_VIEW_HEIGHT - barHeight}
              width={Math.max(0, barWidth - BAR_GAP)}
              height={barHeight}
              className={d.xp > 0 ? "fill-neon-lime" : "fill-surface-container-high"}
            >
              <title>{`${d.date}: ${d.xp} XP`}</title>
            </rect>
          );
        })}
      </svg>

      <table className="sr-only">
        <caption>XP earned per day, last {days} days</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">XP</th>
          </tr>
        </thead>
        <tbody>
          {data.days.map((d) => (
            <tr key={d.date}>
              <td>{d.date}</td>
              <td>{d.xp}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </NeonPanel>
  );
}
