import axios from 'axios';

export const deployNode = async (node) => {
  try {
    console.log(node)
    const response = await axios.post('http://localhost:8000/api/nodes', JSON.stringify(node) ,{ headers: { "Access-Control-Allow-Origin": "*", 'Content-Type': 'application/json'}});
    return response.status === 200;
  } catch (error) {
    console.error(error);
    return false;
  }
};


export const getNodes = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/nodes' ,{ headers: { "Access-Control-Allow-Origin": "*", 'Accept': 'application/json'}});
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
    const response = await axios.get('http://localhost:8000/api/edges' ,{ headers: { "Access-Control-Allow-Origin": "*", 'Accept': 'application/json'}});
    return JSON.parse(response.data);
  } catch (error) {
    console.error(error);
    return false;
  }
};
