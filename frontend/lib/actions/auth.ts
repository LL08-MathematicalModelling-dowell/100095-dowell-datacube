"use server";

import { signIn, signOut } from "@/auth";

export const githubSignIn = async () => {
  await signIn("github", { redirectTo: "/dashboard" });
};

export const googleSignIn = async () => {
  await signIn("google", { redirectTo: "/dashboard" });
};

export const credentialLogin = async (email: string, password: string) => {
  await signIn("credentials", {
    email,
    password,
    redirectTo: "/dashboard",
  });
}

export const logout = async () => {
  await signOut({ redirectTo: "/" });
};
