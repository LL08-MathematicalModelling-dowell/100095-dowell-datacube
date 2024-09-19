import axios from "axios";

// comment the localhost baseURL before pushing
const servicesAxiosInstance = axios.create({
    baseURL: "http://127.0.0.1:8001"
});

export {
  servicesAxiosInstance
}