"use client"

import { usePathname } from "next/navigation"
import { LayoutDashboard, Users, Package, Tags, Terminal, ChevronRight, ChevronDown, LucideIcon } from "lucide-react"
import React, { useState } from "react"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
  // SidebarFooter was imported but will be removed
} from "@/components/ui/sidebar"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface NavItem {
  title: string
  url?: string // Optional for parent items that only toggle
  icon: LucideIcon
  subItems?: NavItem[]
}

const items: NavItem[] = [
  {
    title: "Dashboard",
    url: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Categories",
    url: "/dashboard/categories",
    icon: Tags,
  },
  {
    title: "Products",
    url: "/dashboard/products",
    icon: Package,
  },
  {
    title: "Suppliers",
    url: "/dashboard/suppliers",
    icon: Users,
  },
  {
    title: "SQL Console",
    url: "/dashboard/sql-console",
    icon: Terminal,
  },
]

export function AppSidebar() {
  const pathname = usePathname()
  const { state } = useSidebar()
  const [openSubmenus, setOpenSubmenus] = useState<Record<string, boolean>>({})

  const toggleSubmenu = (title: string) => {
    setOpenSubmenus((prev) => ({ ...prev, [title]: !prev[title] }))
  }

  const isItemActive = (itemUrl?: string): boolean => {
    if (!itemUrl) return false
    if (itemUrl === '/dashboard' && pathname !== '/dashboard') {
      return false
    }
    return pathname.startsWith(itemUrl) && (pathname === itemUrl || pathname.charAt(itemUrl.length) === '/')
  }

  const isParentActive = (item: NavItem): boolean => {
    if (!item.subItems) return false
    return item.subItems.some(subItem => isItemActive(subItem.url))
  }

  return (
    <Sidebar collapsible="icon" variant="floating" className="rounded-xl"> {/* Changed variant and added rounded-xl */}
      <SidebarContent className="flex flex-col">
        <div className="grow">
          <SidebarGroup>
            <SidebarGroupLabel className="px-2 py-1 text-xl font-bold mb-6">PesapalDB</SidebarGroupLabel>
            {/* <SidebarGroupLabel className="px-2 py-1 text-xs font-semibold uppercase text-muted-foreground tracking-wider">Dashboards</SidebarGroupLabel> */}
            <SidebarGroupContent>
              <SidebarMenu>
                {items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    {item.subItems ? (
                      <>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <SidebarMenuButton
                              onClick={() => toggleSubmenu(item.title)}
                              isActive={isParentActive(item) || (item.url ? isItemActive(item.url) : false)}
                              className={`flex w-full items-center justify-between ${state === "collapsed" ? "justify-center" : ""}`}
                            >
                              <div className={`flex items-center ${state === "expanded" ? "gap-2" : "justify-center w-full"}`}>
                                <item.icon className="h-4 w-4" />
                                {state === "expanded" && <span className="text-sm">{item.title}</span>}
                              </div>
                              {state === "expanded" && (
                                openSubmenus[item.title] ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
                              )}
                            </SidebarMenuButton>
                          </TooltipTrigger>
                          {state === "collapsed" && (
                            <TooltipContent side="right"><p>{item.title}</p></TooltipContent>
                          )}
                        </Tooltip>
                        {state === "expanded" && openSubmenus[item.title] && (
                          <SidebarMenu className="pl-6 pt-1">
                            {item.subItems.map((subItem) => (
                              <SidebarMenuItem key={subItem.title}>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <SidebarMenuButton
                                      asChild
                                      isActive={isItemActive(subItem.url)}
                                    >
                                      <a href={subItem.url} className="flex items-center gap-2 text-sm">
                                        {subItem.title}
                                      </a>
                                    </SidebarMenuButton>
                                  </TooltipTrigger>
                                </Tooltip>
                              </SidebarMenuItem>
                            ))}
                          </SidebarMenu>
                        )}
                      </>
                    ) : (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <SidebarMenuButton
                            asChild
                            isActive={isItemActive(item.url)}
                            className={state === "collapsed" ? "justify-center" : ""}
                          >
                            <a href={item.url} className={`flex items-center ${state === "expanded" ? "gap-2" : "justify-center w-full"}`}>
                              <item.icon className="h-4 w-4" />
                              <span className={`text-sm ${state === "expanded" ? "opacity-100" : "opacity-0 w-0 hidden"}`}>{item.title}</span>
                            </a>
                          </SidebarMenuButton>
                        </TooltipTrigger>
                        {state === "collapsed" && (
                          <TooltipContent side="right"><p>{item.title}</p></TooltipContent>
                        )}
                      </Tooltip>
                    )}
                  </SidebarMenuItem>
                ))}

              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </div>
        {/* SidebarFooter removed */}
      </SidebarContent>
    </Sidebar>
  )
}