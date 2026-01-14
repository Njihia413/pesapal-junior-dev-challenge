'use client';

import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Menu, Database } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { navItems } from '@/config/nav';
import { useState } from 'react';

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="flex items-center justify-between border-b border-white/10 bg-background/60 p-4 backdrop-blur-md md:hidden">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-400">
          <Database className="h-4 w-4 text-white" />
        </div>
        <span className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text font-bold text-transparent">
          PesapalDB
        </span>
      </div>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="shrink-0">
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle navigation menu</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-[80vw] max-w-[300px] border-r border-white/10 bg-background p-0">
          <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
          {/* Logo */}
          <div className="flex h-16 items-center gap-3 border-b border-white/10 px-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-400">
              <Database className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-lg font-bold text-transparent">
                PesapalDB
              </h1>
              <p className="text-xs text-muted-foreground">Inventory Manager</p>
            </div>
          </div>

          <nav className="flex flex-col gap-1 p-4">
             <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Navigation
            </p>
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary/20 text-primary border-l-2 border-primary'
                      : 'text-muted-foreground hover:bg-white/5 hover:text-white'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </SheetContent>
      </Sheet>
    </div>
  );
}
