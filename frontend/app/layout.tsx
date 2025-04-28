import type { Metadata } from "next";
import "./globals.css";
import AuthProvider from "@/components/AuthProvider";
import { Provider } from "@/components/ui/provider";
import QueryProvider from "@/components/QueryProvider";

export const metadata: Metadata = {
  title: "DataCube",
  description: "DataCube is a database management platform",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <AuthProvider>
        <body>
          <QueryProvider>
            <Provider>
              {children}
            </Provider>
          </QueryProvider>
        </body>
      </AuthProvider>
    </html>
  );
}
