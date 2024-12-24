import {
  LayoutDashboard,
  FileArchiveIcon,
  Building2,
  GraduationCap,
  Settings,
  Users,
  BookOpen,
  Receipt,
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
    title: "Programs",
    href: "/programs",
    icon: BookOpen,
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
    title: "Billings",
    href: "/billings",
    icon: Receipt,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
] 