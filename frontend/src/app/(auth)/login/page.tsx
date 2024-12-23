import { auth } from "@/auth"
import { redirect } from "next/navigation"
import { LoginForm } from "@/components/forms/auth/login-form"

const LoginPage = async () => {
  const session = await auth();
  console.log(session);

  if (session) {
    redirect("/contracts")
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
        <div className="flex flex-col space-y-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome back
          </h1>
          <p className="text-sm text-muted-foreground">
            Enter your credentials to continue
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  )
}

export default LoginPage;