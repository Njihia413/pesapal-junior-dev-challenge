'use client';

import { useState, useEffect } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/data-table/data-table';
import { api } from '@/lib/api';
import { Plus, Pencil, Trash2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

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
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [tableExists, setTableExists] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [productToDelete, setProductToDelete] = useState<Product | null>(null);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    category_id: '',
    price: '',
    quantity: '',
  });

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const result = await api.getTableRows('products');
      if (result.success) {
        setProducts(result.rows as unknown as Product[]);
        setTableExists(true);
      }
    } catch {
      setProducts([]);
      setTableExists(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const result = await api.getTableRows('categories');
      if (result.success) {
        setCategories(result.rows as unknown as Category[]);
      }
    } catch (err) {
      console.error('Failed to fetch categories:', err);
      setCategories([]);
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      name: formData.name,
      sku: formData.sku,
      category_id: formData.category_id ? parseInt(formData.category_id) : null,
      price: parseFloat(formData.price),
      quantity: parseInt(formData.quantity) || 0,
    };

    try {
      if (editingProduct) {
        await api.updateRow('products', editingProduct.id, data);
        toast.success('Product updated successfully');
      } else {
        await api.insertRow('products', data);
        toast.success('Product created successfully');
      }
      setDialogOpen(false);
      resetForm();
      fetchProducts();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Operation failed');
    }
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name,
      sku: product.sku,
      category_id: product.category_id?.toString() || '',
      price: product.price.toString(),
      quantity: product.quantity.toString(),
    });
    setDialogOpen(true);
  };

  const handleDeleteClick = (product: Product) => {
    setProductToDelete(product);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!productToDelete) return;
    try {
      await api.deleteRow('products', productToDelete.id);
      toast.success('Product deleted successfully');
      fetchProducts();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setDeleteDialogOpen(false);
      setProductToDelete(null);
    }
  };

  const resetForm = () => {
    setEditingProduct(null);
    setFormData({ name: '', sku: '', category_id: '', price: '', quantity: '' });
  };

  const createTable = async () => {
    try {
      await api.executeQuery(`
        CREATE TABLE products (
          id INTEGER PRIMARY KEY AUTO_INCREMENT,
          name VARCHAR(200) NOT NULL,
          sku VARCHAR(50) UNIQUE NOT NULL,
          category_id INTEGER,
          price FLOAT NOT NULL,
          quantity INTEGER DEFAULT 0
        )
      `);
      toast.success('Products table created!');
      fetchProducts();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create table');
    }
  };

  const columns: ColumnDef<Product>[] = [
    {
      accessorKey: 'id',
      header: 'ID',
    },
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
    },
    {
      accessorKey: 'sku',
      header: 'SKU',
      cell: ({ row }) => <Badge variant="outline">{row.original.sku}</Badge>,
    },
    {
      accessorKey: 'price',
      header: 'Price',
      cell: ({ row }) => `Kshs${row.original.price.toFixed(2)}`,
    },
    {
      accessorKey: 'quantity',
      header: 'Quantity',
      cell: ({ row }) => (
        <Badge variant={row.original.quantity > 10 ? 'default' : 'destructive'}>
          {row.original.quantity}
        </Badge>
      ),
    },
    {
      accessorKey: 'category_id',
      header: 'Category',
      cell: ({ row }) => row.original.category_id || '-',
    },
    {
      id: 'actions',
      header: () => <div className="text-right">Actions</div>,
      cell: ({ row }) => (
        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => handleEdit(row.original)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => handleDeleteClick(row.original)}>
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Products</h1>
          <p className="mt-1 text-muted-foreground">Manage your product inventory</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchProducts}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={resetForm}>
                <Plus className="h-4 w-4" />
                Add Product
              </Button>
            </DialogTrigger>
            <DialogContent className="font-montserrat">
              <DialogHeader>
                <DialogTitle>
                  {editingProduct ? 'Edit Product' : 'Add New Product'}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Product Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter product name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sku">SKU</Label>
                  <Input
                    id="sku"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    placeholder="Enter SKU"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="price">Price (Kshs)</Label>
                    <Input
                      id="price"
                      type="number"
                      step="0.01"
                      value={formData.price}
                      onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                      placeholder="0.00"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="quantity">Quantity</Label>
                    <Input
                      id="quantity"
                      type="number"
                      value={formData.quantity}
                      onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                      placeholder="0"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1">
                  <Label htmlFor="category_id">Category</Label>
                  {categories.length > 0 ? (
                    <Select
                      value={formData.category_id}
                      onValueChange={(value) => setFormData({ ...formData, category_id: value })}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map((cat) => (
                          <SelectItem key={cat.id} value={cat.id.toString()}>
                            {cat.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed p-4">
                      <p className="text-sm text-muted-foreground">No categories found</p>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          // Close this dialog and open the category creation one
                          setDialogOpen(false);
                          // This is a bit of a hack, ideally you'd use a router or global state
                          setTimeout(() => {
                            const addCategoryButton = document.querySelector('#add-category-button');
                            if (addCategoryButton instanceof HTMLElement) {
                              addCategoryButton.click();
                            }
                          }, 100);
                        }}
                      >
                        Create Category
                      </Button>
                    </div>
                  )}
                </div>
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">
                    {editingProduct ? 'Update' : 'Create'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          {loading ? (
            <div className="flex h-48 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : !tableExists ? (
            <div className="flex h-48 flex-col items-center justify-center gap-4">
              <p className="text-muted-foreground">Products table does not exist</p>
              <Button variant="outline" onClick={createTable}>
                Create Products Table
              </Button>
            </div>
          ) : products.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center gap-4">
              <div className="border-2 border-primary rounded-lg p-6 text-center">
                <p className="text-muted-foreground">No products found</p>
                <p className="text-sm text-muted-foreground mt-2">Click &quot;Add Product&quot; to create your first product</p>
              </div>
            </div>
          ) : (
            <DataTable columns={columns} data={products} />
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent className="font-montserrat">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Product</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{productToDelete?.name}&quot;? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
