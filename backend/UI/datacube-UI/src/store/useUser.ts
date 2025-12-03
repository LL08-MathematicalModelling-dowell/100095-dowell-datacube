// hooks/useUser.ts
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
  const { accessToken, refreshToken, firstName, updateAccessToken, logout } = useAuthStore();

  const { data, isLoading, error } = useQuery<UserResponse>({
    queryKey: ["user"],
    queryFn: async () => {
      const res = await api.get("/core/profile");
      return res;
    },
    // Only run when we have a token but no firstName yet (e.g. after page refresh)
    enabled: !!accessToken && !firstName,
    retry: false, // api.ts already handles 401 → refresh → retry
    staleTime: 1000 * 60 * 10, // 10 minutes – user data rarely changes
  });

  useEffect(() => {
    if (data && !firstName) {
      // Save firstName to store + localStorage
      useAuthStore.getState().setAuth?.(
        accessToken!,
        refreshToken!,
        data.firstName
      );
    }

    // If the request failed (even after refresh attempts) → session is dead
    if (error) {
      logout();
      navigate("/login", { replace: true });
    }
  }, [data, error, firstName, accessToken, refreshToken, navigate, logout]);

  // Return the most up-to-date user info
  const user = data || (firstName ? { firstName } : null);

  return {
    user,
    isLoading: isLoading && !!accessToken, // don’t show loading if we’re already logged out
    error,
  };
};

export default useUser;


// import { useQuery } from "@tanstack/react-query";
// import { useEffect } from "react";
// import { useNavigate } from "react-router-dom";
// import api from "../services/api";
// import useAuthStore from "../store/authStore";

// interface User {
//   user_id: string;
//   email: string;
//   firstName: string;
//   lastName: string;
// }

// const useUser = () => {
//   const { token, firstName, setAuth, logout } = useAuthStore();
//   const navigate = useNavigate();

//   const { data, isLoading, error } = useQuery<User>({
//     queryKey: ["user"],
//     queryFn: async () => {
//       const response = await api.get("/core/profile");
//       return response;
//     },
//     enabled: !!token && !firstName,
//     retry: 1,
//   });

//   useEffect(() => {
//     if (data && !firstName) {
//       setAuth(token!, data.firstName);
//     } else if (error) {
//       logout();
//       navigate("/login");
//     }
//   }, [data, error, firstName, token, setAuth, logout, navigate]);

//   return { user: data || { firstName: firstName || '' }, isLoading, error };
// };

// export default useUser;