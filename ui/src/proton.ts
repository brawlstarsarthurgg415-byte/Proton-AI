export type ProtonCommand =
  | "help" | "status" | "study" | "memory" | "learn" | "ask";

export type CommandRequest = {
  name: ProtonCommand;
  args: string[];
  raw: string;
};

export interface ProtonStatus {
  version: string;
  languages: readonly string[];
  studyMode: string;
  codingAgentReady: boolean;
}

export const protonStatus: ProtonStatus = Object.freeze({
  version: "0.4.0",
  languages: [
    "Rust", "C++", "Python", "TypeScript", "JavaScript", "Shell",
    "Go", "Java", "Ruby", "PHP", "C#", "Swift"
  ],
  studyMode: "curriculum-checkpoint",
  codingAgentReady: false
});

const knownCommands = new Set<ProtonCommand>([
  "help", "status", "study", "memory", "learn", "ask"
]);

export function parseCommand(input: string): CommandRequest {
  const raw = input.trim();
  if (!raw) throw new Error("Digite um comando.");
  const parts = raw.match(/(?:[^\s"]+|"[^"]*")+/g) ?? [];
  const name = parts.shift()?.toLowerCase() as ProtonCommand | undefined;
  if (!name || !knownCommands.has(name)) {
    throw new Error("Comando desconhecido. Use proton help.");
  }
  const args = parts.map(part => part.startsWith('"') && part.endsWith('"')
    ? part.slice(1, -1) : part);
  return { name, args, raw };
}

export function validateLearnText(text: string, maxLength = 20_000): string {
  const clean = text.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "").trim();
  if (!clean) throw new Error("A anotação não pode ficar vazia.");
  if (clean.length > maxLength) throw new Error(`Limite de ${maxLength} caracteres excedido.`);
  return clean;
}

export function commandHelp(): readonly string[] {
  return [
    "proton help", "proton status", "proton study --hours 15",
    "proton learn <texto>", "proton ask <termos>", "proton memory"
  ];
}
