'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { navItems } from '@/config/nav';
import { Database } from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 hidden h-screen w-64 border-r border-white/10 bg-sidebar/60 backdrop-blur-xl md:block">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-white/10 px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-linear-to-br from-indigo-500 to-cyan-400">
          <Database className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="bg-linear-to-r from-indigo-400 to-cyan-400 bg-clip-text text-lg font-bold text-transparent">
            PesapalDB
          </h1>
          <p className="text-xs text-zinc-500">Inventory Manager</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="space-y-1 p-4">
        <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Navigation
        </p>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
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

      {/* Status */}
      <div className="absolute bottom-0 left-0 right-0 border-t border-white/10 p-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
          Database Connected
        </div>
        <p className="mt-1 text-xs text-muted-foreground/60">PesapalDB v0.1.0</p>
      </div>
    </aside>
  );
}
