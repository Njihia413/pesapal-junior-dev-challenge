'use client';

import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  SidebarProvider,
  SidebarInset,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/app-sidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const userInitials = 'JD';


  return (
    <SidebarProvider>
      <div className="relative flex min-h-screen font-montserrat w-full">
        <AppSidebar />
        <SidebarInset>
          <header className="bg-background/80 sticky top-0 z-30 flex h-14 items-center gap-3 px-4 backdrop-blur-xl lg:h-[60px]">
            <SidebarTrigger className="size-9 p-0 flex items-center justify-center border border-sidebar-border bg-sidebar shadow-xs hover:bg-accent hover:text-accent-foreground dark:hover:bg-input/50 rounded-full" />

            {/* Search Section */}
            <div className="ms-auto lg:ms-0 lg:flex-1">
              <div className="relative hidden max-w-sm flex-1 lg:block">
                <Search className="text-sidebar-foreground/70 absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
                <Input
                  type="search"
                  placeholder="Search..."
                  className="h-9 w-full cursor-pointer rounded-full bg-transparent text-sidebar-foreground placeholder:text-sidebar-foreground/70 pr-4 pl-10 text-sm shadow-xs"
                />
                <div className="absolute top-1/2 right-2 hidden -translate-y-1/2 items-center gap-0.5 rounded-sm bg-zinc-200 p-1 font-mono text-xs font-medium sm:flex dark:bg-neutral-700">
                  <kbd>⌘</kbd>
                  <kbd>K</kbd>
                </div>
              </div>
              <div className="block lg:hidden">
                <Button variant="outline" size="icon" className="size-9 border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50">
                  <Search className="h-4 w-4" />
                  <span className="sr-only">Search</span>
                </Button>
              </div>
            </div>

            {/* Right Aligned Icons */}
            <div className="flex items-center gap-3">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="rounded-xl">
                    <Avatar>
                      <AvatarFallback className="bg-primary text-white">{userInitials}</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
              </DropdownMenu>
            </div>
          </header>
          <main className="p-4 sm:px-6 sm:py-8">
            {children}
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
