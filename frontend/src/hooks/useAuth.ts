"use client"

import { signIn, signOut, useSession } from "next-auth/react";
import { apiClient } from "@/lib/api/apiClient";
import { DEFAULT_REDIRECT_URL } from "@/routes";

export function useAuth() {
  const { data: session, status } = useSession();

  const login = async (username: string, password: string) => {
    return signIn("credentials", {
      username,
      password,
      redirectTo: DEFAULT_REDIRECT_URL,
    });
  };

  const register = async (userData: {
    username: string;
    email: string;
    password: string;
    password2: string;
    role: string;
    phone_number: string;
  }) => {
    return apiClient.register(userData);
  };

  const logout = () => signOut();

  return {
    session,
    status,
    login,
    register,
    logout,
  };
} 