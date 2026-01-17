import {
  LayoutDashboard,
  Package,
  Tags,
  Users,
  Terminal,
} from 'lucide-react';

export const navItems = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Products', href: '/dashboard/products', icon: Package },
  { name: 'Categories', href: '/dashboard/categories', icon: Tags },
  { name: 'Suppliers', href: '/dashboard/suppliers', icon: Users },
  { name: 'SQL Console', href: '/dashboard/sql-console', icon: Terminal },
];
