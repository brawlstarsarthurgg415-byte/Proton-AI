// Small JavaScript helper used by the Proton developer UI.
export const protonCommands = Object.freeze({
  help: "proton help",
  status: "proton status",
  study15h: "proton study --hours 15",
  memory: "proton memory"
});

export function makeLearnCommand(text) {
  const clean = String(text ?? "").trim().replace(/[\\r\\n]+/g, " ");
  if (!clean) throw new Error("Digite um conhecimento antes de enviar.");
  return "proton learn " + JSON.stringify(clean);
}
