import axios from "axios";

const baseUrl = "http://localhost:8080";

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

export const deleteLink = async (linkId) => {
  try {
    console.log("sending deleteLink for edge: ", linkId);
    const response = await axios.delete(
      baseUrl + `/api/mininet/delete_link/${linkId}`,
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

export const getEdges = async () => {
  return await sendGet(baseUrl + "/api/mininet/links");
};

export const isNetworkStarted = async () => {
  return await sendGet(baseUrl + "/api/mininet/start");
};

export const getNodeStats = async (nodeId) => {
  return await sendGet(baseUrl + `/api/mininet/stats/${nodeId}`);
};
