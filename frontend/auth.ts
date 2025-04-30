// app/api/auth/[...nextauth]/route.ts
import NextAuth from "next-auth/next";
import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { PrismaAdapter } from "@next-auth/prisma-adapter";
import { prisma } from "@/prisma/client";
import { compare } from "bcryptjs";

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials.password) {
          return null;
        }

        const user = await prisma.user.findUnique({
          where: { email: credentials.email },
        });
        if (!user || !user.hashedPassword) {
          return null;
        }

        // <-- don’t forget to await
        const isValid = await compare(
          credentials.password,
          user.hashedPassword
        );
        if (!isValid) {
          return null;
        }

        // Return a plain object with at least an id or email
        return {
          id: user.id.toString(),
          email: user.email,
          name: user.name ?? user.email,
        };
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
  secret: process.env.NEXTAUTH_SECRET,
  trustHost: true,
};

// Build a handler function from NextAuth, then wire it up to GET/POST
const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };

// import NextAuth from "next-auth";
// // import GitHubProvider from "next-auth/providers/github";
// // import GoogleProvider from "next-auth/providers/google";
// import CredentialsProvider from "next-auth/providers/credentials";
// import { PrismaAdapter } from "@auth/prisma-adapter";
// import { prisma } from "@/prisma/client";
// import bcrypt from "bcryptjs";
// import { NextAuthConfig } from "next-auth";
// // import { NextAuthOptions } from "next-auth";

// // interface Session {
// //   accessToken?: string;
// //   user: {
// //     id: string;
// //   };
// // }

// // interface Token {
// //   accessToken: string;
// //   id: string;
// // }

// // interface Callbacks {
// //   session(props: {
// //     session: Session;
// //     token: Token;
// //     user: any;
// //   }): Promise<Session>;
// // }

// export const authOptions: NextAuthConfig = {
//   adapter: PrismaAdapter(prisma),
//   trustHost: true,
//   providers: [
//     CredentialsProvider({
//       name: "Credentials",
//       credentials: {
//         email: { label: "Email", type: "email", placeholder: "Email" },
//         password: {
//           label: "Password",
//           type: "password",
//           placeholder: "Password",
//         },
//       },
//       authorize: async (credentials) => {
//         if (credentials && credentials.email && credentials.password) {
//           const user = await prisma.user.findUnique({
//             where: { email: credentials.email },
//           });

//           if (!user) return null;
//           const password = credentials.password;
//           const isValid = bcrypt.compare(password, user.hashedPassword!);
//           if (!isValid) return null;

//           return { id: user.id, name: user.email, email: user.email };
//         }
//         return null;
//       },
//     }),
//     // GitHubProvider({
//     //   clientId: process.env.GITHUB_ID,
//     //   clientSecret: process.env.GITHUB_SECRET,
//     // }),
//     // GoogleProvider({
//     //   clientId: process.env.GOOGLE_CLIENT_ID,
//     //   clientSecret: process.env.GOOGLE_CLIENT_SECRET,
//     // }),
//   ],
//   pages: {
//     signIn: "/auth/signin",
//     error: "/auth/error", // Error code passed in query string as ?error=
//     verifyRequest: "/auth/verify-request", // (used for check email message)
//     newUser: "/auth/signup", // Will disable the new account creation screen
//   },
//   theme: {
//     colorScheme: "dark", // Can be one of: auto | dark | light
//     brandColor: "#000000",
//     // logo: "/logo.png",
//   },
//   session: {
//     strategy: "jwt", // You can use JWT or database sessions based on your needs
//   },
// };

// export const { auth, handlers, signIn, signOut } = NextAuth(authOptions);
