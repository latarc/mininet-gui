export const buildSystemPrompt = () => {
  const actionsDescription = [
    "Available actions:",
    "- create_host({nodes:[{x,y},...]})",
    "- create_switch({nodes:[{x,y},...]})",
    "- create_controller({nodes:[{x,y,remote,ip,port},...]})",
    "- create_link({from,to})",
    "- associate_switch({switch_id,controller_id})",
    "- get_topology({})",
    "- run_command({node_id, command})",
    "- delete_node({node_id})",
    "",
    "Topology descriptions:",
    "- Single-switch: one switch connected to k hosts.",
    "- Linear: k switches in a chain, each switch has n hosts.",
    "- Leaf-Spine Topology",
    "Definition:",
    "    Leaf-Spine is a two-layered network topology, where a series of",
    "    leaf switches that form the access layer are fully meshed to a",
    "    series of spine switches that form the backbone layer.",
    "Discussion:",
    "    In the Leaf-Spine topology, every leaf switch is connected to each",
    "    of the spine switches in the topology.",
    "",
    "Example (single-switch):",
    "User prompt: 'Create a single-switch topology with 4 hosts.'",
    "Topology spec: create switch s1, create hosts h1..h4, link each host to s1.",
    "Spacing: place nodes at least 100 units apart on x/y (use always +100 steps).",
    "",
    "Example coordinates:",
    "- s1 at (0, 0)",
    "- h1 at (0, 100)",
    "- h2 at (0, 200)",
    "- h3 at (100, 100)",
    "- h4 at (200, 100)",
    "",
    "Controller creation:",
    "- Default controller: create_controller({nodes:[{x,y,remote:false}]})",
    "- Remote controller: create_controller({nodes:[{x,y,remote:true,ip:\"1.2.3.4\",port:6653}]})",
    "- Every switch created should be associated to an existing controller. If the controller does not exist, DO NOT try to create it.",
    "",
    "Example (linear):",
    "User prompt: 'Create a linear topology with 3 switches and 2 hosts per switch.'",
    "Topology spec: create switches s1-s3 in a line, create links between s1-s2 and s2-s3 with each other. For each switch si, create hosts hj and link them to si.",
    "Spacing: switches along x by 100 units; hosts below each switch spaced by 100 units on x/y.",
    "",
    "Topology guidance:",
    "- When creating multiple nodes, separate positions by 100 units on x and/or y (use +100 steps).",
    "",
    "IMPORTANT: After creating topology, call get_topology() and verify that the graph matches the intended design.",
  ].join("\n");

  return actionsDescription.trim();
};

export const buildGraphStateMessage = (graphState) => {
  if (!graphState) return "";
  return `Graph state (JSON): ${JSON.stringify(graphState)}`.trim();
};
