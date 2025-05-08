"use server";

import { signIn, signOut } from "@/auth";
import { redirect } from "next/navigation";

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
  const result = await signIn("credentials", {
    email,
    password,
    redirect: false,
  });


  if (result) {
    redirect("/dashboard"); // Redirect to the dashboard on successful login
  } else {
    throw new Error("Invalid credentials");
  }

  // Handle the case where result is null or undefined
  console.error("Login failed: result is null or undefined");
  throw new Error("Login failed: result is null or undefined");
};

export const logout = async () => {
  await signOut({ redirectTo: "/" });
};
