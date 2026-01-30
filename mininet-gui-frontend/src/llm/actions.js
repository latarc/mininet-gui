export const llmTools = [
  {
    type: "function",
    function: {
      name: "create_host",
      description: "Create host nodes in batch.",
      parameters: {
        type: "object",
        properties: {
          nodes: {
            type: "array",
            description: "Batch create hosts with positions.",
            items: {
              type: "object",
              properties: {
                x: { type: "number" },
                y: { type: "number" }
              },
              required: ["x", "y"]
            }
          }
        },
        required: ["nodes"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "create_switch",
      description: "Create switch nodes in batch.",
      parameters: {
        type: "object",
        properties: {
          nodes: {
            type: "array",
            description: "Batch create switches with positions.",
            items: {
              type: "object",
              properties: {
                x: { type: "number" },
                y: { type: "number" }
              },
              required: ["x", "y"]
            }
          }
        },
        required: ["nodes"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "create_controller",
      description: "Create a controller (default or remote) in batch.",
      parameters: {
        type: "object",
        properties: {
          nodes: {
            type: "array",
            description: "Batch create controllers.",
            items: {
              type: "object",
              properties: {
                x: { type: "number" },
                y: { type: "number" },
                remote: { type: "boolean", description: "True for remote controller." },
                ip: { type: "string", description: "Remote controller IP." },
                port: { type: "number", description: "Remote controller port." }
              },
              required: ["x", "y"]
            }
          }
        },
        required: ["nodes"]
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
      name: "associate_switch",
      description: "Associate a switch to a controller.",
      parameters: {
        type: "object",
        properties: {
          switch_id: { type: "string", description: "Switch id, e.g. s1" },
          controller_id: { type: "string", description: "Controller id, e.g. c1" }
        },
        required: ["switch_id", "controller_id"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "get_topology",
      description: "Get current topology nodes and edges as JSON.",
      parameters: {
        type: "object",
        properties: {}
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
  async create_controller(args = {}) {
    return handlers.createController?.(args);
  },
  async create_link(args = {}) {
    return handlers.createLink?.(args);
  },
  async associate_switch(args = {}) {
    return handlers.associateSwitch?.(args);
  },
  async get_topology(args = {}) {
    return handlers.getTopology?.(args);
  },
  async run_command(args = {}) {
    return handlers.runCommand?.(args);
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
