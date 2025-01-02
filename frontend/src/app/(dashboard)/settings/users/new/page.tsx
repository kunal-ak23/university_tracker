import { UserForm } from "@/components/forms/user/user-form"

export default function NewUserPage() {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Create User</h3>
      <p className="text-sm text-muted-foreground">
        Add a new user to the system.
      </p>
      <UserForm />
    </div>
  )
} 