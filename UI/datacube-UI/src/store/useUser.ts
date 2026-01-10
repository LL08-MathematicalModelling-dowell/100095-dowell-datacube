import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import useAuthStore from "../store/authStore";

interface UserResponse {
  user_id: string;
  email: string;
  firstName: string;
  lastName: string;
}

const useUser = () => {
  const navigate = useNavigate();
  const { accessToken, logout, firstName } = useAuthStore();
  
  const { setAuth } = useAuthStore.getState(); 

  // --- TanStack Query Logic ---
  const { data, isLoading, error } = useQuery<UserResponse>({
    queryKey: ["user"],
    queryFn: async () => {
      const res = await api.get("/core/profile");
      return res;
    },
    enabled: !!accessToken && !firstName,
    retry: false,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });

  useEffect(() => {
    const { setFirstName } = useAuthStore.getState();

    if (data && !firstName) {
      setFirstName(data.firstName); 
    }
    if (error) {
      logout();
      navigate("/login", { replace: true }); 
    }
  }, [data, error, firstName, logout, navigate, setAuth]); 

  const user = data || (firstName ? { firstName } : null);

  return {
    user,
    isLoading: isLoading && !!accessToken, 
    error,
  };
};

export default useUser;