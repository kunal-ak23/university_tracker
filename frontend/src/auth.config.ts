/* eslint-disable @typescript-eslint/ban-ts-comment */
import CredentialsProvider from "next-auth/providers/credentials";

export const authConfig = {
    providers: [
        CredentialsProvider({
          name: "Credentials",
          credentials: {
            username: { label: "Email", type: "email" },
            password: { label: "Password", type: "password" },
          },
          // @ts-ignore
          async authorize(credentials) {
            if (!credentials?.username || !credentials?.password) {
              throw new Error("Missing credentials");
            }
    
            try {
              console.log("Attempting login with:", {
                username: credentials.username,
              });
              console.log('API URL:', `${process.env.NEXT_PUBLIC_API_URL}/auth/login/`);
    
              const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/auth/login/`,
                {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    username: credentials.username,
                    password: credentials.password,
                  }),
                }
              );
    
              const data = await response.json();
    
              if (!response.ok) {
                throw new Error(data.message || "Authentication failed");
              }
    
              if (!data.access) {
                throw new Error("No access token received");
              }
    
              // Return user object on successful auth
              const user = {
                id: data.user.id,
                name: `${data.user.first_name} ${data.user.last_name}`.trim() || data.user.email,
                email: data.user.email,
                role: data.role,
                accessToken: data.access,
                refreshToken: data.refresh,
                ...data.user
              };

              return user;
    
            } catch (error) {
              console.error("Auth error:", error);
              // Throw the error to be handled by NextAuth
              throw new Error(error instanceof Error ? error.message : "Authentication failed");
            }
          },
        }),
      ],
      callbacks: {
        // @ts-ignore
        async jwt({ token, user }) {
          if (user) {
            return {
              ...token,
              accessToken: user.accessToken,
              refreshToken: user.refreshToken,
              role: user.role,
              id: user.id,
              first_name: user.first_name,
              last_name: user.last_name,
              email: user.email,
              name: user.name,
            };
          }
          return token;
        },
        // @ts-ignore
        async session({ session, token }) {
          session.accessToken = token.accessToken;
          session.refreshToken = token.refreshToken;
          
          // Make sure user information is passed to the session
          session.user = {
            ...session.user,
            id: token.id,
            role: token.role,
            first_name: token.first_name,
            last_name: token.last_name,
            name: token.name,
            email: token.email,
          };

          return session;
        },
      },
      pages: {
        signIn: '/login',
        signOut: '/login',
        error: '/login', // Error code passed in query string as ?error=
      },
      session: {
        strategy: "jwt",
        maxAge: 30 * 24 * 60 * 60, // 30 days
      },
      debug: true,
      secret: process.env.NEXTAUTH_SECRET,
}