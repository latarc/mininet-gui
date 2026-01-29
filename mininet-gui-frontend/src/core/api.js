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

export const deployLink = async (src, dst) => {
  try {
    console.log(src, dst);
    const response = await axios.post(
      baseUrl + "/api/mininet/links",
      JSON.stringify([src, dst]),
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
    alert(error.response ? error.response.data["detail"] : "Network Error");
    return false;
  }i
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

export const getSwitches = async () => {
  return await sendGet(baseUrl + "/api/mininet/switches");
};

export const getControllers = async () => {
  return await sendGet(baseUrl + "/api/mininet/controllers");
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
