import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type SkillNodeOut = components["schemas"]["SkillNodeOut"];
export type SkillNodeState = components["schemas"]["SkillNodeState"];
export type SkillTreeOut = components["schemas"]["SkillTreeOut"];
export type UnlockResponse = components["schemas"]["UnlockResponse"];

export function fetchSkillTree(): Promise<SkillTreeOut> {
  return apiJson<SkillTreeOut>("/me/skill-tree");
}

export function unlockSkillNode(code: string): Promise<UnlockResponse> {
  return apiJson<UnlockResponse>(`/skill-nodes/${code}/unlock`, { method: "POST" });
}
