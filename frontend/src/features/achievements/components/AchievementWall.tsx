import { lucideByName } from "@/lib/lucideByName";
import { useAchievements } from "../hooks";
import type { AchievementOut, AchievementTier } from "../api";

/** Tier → existing design tokens only (no new colours, per the plan §6.11);
 * legendary deliberately reuses neon-pink rather than inventing a fifth
 * accent. */
const TIER_CLASSES: Record<AchievementTier, string> = {
  bronze: "border-outline text-outline",
  silver: "border-on-surface-variant text-on-surface-variant",
  gold: "border-neon-yellow text-neon-yellow",
  legendary: "border-neon-pink text-neon-pink",
};

const TIER_GLOW: Record<AchievementTier, string> = {
  bronze: "shadow-[0_0_8px_rgba(142,147,121,0.4)]",
  silver: "shadow-[0_0_8px_rgba(196,201,172,0.4)]",
  gold: "shadow-[0_0_10px_rgba(234,234,0,0.5)]",
  legendary: "shadow-[0_0_12px_rgba(254,0,254,0.6)]",
};

function AchievementTile({ achievement }: { achievement: AchievementOut }) {
  const Icon = lucideByName(achievement.icon);
  const earned = achievement.earned_at !== null;

  return (
    <div
      className={`clip-chamfer flex flex-col items-center gap-2 border p-4 text-center ${
        earned
          ? `${TIER_CLASSES[achievement.tier]} ${TIER_GLOW[achievement.tier]}`
          : "border-outline-variant text-on-surface-variant grayscale opacity-60"
      }`}
    >
      <Icon size={28} aria-hidden="true" />
      <p className="font-mono text-label-mono uppercase">{achievement.name}</p>
      <p className="font-body text-body-md text-on-surface-variant">{achievement.description}</p>
      {earned ? (
        <p className="font-mono text-label-mono text-neon-lime uppercase">Earned</p>
      ) : (
        <p className="font-mono text-label-mono uppercase">
          {Math.round(achievement.progress_percent)}%
        </p>
      )}
    </div>
  );
}

export function AchievementWall() {
  const { data: achievements, isLoading, isError } = useAchievements();

  if (isLoading) {
    return (
      <p className="font-mono text-label-mono text-neon-lime uppercase">
        &gt;&gt; loading achievements...
      </p>
    );
  }
  if (isError || !achievements) {
    return (
      <p className="font-mono text-label-mono text-neon-pink uppercase">
        &gt;&gt; connection to mainframe failed
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {achievements.map((a) => (
        <AchievementTile key={a.id} achievement={a} />
      ))}
    </div>
  );
}
