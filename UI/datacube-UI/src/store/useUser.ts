import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchProfile,
  PROFILE_QUERY_KEY,
  type UserProfile,
} from "../services/profile";
import useAuthStore from "./authStore";

const useUser = () => {
  const navigate = useNavigate();
  const { accessToken, logout, setFirstName } = useAuthStore();

  const { data, isLoading, error, isFetching, refetch } = useQuery<UserProfile>({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchProfile,
    enabled: !!accessToken,
    retry: false,
    staleTime: 1000 * 60 * 5,
  });

  useEffect(() => {
    if (data?.firstName) {
      setFirstName(data.firstName);
    }
    if (error) {
      logout();
      navigate("/login", { replace: true });
    }
  }, [data, error, logout, navigate, setFirstName]);

  return {
    user: data ?? null,
    isLoading: isLoading && !!accessToken,
    isFetching,
    error,
    refetch,
  };
};

export default useUser;
