'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { api, type QueryResponse } from '@/lib/api';
import { Play, Trash2, Clock, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';

interface QueryHistoryItem {
  sql: string;
  success: boolean;
  message: string;
  timestamp: Date;
}

export default function SQLConsolePage() {
  const [sql, setSql] = useState('');
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);

  const executeQuery = async () => {
    if (!sql.trim()) {
      toast.error('Please enter a SQL query');
      return;
    }

    setLoading(true);
    try {
      const response = await api.executeQuery(sql);
      setResult(response);

      setHistory((prev) => [
        {
          sql: sql.trim(),
          success: response.success,
          message: response.message,
          timestamp: new Date(),
        },
        ...prev.slice(0, 9),
      ]);

      if (response.success) {
        toast.success(response.message);
      } else {
        toast.error(response.message);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Query failed';
      toast.error(message);
      setResult({ success: false, message, rows: [], columns: [], row_count: 0 });
    } finally {
      setLoading(false);
    }
  };

  const clearConsole = () => {
    setSql('');
    setResult(null);
  };

  const loadFromHistory = (item: QueryHistoryItem) => {
    setSql(item.sql);
  };

  const exampleQueries = [
    {
      name: 'Create Categories Table',
      sql: `CREATE TABLE categories (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) UNIQUE NOT NULL,
  description VARCHAR(500)
);`,
    },
    {
      name: 'Create Products Table',
      sql: `CREATE TABLE products (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(200) NOT NULL,
  sku VARCHAR(50) UNIQUE NOT NULL,
  category_id INTEGER,
  price FLOAT NOT NULL,
  quantity INTEGER DEFAULT 0
);`,
    },
    {
      name: 'Create Suppliers Table',
      sql: `CREATE TABLE suppliers (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(200) NOT NULL,
  email VARCHAR(100) UNIQUE,
  phone VARCHAR(20),
  address VARCHAR(500)
);`,
    },
    {
      name: 'Insert Sample Data',
      sql: `INSERT INTO categories (name, description)
      VALUES ('Electronics', 'Electronic devices and accessories');`,
    },
    {
      name: 'Select All',
      sql: `SELECT * FROM categories;`,
    },
    {
      name: 'Join Query',
      sql: `SELECT p.name, p.price, c.name AS category 
FROM products p 
JOIN categories c ON p.category_id = c.id;`,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">SQL Console</h1>
        <p className="mt-1 text-muted-foreground">
          Execute raw SQL queries against PesapalDB
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card className="glass">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Query Editor</CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={clearConsole}
                    className="gap-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    Clear
                  </Button>
                  <Button
                    size="sm"
                    onClick={executeQuery}
                    disabled={loading}
                    className="gap-2"
                  >
                    <Play className="h-4 w-4" />
                    {loading ? 'Running...' : 'Execute'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Textarea
                value={sql}
                onChange={(e) => setSql(e.target.value)}
                placeholder="Enter your SQL query here...

Example:
SELECT * FROM users WHERE active = true;"
                className="min-h-[200px] font-mono text-sm bg-background/50 border-white/5"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    executeQuery();
                  }
                }}
              />
              <p className="mt-2 text-xs text-muted-foreground">
                Press Cmd/Ctrl + Enter to execute
              </p>
            </CardContent>
          </Card>

          <Card className="glass">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                Results
                {result && (
                  <Badge variant={result.success ? 'default' : 'destructive'}>
                    {result.success ? 'Success' : 'Error'}
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!result ? (
                <p className="py-8 text-center text-muted-foreground">
                  Execute a query to see results
                </p>
              ) : result.rows.length > 0 ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent">
                        {result.columns.map((col) => (
                          <TableHead key={col}>{col}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {result.rows.map((row, idx) => (
                        <TableRow key={idx}>
                          {result.columns.map((col) => (
                            <TableCell key={col}>
                              {String(row[col] ?? 'NULL')}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="py-8 text-center">
                  <p className={result.success ? 'text-emerald-400' : 'text-destructive'}>
                    {result.message}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="glass">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Example Queries</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {exampleQueries.map((example) => (
                <Button
                  key={example.name}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-left"
                  onClick={() => setSql(example.sql)}
                >
                  {example.name}
                </Button>
              ))}
            </CardContent>
                      </Card>
                      <Card className="glass">
                        <CardHeader className="pb-3">
                          <CardTitle className="flex items-center gap-2 text-lg">
                            <Clock className="h-4 w-4" />
                            Query History
                          </CardTitle>
                        </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No queries yet
                </p>
              ) : (
                <div className="space-y-2">
                  {history.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => loadFromHistory(item)}
                      className="flex w-full items-start gap-2 rounded-lg p-2 text-left hover:bg-white/5 transition-colors"
                    >
                      {item.success ? (
                        <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                      ) : (
                        <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-mono text-xs">{item.sql}</p>
                        <p className="text-xs text-muted-foreground">
                          {item.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
