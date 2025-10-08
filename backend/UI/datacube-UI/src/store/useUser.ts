import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import useAuthStore from "../store/authStore";

interface User {
  user_id: string;
  email: string;
  firstName: string;
  lastName: string;
}

const useUser = () => {
  const { token, firstName, setAuth, logout } = useAuthStore();
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery<User>({
    queryKey: ["user"],
    queryFn: async () => {
      const response = await api.get("/core/profile");
      return response;
    },
    enabled: !!token && !firstName, // Only fetch if token exists and firstName is null
    retry: 1,
  });

  useEffect(() => {
    if (data && !firstName) {
      setAuth(token!, data.firstName); // Update firstName in store and localStorage
    } else if (error) {
      logout();
      navigate("/login");
    }
  }, [data, error, firstName, token, setAuth, logout, navigate]);

  return { user: data || { firstName }, isLoading, error };
};

export default useUser;
