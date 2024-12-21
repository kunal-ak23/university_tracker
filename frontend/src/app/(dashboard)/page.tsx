export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <h1 className="text-4xl font-bold">University Course Management</h1>
      <p className="mt-4 text-lg text-muted-foreground">
        Manage your university courses, contracts, and payments
      </p>
      <div className="mt-8 flex gap-4">
        <a
          href="/login"
          className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
        >
          Login
        </a>
        <a
          href="/register"
          className="rounded-md bg-secondary px-4 py-2 text-secondary-foreground hover:bg-secondary/90"
        >
          Register
        </a>
      </div>
    </div>
  )
} 