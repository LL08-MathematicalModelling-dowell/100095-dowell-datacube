import { prisma } from "@/prisma/client";
import { compare } from "bcryptjs";
import NextAuth, { AuthError, NextAuthConfig } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
// import GitHubProvider from "next-auth/providers/github";
// import GoogleProvider from "next-auth/providers/google";
import { PrismaAdapter } from "@auth/prisma-adapter";

export const authOptions: NextAuthConfig = {
  adapter: PrismaAdapter(prisma),
  providers: [
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email", required: true },
        password: { label: "Password", type: "password", required: true },
      },
      authorize: async (credentials) => {
        try {
          let user = null;
          if (credentials && credentials.email && credentials.password) {
            user = await prisma.user.findUnique({
              where: { email: credentials.email as string },
            });
          }

          if (!user) {
            throw new AuthError("Invalid email or password");
          }
          const isValid = await compare(
            credentials.password as string,
            user.hashedPassword!
          );

          if (!isValid) {
            throw new AuthError("Invalid email or password");
          }

          // return user object without hashedPassword
          const { id, name, email, image } = user;

          return { id, name, email, image };
        } catch {
          return null;
        }
      },
    }),
  ],

  // custom pages (optional)
  pages: {
    signIn: "/auth/signin",
    error: "/auth/error",
  },

  session: {
    strategy: "jwt",
  },

  // make sure this matches your public URL:
  trustHost: true,
};

// Build a handler function from NextAuth, then wire it up to GET/POST
export const { auth, handlers, signIn, signOut } = NextAuth(authOptions);
