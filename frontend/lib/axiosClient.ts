import axios from "axios";

// const baseURL = "https://datacube.uxlivinglab.online/api";
// const baseURL = "http://127.0.0.1:8000/api";
const baseURL = "/api";

const axiosClient = axios.create({
  baseURL: baseURL,
  headers: {
    "Content-Type": "application/json",
    "API-KEY": "datacube",
  },
});

export default axiosClient;
