/**
 * PesapalDB API Client
 * 
 * Client library for interacting with the PesapalDB REST API.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface QueryResponse {
  success: boolean;
  message: string;
  rows: Record<string, unknown>[];
  columns: string[];
  row_count: number;
}

export interface TableInfo {
  name: string;
  columns: number;
  rows: number;
}

export interface TableDetails {
  name: string;
  columns: Array<{
    name: string;
    type: string;
    length: number | null;
    nullable: boolean;
    primary_key: boolean;
    unique: boolean;
    auto_increment: boolean;
  }>;
  row_count: number;
  indexes: string[];
}

export interface DatabaseStats {
  table_count: number;
  total_size_bytes: number;
  data_directory: string;
  tables: Record<string, number>;
  created_at: string | null;
  last_modified: string | null;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || error.message || 'Request failed');
  }
  return response.json();
}

export const api = {
  // Health check
  async health() {
    const response = await fetch(`${API_BASE}/health`);
    return handleResponse<{ status: string; database: string; tables: number }>(response);
  },

  // Database stats
  async getStats(): Promise<DatabaseStats> {
    const response = await fetch(`${API_BASE}/stats`);
    return handleResponse<DatabaseStats>(response);
  },

  // Execute SQL query
  async executeQuery(sql: string): Promise<QueryResponse> {
    const response = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql }),
    });
    return handleResponse<QueryResponse>(response);
  },

  // List all tables
  async getTables(): Promise<{ tables: TableInfo[] }> {
    const response = await fetch(`${API_BASE}/tables`);
    return handleResponse<{ tables: TableInfo[] }>(response);
  },

  // Get table info
  async getTableInfo(tableName: string): Promise<TableDetails> {
    const response = await fetch(`${API_BASE}/tables/${tableName}`);
    return handleResponse<TableDetails>(response);
  },

  // Get table rows
  async getTableRows(
    tableName: string,
    options?: { limit?: number; offset?: number; orderBy?: string; orderDir?: 'ASC' | 'DESC' }
  ): Promise<QueryResponse> {
    const params = new URLSearchParams();
    if (options?.limit) params.set('limit', String(options.limit));
    if (options?.offset) params.set('offset', String(options.offset));
    if (options?.orderBy) params.set('order_by', options.orderBy);
    if (options?.orderDir) params.set('order_dir', options.orderDir);

    const url = `${API_BASE}/tables/${tableName}/rows${params.toString() ? '?' + params : ''}`;
    const response = await fetch(url);
    return handleResponse<QueryResponse>(response);
  },

  // Insert row
  async insertRow(tableName: string, data: Record<string, unknown>): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/tables/${tableName}/rows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data }),
    });
    return handleResponse<{ success: boolean; message: string }>(response);
  },

  // Update row
  async updateRow(
    tableName: string,
    rowId: number,
    data: Record<string, unknown>
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/tables/${tableName}/rows/${rowId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data }),
    });
    return handleResponse<{ success: boolean; message: string }>(response);
  },

  // Delete row
  async deleteRow(tableName: string, rowId: number): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/tables/${tableName}/rows/${rowId}`, {
      method: 'DELETE',
    });
    return handleResponse<{ success: boolean; message: string }>(response);
  },

  // Drop table
  async dropTable(tableName: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/tables/${tableName}`, {
      method: 'DELETE',
    });
    return handleResponse<{ success: boolean; message: string }>(response);
       },
    
  // Reset database
  async resetDatabase(): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/reset`, {
      method: 'POST',
    });
    return handleResponse<{ success: boolean; message: string }>(response);
  },
  };
