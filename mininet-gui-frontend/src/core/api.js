import axios from 'axios';

export const deployHost = async (host) => {
  try {
    console.log(host)
    const response = await axios.post('http://localhost:8000/api/mininet/host', JSON.stringify(host) ,{ headers: { "Access-Control-Allow-Origin": "*", 'Content-Type': 'application/json'}});
    return response.status === 200;
  } catch (error) {
    console.error(error);
    return false;
  }
};


export const getNodes = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/mininet/nodes' ,{ headers: { "Access-Control-Allow-Origin": "*", 'Accept': 'application/json'}});
    console.log(response.data)
    // return JSON.parse(response.data);
    return response.data;
  } catch (error) {
    console.error(error);
    return false;
  }
};

export const getEdges = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/mininet/links' ,{ headers: { "Access-Control-Allow-Origin": "*", 'Accept': 'application/json'}});
    console.log(response.data)
    // return JSON.parse(response.data);
    return response.data;
  } catch (error) {
    console.error(error);
    return false;
  }
};
