/* eslint-disable @typescript-eslint/ban-ts-comment */
import NextAuth from "next-auth"
import { authConfig } from "./auth.config"

// @ts-ignore
export const { auth, handlers, signIn, signOut } = NextAuth({
  ...authConfig,
})