/* eslint-disable @typescript-eslint/ban-ts-comment */
import { getSession } from "next-auth/react";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export const apiClient = {
  async fetch(endpoint: string, options: RequestInit = {}) {
    const session = await getSession();
    
    const headers = {
      "Content-Type": "application/json",
      // @ts-ignore
      ...(session?.accessToken
        // @ts-ignore
        ? { Authorization: `Bearer ${session.accessToken}` }
        : {}),
      ...options.headers,
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    if (!!response) {
      return await response.json()
    }
    return null
  },

  async register(userData: {
    username: string;
    email: string;
    password: string;
    password2: string;
    role: string;
    phone_number: string;
  }) {
    return this.fetch("/auth/register/", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  },

  async getUserProfile() {
    return this.fetch("/auth/me/");
  },
}; 