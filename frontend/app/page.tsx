'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api, type DatabaseStats, type TableInfo } from '@/lib/api';
import { Database, Table, HardDrive, Clock, Terminal, Package, Tags, Users } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [statsData, tablesData] = await Promise.all([
          api.getStats(),
          api.getTables(),
        ]);
        setStats(statsData);
        setTables(tablesData.tables);
      } catch (err) {
        setError('Failed to connect to database. Make sure the API is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const quickActions = [
    { name: 'Products', href: '/products', icon: Package, color: 'from-blue-500 to-cyan-400' },
    { name: 'Categories', href: '/categories', icon: Tags, color: 'from-purple-500 to-pink-400' },
    { name: 'Suppliers', href: '/suppliers', icon: Users, color: 'from-orange-500 to-yellow-400' },
    { name: 'SQL Console', href: '/sql-console', icon: Terminal, color: 'from-emerald-500 to-teal-400' },
  ];

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error}</p>
        <Button onClick={() => window.location.reload()}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="mt-1 text-muted-foreground">Welcome to PesapalDB Inventory Management</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="glass">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Tables</CardTitle>
            <Table className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.table_count || 0}</div>
            <p className="text-xs text-muted-foreground">Database tables</p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats ? (stats.total_size_bytes / 1024).toFixed(1) : 0} KB
            </div>
            <p className="text-xs text-muted-foreground">Total size</p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Rows</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tables.reduce((sum, t) => sum + t.rows, 0)}
            </div>
            <p className="text-xs text-muted-foreground">Across all tables</p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Last Modified</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.last_modified ? new Date(stats.last_modified).toLocaleDateString() : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">Database activity</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Quick Actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => (
            <Link key={action.href} href={action.href}>
              <Card className="group glass cursor-pointer transition-all hover:scale-[1.02]">
                <CardContent className="flex items-center gap-4 p-6">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br ${action.color}`}>
                    <action.icon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <p className="font-medium">{action.name}</p>
                    <p className="text-sm text-muted-foreground">Manage data</p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Tables Overview */}
      {tables.length > 0 && (
        <div>
          <h2 className="mb-4 text-xl font-semibold">Tables Overview</h2>
          <Card className="glass overflow-hidden">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Name</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Columns</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Rows</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tables.map((table) => (
                      <tr key={table.name} className="border-b border-white/5 hover:bg-white/5">
                        <td className="px-6 py-4 font-medium">{table.name}</td>
                        <td className="px-6 py-4 text-muted-foreground">{table.columns}</td>
                        <td className="px-6 py-4 text-muted-foreground">{table.rows}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
