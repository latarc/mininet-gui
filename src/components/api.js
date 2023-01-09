import axios from 'axios';

export const createNode = async (node) => {
  try {
    console.log(node)
    const response = await axios.post('http://localhost:8000/api/nodes', node ,{ headers: { "Access-Control-Allow-Origin": "*", 'Content-Type': 'application/json'}});
    return response.status === 200;
  } catch (error) {
    console.error(error);
    return false;
  }
};

