"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { signIn } from "next-auth/react"

const loginFormSchema = z.object({
  username: z.string().email("Must be a valid email"),
  password: z.string().min(1, "Password is required"),
})

type LoginFormValues = z.infer<typeof loginFormSchema>

export function LoginForm() {
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginFormSchema),
    mode: "all",
    reValidateMode: "onChange",
    defaultValues: {
      username: "",
      password: "",
    },
  })

  async function onSubmit(data: LoginFormValues) {
    setIsLoading(true)
    
    try {
      const response = await signIn("credentials", {
        username: data.username,
        password: data.password,
        redirect: false,
      })

      if (response?.error) {
        // Handle server validation errors
        try {
          const errorData = JSON.parse(response.error)
          
          // Set server-side validation errors in the form
          if (typeof errorData === 'object') {
            Object.keys(errorData).forEach((key) => {
              const messages = errorData[key]
              if (Array.isArray(messages)) {
                form.setError(key as keyof LoginFormValues, {
                  type: 'server',
                  message: messages.join(', ')
                })
              } else if (typeof messages === 'string') {
                form.setError(key as keyof LoginFormValues, {
                  type: 'server',
                  message: messages
                })
              }
            })
            
            // Show a toast with the first error message
            const firstError = Object.values(errorData)[0]
            const errorMessage = Array.isArray(firstError) ? firstError[0] : firstError
            
            toast({
              title: "Error",
              description: errorMessage || "Invalid credentials",
              variant: "destructive",
            })
          } else {
            toast({
              title: "Error",
              description: "Invalid credentials",
              variant: "destructive",
            })
          }
        } catch {
          // If error isn't JSON, show it directly
          toast({
            title: "Error",
            description: response.error || "Invalid credentials",
            variant: "destructive",
          })
        }
        return
      }

      if (response?.ok) {
        router.push("/contracts")
        router.refresh()
      }
    } catch (error) {
      console.error("Login error:", error)
      
      // Handle unexpected errors
      if (error instanceof Error) {
        toast({
          title: "Error",
          description: error.message || "Something went wrong",
          variant: "destructive",
        })
      } else {
        toast({
          title: "Error",
          description: "Something went wrong",
          variant: "destructive",
        })
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="Enter your email" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" placeholder="Enter your password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? "Signing in..." : "Sign in"}
        </Button>
      </form>
    </Form>
  )
} 