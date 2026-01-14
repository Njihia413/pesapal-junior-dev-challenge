import {
  LayoutDashboard,
  Package,
  Tags,
  Users,
  Terminal,
} from 'lucide-react';

export const navItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Products', href: '/products', icon: Package },
  { name: 'Categories', href: '/categories', icon: Tags },
  { name: 'Suppliers', href: '/suppliers', icon: Users },
  { name: 'SQL Console', href: '/sql-console', icon: Terminal },
];
