import { RegisterForm } from "@/components/forms/auth/register-form"

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-8 px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Create an account</h2>
          <p className="text-muted-foreground">Get started with our platform</p>
        </div>
        <RegisterForm />
      </div>
    </div>
  )
} 