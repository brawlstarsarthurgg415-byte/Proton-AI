export type ProtonCommand = "status" | "study" | "memory";
export interface ProtonStatus { version: string; languages: string[]; studyMode: string; }
export const protonStatus: ProtonStatus = {
  version: "0.3.0",
  languages: ["Rust", "C++", "Python", "TypeScript", "JavaScript", "Shell"],
  studyMode: "curriculum-checkpoint"
};
export function commandHelp(): string[] {
  return ["proton help", "proton status", "proton study --hours 15", "proton learn <texto>", "proton ask <termos>", "proton memory"];
}
