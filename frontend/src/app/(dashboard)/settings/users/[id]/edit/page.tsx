import { notFound } from "next/navigation"
import { UserForm } from "@/components/forms/user/user-form"
import { getUser } from "@/service/api/users"

export default async function EditUserPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  let user;
  try {
    const {id} = await params;
    user = await getUser(Number(id))
  } catch (error) {
    console.error('Error fetching user:', error)
    notFound()
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Edit User</h3>
      <p className="text-sm text-muted-foreground">
        Update user information and permissions.
      </p>
      <UserForm mode="edit" user={user} />
    </div>
  )
} 