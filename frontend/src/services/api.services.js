import {servicesAxiosInstance} from "./config";

const getServerStatus = async () => {
  return await servicesAxiosInstance.get("/");
};

const getAPIServerStatus = async () => {
  return await servicesAxiosInstance.get("/api/v1/")
};
export { 
    getServerStatus,
    getAPIServerStatus
}