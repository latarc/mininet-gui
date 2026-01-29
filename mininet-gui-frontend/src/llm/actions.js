export const llmTools = [
  {
    type: "function",
    function: {
      name: "create_host",
      description: "Create a host node in the topology.",
      parameters: {
        type: "object",
        properties: {
          x: { type: "number", description: "Optional x position in canvas coordinates." },
          y: { type: "number", description: "Optional y position in canvas coordinates." },
          nodes: {
            type: "array",
            description: "Batch create hosts with positions.",
            items: {
              type: "object",
              properties: {
                x: { type: "number" },
                y: { type: "number" }
              },
              required: []
            }
          }
        },
        required: []
      }
    }
  },
  {
    type: "function",
    function: {
      name: "create_switch",
      description: "Create a switch node in the topology.",
      parameters: {
        type: "object",
        properties: {
          x: { type: "number", description: "Optional x position in canvas coordinates." },
          y: { type: "number", description: "Optional y position in canvas coordinates." },
          nodes: {
            type: "array",
            description: "Batch create switches with positions.",
            items: {
              type: "object",
              properties: {
                x: { type: "number" },
                y: { type: "number" }
              },
              required: []
            }
          }
        },
        required: []
      }
    }
  },
  {
    type: "function",
    function: {
      name: "create_link",
      description: "Create a link between two existing nodes by id.",
      parameters: {
        type: "object",
        properties: {
          from: { type: "string", description: "Source node id, e.g. h1" },
          to: { type: "string", description: "Destination node id, e.g. s1" }
        },
        required: ["from", "to"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "run_command",
      description: "Run a shell command in a node terminal.",
      parameters: {
        type: "object",
        properties: {
          node_id: { type: "string", description: "Node id, e.g. h1" },
          command: { type: "string", description: "Command to execute" }
        },
        required: ["node_id", "command"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "run_pingall",
      description: "Run Mininet pingall test.",
      parameters: {
        type: "object",
        properties: {}
      }
    }
  },
  {
    type: "function",
    function: {
      name: "delete_node",
      description: "Delete a node by id.",
      parameters: {
        type: "object",
        properties: {
          node_id: { type: "string", description: "Node id, e.g. h1" }
        },
        required: ["node_id"]
      }
    }
  }
];

export const buildLlmsActions = (handlers) => ({
  async create_host(args = {}) {
    return handlers.createHost?.(args);
  },
  async create_switch(args = {}) {
    return handlers.createSwitch?.(args);
  },
  async create_link(args = {}) {
    return handlers.createLink?.(args);
  },
  async run_command(args = {}) {
    return handlers.runCommand?.(args);
  },
  async run_pingall(args = {}) {
    return handlers.runPingall?.(args);
  },
  async delete_node(args = {}) {
    return handlers.deleteNode?.(args);
  },
});

export const runToolCalls = async (toolCalls, handlers) => {
  const toolHandlers = buildLlmsActions(handlers);
  const results = [];
  for (const call of toolCalls) {
    const name = call?.function?.name;
    let args = {};
    if (call?.function?.arguments) {
      try {
        args = JSON.parse(call.function.arguments);
      } catch (error) {
        results.push({
          role: "tool",
          tool_call_id: call.id,
          content: JSON.stringify({ error: "Invalid tool arguments JSON." }),
        });
        continue;
      }
    }
    if (!toolHandlers[name]) {
      results.push({
        role: "tool",
        tool_call_id: call.id,
        content: JSON.stringify({ error: `Unknown tool: ${name}` }),
      });
      continue;
    }
    try {
      const output = await toolHandlers[name](args);
      results.push({
        role: "tool",
        tool_call_id: call.id,
        content: JSON.stringify({ ok: true, output }),
      });
    } catch (error) {
      results.push({
        role: "tool",
        tool_call_id: call.id,
        content: JSON.stringify({ error: String(error?.message || error) }),
      });
    }
  }
  return results;
};
