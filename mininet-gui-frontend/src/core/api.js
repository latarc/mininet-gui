import axios from "axios";

const baseUrl = import.meta.env.VITE_BACKEND_URL;

export const deployHost = async (host) => {
  try {
    console.log(host);
    const response = await axios.post(
      baseUrl + "/api/mininet/hosts",
      JSON.stringify(host),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};

export const deploySwitch = async (sw) => {
  try {
    console.log(sw);
    const response = await axios.post(
      baseUrl + "/api/mininet/switches",
      JSON.stringify(sw),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};

export const deployController = async (ctl) => {
  try {
    console.log(ctl);
    const response = await axios.post(
      baseUrl + "/api/mininet/controllers",
      JSON.stringify(ctl),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    if (response.status === 200)
      return response.data;
    throw new Error("Error deploying controller in mininet");
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const deployNat = async (nat) => {
  try {
    console.log(nat);
    const response = await axios.post(
      baseUrl + "/api/mininet/nats",
      JSON.stringify(nat),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};

export const deployRouter = async (router) => {
  try {
    console.log(router);
    const response = await axios.post(
      baseUrl + "/api/mininet/routers",
      JSON.stringify(router),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};
export const getBackendVersion = async () => {
  try {
    const root = baseUrl?.endsWith("/api") ? baseUrl : `${baseUrl}/api`;
    const response = await axios.get(`${root}/version`);
    return response.data || null;
  } catch (error) {
    console.warn("Failed to fetch backend version", error);
    return null;
  }
};

export const getRyuApps = async () => {
  try {
    const root = baseUrl?.endsWith("/api") ? baseUrl : `${baseUrl}/api`;
    const response = await axios.get(`${root}/ryu/apps`);
    return response.data?.apps || [];
  } catch (error) {
    console.warn("Failed to fetch ryu apps", error);
    return [];
  }
};

export const getHealthStatus = async () => {
  try {
    const root = baseUrl?.endsWith("/api") ? baseUrl : `${baseUrl}/api`;
    const response = await axios.get(`${root}/health`);
    return response.data || null;
  } catch (error) {
    console.warn("Failed to fetch health status", error);
    return null;
  }
};

export const deployLink = async (src, dst, options = null) => {
  try {
    console.log(src, dst, options);
    const payload = options ? { src, dst, options } : [src, dst];
    const response = await axios.post(
      baseUrl + "/api/mininet/links",
      JSON.stringify(payload),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    if (response.status === 200)
      return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const assocSwitch = async (sw, ctl) => {
  try {
    console.log("assoc",sw, ctl);
    const response = await axios.post(
      baseUrl + `/api/mininet/associate_switch`,
      JSON.stringify({"switch": sw, "controller": ctl}),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    if (response.status === 200)
      return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
  }
  throw error;
};

export const deleteNode = async (nodeId) => {
  try {
    const response = await axios.delete(
      baseUrl + `/api/mininet/delete_node/${nodeId}`,
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const deleteLink = async (srcId, dstId) => {
  try {
    console.log("sending deleteLink for edge: ", srcId, dstId);
    const response = await axios.delete(
      baseUrl + `/api/mininet/delete_link/${srcId}/${dstId}`,
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const getInterfaces = async () => {
  try {
    const response = await axios.get(baseUrl + "/api/mininet/interfaces", {
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const getSnifferState = async () => {
  try {
    const response = await axios.get(baseUrl + "/api/mininet/sniffer/state", {
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const getSnifferHistory = async () => {
  try {
    const response = await axios.get(baseUrl + "/api/mininet/sniffer/history", {
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const startSniffer = async () => {
  try {
    const response = await axios.post(baseUrl + "/api/mininet/sniffer/start", null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const stopSniffer = async () => {
  try {
    const response = await axios.post(baseUrl + "/api/mininet/sniffer/stop", null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const exportSnifferPcap = async () => {
  try {
    const response = await axios.get(baseUrl + "/api/mininet/sniffer/export", {
      responseType: "blob",
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const removeAssociation = async (srcId, dstId) => {
  try {
    console.log("sending removeAssociation for edge: ", srcId, dstId);
    const response = await axios.delete(
      baseUrl + `/api/mininet/remove_association/${srcId}/${dstId}`,
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const updateNodePosition = async (nodeId, position) => {
  try {
    const response = await axios.post(
      baseUrl + `/api/mininet/node_position`,
      JSON.stringify({"node_id": nodeId, "position": position}),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const requestStartNetwork = async () => {
  try {
    const response = await axios.post(
      baseUrl + "/api/mininet/start",
      null,
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};

export const requestStopNetwork = async () => {
  try {
    const response = await axios.post(
      baseUrl + "/api/mininet/stop",
      null,
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};

export const requestResetNetwork = async () => {
  try {
    const response = await axios.post(
      baseUrl + "/api/mininet/reset",
      null,
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};

export const requestExportNetwork = async () => {
  try {
    const response = await axios.get(baseUrl + "/api/mininet/export_json", {
      responseType: "blob",
    });

    if (response.status === 200) {
      const blob = new Blob([response.data], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = "network_export.json";
      document.body.appendChild(a);
      a.click(); 
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
  }
};

export const requestImportNetwork = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await axios.post(baseUrl + "/api/mininet/import_json", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    });

    if (response.status === 200) {
      return response.data;
    } else {
      throw new Error("Import failed.");
    }
  } catch (error) {
    throw new Error(error.response ? error.response.data.detail : "Network Error");
  }
};

export const requestExportMininetScript = async () => {
  try {
    const response = await axios.get(baseUrl + "/api/mininet/export_script", {
      responseType: "blob",
    });

    if (response.status === 200) {
      const blob = new Blob([response.data], { type: "text/x-python" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "network_export.py";
      document.body.appendChild(a);
      a.click(); 
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
  }
};

export const requestRunPingall = async () => {
  try {
    const response = await axios.post(
      baseUrl + "/api/mininet/pingall",
      null,
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.data;
  } catch (error) {
    if (error.response?.status === 409) {
      return { running: true };
    }
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};

export const runIperf = async (payload) => {
  try {
    const response = await axios.post(
      baseUrl + "/api/mininet/iperf",
      JSON.stringify(payload),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.data || null;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return null;
  }
};

export const sendGet = async (url) => {
  try {
    const response = await axios.get(url, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        Accept: "application/json",
      },
    });
    console.log("response.data");
    console.log(response.data);
    // return JSON.parse(response.data);
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }
};

export const getHosts = async () => {
  return await sendGet(baseUrl + "/api/mininet/hosts");
};

export const updateHost = async (hostId, payload) => {
  try {
    const response = await axios.patch(
      baseUrl + `/api/mininet/hosts/${hostId}`,
      JSON.stringify(payload),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.data || null;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return null;
  }
};

export const getSwitches = async () => {
  return await sendGet(baseUrl + "/api/mininet/switches");
};

export const getControllers = async () => {
  return await sendGet(baseUrl + "/api/mininet/controllers");
};

export const getNats = async () => {
  return await sendGet(baseUrl + "/api/mininet/nats");
};

export const getRouters = async () => {
  return await sendGet(baseUrl + "/api/mininet/routers");
};

export const getEdges = async () => {
  return await sendGet(baseUrl + "/api/mininet/links");
};

export const isNetworkStarted = async () => {
  return await sendGet(baseUrl + "/api/mininet/start");
};

export const getNodeStats = async (nodeId) => {
  return await sendGet(baseUrl + `/api/mininet/stats/${nodeId}`);
};

export const getAddressingPlan = async () => {
  try {
    const response = await axios.get(baseUrl + "/api/mininet/addressing_plan", {
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const listFlows = async (switchId) => {
  try {
    const response = await axios.get(baseUrl + `/api/mininet/flows/${switchId}`, {
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const addFlow = async (flow) => {
  try {
    const response = await axios.post(
      baseUrl + "/api/mininet/flows",
      JSON.stringify(flow),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const deleteFlows = async (flow) => {
  try {
    const response = await axios.delete(baseUrl + "/api/mininet/flows", {
      data: flow,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};

export const deleteFlowById = async (switchId, flowId) => {
  try {
    const response = await axios.delete(
      baseUrl + `/api/mininet/flows/${switchId}/${flowId}`,
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
        },
      },
    );
    return response.data;
  } catch (error) {
    alert(error.response ? error.response.data["detail"] : "Network Error");
    throw error;
  }
};
