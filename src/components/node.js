let nextNodeId = 1;

const generateNodeId = () => {
  return nextNodeId++;
};
const generateNodeIp = (nodeId) => {
  return `192.168.${nodeId++}.1`;
};
const generateNodeMac = (nodeId) => {
  return `00:00:00:00:00:${nodeId++}`;
};

export const createNodeObject = () => {
  // Generate unique default values for the node
  const nodeId = generateNodeId();
  const nodeLabel = `Node ${nodeId}`;
  const nodeIp = generateNodeIp(nodeId);
  const nodeMac = generateNodeMac(nodeId);
  // Create the node object
  return {
    node_id: nodeId,
    label: nodeLabel,
    ip: nodeIp,
    mac: nodeMac
  };
};

