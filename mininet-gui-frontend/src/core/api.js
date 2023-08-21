import axios from "axios";

export const deployHost = async (host) => {
  try {
    console.log(host);
    const response = await axios.post(
      "http://mininet-gui-backend:8000/api/mininet/hosts",
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
    alert(error.response.data["detail"]);
    return false;
  }
};

export const deploySwitch = async (sw) => {
  try {
    console.log(sw);
    const response = await axios.post(
      "http://mininet-gui-backend:8000/api/mininet/switches",
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
    alert(error.response.data["detail"]);
    return false;
  }
};

export const deployLink = async (src, dst) => {
  try {
    console.log(src, dst);
    const response = await axios.post(
      "http://mininet-gui-backend:8000/api/mininet/links",
      JSON.stringify([src, dst]),
      {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Content-Type": "application/json",
        },
      },
    );
    return response.status === 200;
  } catch (error) {
    alert(error.response.data["detail"]);
    return false;
  }
};

export const requestStartNetwork = async () => {
  try {
    const response = await axios.post(
      "http://mininet-gui-backend:8000/api/mininet/start",
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
    alert(error.response.data["detail"]);
    return false;
  }
};

export const requestRunPingall = async () => {
  try {
    const response = await axios.post(
      "http://mininet-gui-backend:8000/api/mininet/pingall",
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
    alert(error.response.data["detail"]);
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
    alert(error.response.data["detail"]);
    return false;
  }
};

export const getHosts = async () => {
  return await sendGet("http://mininet-gui-backend:8000/api/mininet/hosts");
};

export const getSwitches = async () => {
  return await sendGet("http://mininet-gui-backend:8000/api/mininet/switches");
};

export const getEdges = async () => {
  return await sendGet("http://mininet-gui-backend:8000/api/mininet/links");
};

export const isNetworkStarted = async () => {
  return await sendGet("http://mininet-gui-backend:8000/api/mininet/start");
};
