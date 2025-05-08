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
  const result = await signIn("credentials", {
    email,
    password,
    redirect: false,
  });

  console.log(
    "<<<<<<<<<<<<<<<<<<<<  Credential login result: >>>>>>>>>>>>>>>>>>>>>>    ",
    result
  ); // Log the result for debugging

  if (result) {
    return {
      status: "success",
      ok: true,
      error: null,
    };
  } else {
    return {
      status: "error",
      ok: false,
      error: "Invalid email or password",
    };
  }
};

export const logout = async () => {
  await signOut({ redirectTo: "/" });
};
