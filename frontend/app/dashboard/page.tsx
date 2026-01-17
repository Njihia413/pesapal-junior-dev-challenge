'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api, type DatabaseStats, type TableInfo } from '@/lib/api';
import { Database, Table, HardDrive, Clock, Terminal, Package, Tags, Users } from 'lucide-react';
import Link from 'next/link';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface Product {
  id: number;
  name: string;
  sku: string;
  category_id: number | null;
  price: number;
  quantity: number;
}

interface Category {
  id: number;
  name: string;
  description?: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
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

        // Fetch products and categories for charts
        try {
          const productsResult = await api.getTableRows('products');
          if (productsResult.success) {
            setProducts(productsResult.rows as unknown as Product[]);
          }
        } catch {
          // Products table might not exist
        }

        try {
          const categoriesResult = await api.getTableRows('categories');
          if (categoriesResult.success) {
            setCategories(categoriesResult.rows as unknown as Category[]);
          }
        } catch {
          // Categories table might not exist
        }
      } catch (err) {
        setError('Failed to connect to database. Make sure the API is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Bar chart data: Inventory value by product (price * quantity)
  const inventoryValueData = useMemo(() => {
    return products.map((product) => ({
      name: product.name.length > 12 ? product.name.substring(0, 12) + '...' : product.name,
      value: product.price * product.quantity,
      price: product.price,
      quantity: product.quantity,
    })).sort((a, b) => b.value - a.value).slice(0, 8);
  }, [products]);

  // Line chart data: Products per category
  const categoryProductsData = useMemo(() => {
    const categoryMap = new Map<number, string>();
    categories.forEach(cat => categoryMap.set(cat.id, cat.name));

    const countByCategory: Record<string, { count: number; totalValue: number }> = {};
    
    products.forEach(product => {
      const categoryName = product.category_id 
        ? (categoryMap.get(product.category_id) || `Category ${product.category_id}`)
        : 'Uncategorized';
      
      if (!countByCategory[categoryName]) {
        countByCategory[categoryName] = { count: 0, totalValue: 0 };
      }
      countByCategory[categoryName].count += 1;
      countByCategory[categoryName].totalValue += product.price * product.quantity;
    });

    return Object.entries(countByCategory).map(([name, data]) => ({
      name: name.length > 10 ? name.substring(0, 10) + '...' : name,
      products: data.count,
      value: data.totalValue,
    }));
  }, [products, categories]);

  const quickActions = [
    { name: 'Products', href: '/dashboard/products', icon: Package },
    { name: 'Categories', href: '/dashboard/categories', icon: Tags },
    { name: 'Suppliers', href: '/dashboard/suppliers', icon: Users },
    { name: 'SQL Console', href: '/dashboard/sql-console', icon: Terminal },
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
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-linear-to-t from-(--overview-card-gradient-from) to-(--overview-card-gradient-to)">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Tables</CardTitle>
            <Table className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stats?.table_count || 0}</div>
            <p className="text-xs text-muted-foreground">Database tables</p>
          </CardContent>
        </Card>

        <Card className="bg-linear-to-t from-(--overview-card-gradient-from) to-(--overview-card-gradient-to)">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Storage Used</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {stats ? (stats.total_size_bytes / 1024).toFixed(1) : 0} KB
            </div>
            <p className="text-xs text-muted-foreground">Total size</p>
          </CardContent>
        </Card>

        <Card className="bg-linear-to-t from-(--overview-card-gradient-from) to-(--overview-card-gradient-to)">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Rows</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {tables.reduce((sum, t) => sum + t.rows, 0)}
            </div>
            <p className="text-xs text-muted-foreground">Across all tables</p>
          </CardContent>
        </Card>

        <Card className="bg-linear-to-t from-(--overview-card-gradient-from) to-(--overview-card-gradient-to)">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Last Modified</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {stats?.last_modified ? new Date(stats.last_modified).toLocaleDateString() : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">Database activity</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Quick Actions</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => (
            <Link key={action.href} href={action.href}>
              <Card className="group bg-linear-to-t from-(--overview-card-gradient-from) to-(--overview-card-gradient-to) cursor-pointer transition-all hover:scale-[1.02]">
                <CardContent className="flex items-center gap-4 p-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary">
                    <action.icon className="h-6 w-6 text-primary-foreground" />
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

      {/* Charts Section */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Bar Chart - Inventory Value by Product */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Inventory Value by Product</CardTitle>
            <p className="text-sm text-muted-foreground">Top products by total value (price × quantity)</p>
          </CardHeader>
          <CardContent>
            {inventoryValueData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={inventoryValueData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis 
                    tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                    tickFormatter={(value) => `Kshs${value}`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--card)', 
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                    }}
                    formatter={(value) => [`Kshs${Number(value).toFixed(2)}`, 'Total Value']}
                  />
                  <Bar 
                    dataKey="value" 
                    fill="var(--primary)" 
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[300px] items-center justify-center text-muted-foreground">
                No product data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Line Chart - Products per Category */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Products by Category</CardTitle>
            <p className="text-sm text-muted-foreground">Distribution of products across categories</p>
          </CardHeader>
          <CardContent>
            {categoryProductsData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={categoryProductsData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis 
                    tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--card)', 
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="products" 
                    stroke="var(--primary)" 
                    strokeWidth={3}
                    dot={{ fill: 'var(--primary)', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 8 }}
                    name="Products"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="var(--chart-3)" 
                    strokeWidth={2}
                    dot={{ fill: 'var(--chart-3)', strokeWidth: 2, r: 4 }}
                    name="Total Value (Kshs)"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[300px] items-center justify-center text-muted-foreground">
                No category data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
