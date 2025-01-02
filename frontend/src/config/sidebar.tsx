import {
  LayoutDashboard,
  FileArchiveIcon,
  Building2,
  GraduationCap,
  Settings,
  Users,
  BookOpen,
  Receipt,
  CreditCard,
  FileText,
  Building,
  School,
  Wallet,
} from "lucide-react"

export const sidebarConfig = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "OEM Management",
    icon: Building,
    items: [
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
    ],
  },
  {
    title: "University Management",
    icon: School,
    items: [
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
        title: "Contracts",
        href: "/contracts",
        icon: FileArchiveIcon,
      },
    ],
  },
  {
    title: "Finance",
    icon: Wallet,
    items: [
      {
        title: "Billings",
        href: "/billings",
        icon: Receipt,
      },
      {
        title: "Invoices",
        href: "/invoices",
        icon: FileText,
      },
      {
        title: "Payments",
        href: "/payments",
        icon: CreditCard,
      },
    ],
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
] 