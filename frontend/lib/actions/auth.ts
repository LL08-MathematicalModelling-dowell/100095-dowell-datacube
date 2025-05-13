"use server";

import { signIn, signOut } from "@/auth";

export const githubSignIn = async () => {
  await signIn("github", { redirectTo: "/dashboard" });
};

export const googleSignIn = async () => {
  await signIn("google", { redirectTo: "/dashboard" });
};

export const credentialLogin = async ({
  email,
  password,
}: {
  email: string;
  password: string;
}) => {
  return await signIn("credentials", {
    email,
    password,
    redirect: false,
  });
};

export const logout = async () => {
  await signOut({ redirectTo: "/" });
};
