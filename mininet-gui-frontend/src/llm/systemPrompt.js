export const buildSystemPrompt = (graphState) => {
  const actionsDescription = [
    "Available actions:",
    "- create_host({x,y})",
    "- create_switch({x,y})",
    "- create_link({from,to})",
    "- run_command({node_id, command})",
    "- run_pingall({})",
    "- delete_node({node_id})",
    "",
    "Topology descriptions:",
    "- Single-switch: one switch connected to k hosts.",
    "",
    "Example (single-switch):",
    "User prompt: 'Create a single-switch topology with 4 hosts.'",
    "Topology spec: create switch s1, create hosts h1..h4, link each host to s1.",
    "Spacing: place nodes 100 units apart on x/y (use -100 or +100 steps).",
    "",
    "Example coordinates:",
    "- s1 at (0, 0)",
    "- h1 at (-100, 100)",
    "- h2 at (0, 100)",
    "- h3 at (100, 100)",
    "- h4 at (200, 100)",
    "",
    "Topology guidance:",
    "- When creating multiple nodes, separate positions by 100 units on x and/or y (use -100 or +100 steps).",
  ].join("\n");

  const graphJson = graphState ? `Graph state (JSON): ${JSON.stringify(graphState)}` : "";
  return `${actionsDescription}\n\n${graphJson}`.trim();
};
