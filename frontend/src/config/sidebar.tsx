import {
  LayoutDashboard,
  FileArchiveIcon,
  Building2,
  GraduationCap,
  Settings,
  Users,
} from "lucide-react"

export const sidebarConfig = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Contracts",
    href: "/contracts",
    icon: FileArchiveIcon,
  },
  {
    title: "OEMs",
    href: "/oems",
    icon: Building2,
  },
  {
    title: "Universities",
    href: "/universities",
    icon: GraduationCap,
  },
  {
    title: "Batches",
    href: "/batches",
    icon: Users,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
] 