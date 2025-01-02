import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { UsersTable } from "@/components/settings/users/users-table"
import { getUsers } from "@/service/api/users"


export default async function UsersPage({
  params
}: {
  params: Promise<{
    page?: string
    search?: string
  }
  >
}) {
  const {page, search} = await params;
  const pageNumber = Number(page) || 1
  const searchString = search || ""
  const response = await getUsers({page: pageNumber, search: searchString})
  const users = response.results;
  const totalPages = Math.ceil(response.count / 10)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Users</h3>
          <p className="text-sm text-muted-foreground">
            Manage user accounts and permissions.
          </p>
        </div>
        <Button onClick={() => window.location.href = "/settings/users/new"}>
          <Plus className="mr-2 h-4 w-4" />
          Add User
        </Button>
      </div>

      <UsersTable 
        users={users}
        currentPage={pageNumber}
        totalPages={totalPages}
        totalCount={response.count}
        hasNextPage={!!response.next}
        hasPreviousPage={!!response.previous}
      />
    </div>
  )
} 