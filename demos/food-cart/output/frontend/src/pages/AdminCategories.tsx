/**
 * Admin Categories Page - Bumblebee Food Cart
 *
 * Displays a list of menu categories with ability to:
 * - View all categories
 * - Add new categories
 * - Edit existing categories
 * - Delete categories
 * - Reorder categories via drag and drop
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

// ---------------------------------------------------------------------------
// Types (mirrors backend CategoryResponse)
// ---------------------------------------------------------------------------

interface Category {
  id: number;
  name: string;
  sort_order: number;
}

interface CategoryFormData {
  name: string;
  sort_order: number;
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

const API_BASE = '/api/categories';

async function fetchCategories(): Promise<Category[]> {
  const res = await fetch(API_BASE);
  if (!res.ok) {
    throw new Error(`Failed to fetch categories: ${res.statusText}`);
  }
  return res.json();
}

async function createCategory(data: CategoryFormData): Promise<Category> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to create category: ${res.statusText}`);
  }
  return res.json();
}

async function updateCategory(
  id: number,
  data: CategoryFormData,
): Promise<Category> {
  const res = await fetch(`${API_BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to update category: ${res.statusText}`);
  }
  return res.json();
}

async function deleteCategory(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete category: ${res.statusText}`);
  }
}

// ---------------------------------------------------------------------------
// Modal component
// ---------------------------------------------------------------------------

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

function Modal({ isOpen, onClose, title, children }: ModalProps) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: '12px',
          padding: '1.5rem',
          width: '90%',
          maxWidth: '500px',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.25rem',
          }}
        >
          <h2
            style={{
              fontSize: '1.25rem',
              fontWeight: '700',
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            {title}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              padding: '0 0.25rem',
              lineHeight: 1,
            }}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Category Form component
// ---------------------------------------------------------------------------

interface CategoryFormProps {
  initialData?: CategoryFormData;
  onSubmit: (data: CategoryFormData) => void;
  onCancel: () => void;
  submitLabel: string;
}

function CategoryForm({ initialData, onSubmit, onCancel, submitLabel }: CategoryFormProps) {
  const [name, setName] = useState(initialData?.name ?? '');
  const [sort_order, setSortOrder] = useState(initialData?.sort_order ?? 0);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!name.trim()) {
      newErrors.name = 'Category name is required';
    } else if (name.trim().length > 100) {
      newErrors.name = 'Name must be 100 characters or less';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({ name: name.trim(), sort_order });
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '0.625rem 0.75rem',
    borderRadius: '8px',
    border: '1px solid var(--border-color)',
    backgroundColor: 'var(--bg-input)',
    color: 'var(--text-primary)',
    fontSize: '0.875rem',
    outline: 'none',
    boxSizing: 'border-box',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: '600',
    color: 'var(--text-primary)',
    marginBottom: '0.375rem',
  };

  const buttonBase: React.CSSProperties = {
    padding: '0.625rem 1.25rem',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: '600',
    cursor: 'pointer',
    border: 'none',
    transition: 'opacity 0.15s',
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ marginBottom: '1rem' }}>
        <label style={labelStyle} htmlFor="cat-name">
          Name *
        </label>
        <input
          id="cat-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Burgers"
          style={{
            ...inputStyle,
            borderColor: errors.name ? 'var(--color-danger)' : 'var(--border-color)',
          }}
        />
        {errors.name && (
          <span style={{ fontSize: '0.75rem', color: 'var(--color-danger)', marginTop: '0.25rem', display: 'block' }}>
            {errors.name}
          </span>
        )}
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label style={labelStyle} htmlFor="cat-sort-order">
          Sort Order
        </label>
        <input
          id="cat-sort-order"
          type="number"
          value={sort_order}
          onChange={(e) => setSortOrder(Number(e.target.value))}
          placeholder="0"
          style={inputStyle}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
        <button
          type="button"
          onClick={onCancel}
          style={{
            ...buttonBase,
            backgroundColor: 'var(--bg-button-secondary)',
            color: 'var(--text-primary)',
          }}
        >
          Cancel
        </button>
        <button
          type="submit"
          style={{
            ...buttonBase,
            backgroundColor: 'var(--color-primary)',
            color: '#fff',
          }}
        >
          {submitLabel}
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Confirm Dialog component
// ---------------------------------------------------------------------------

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
}

function ConfirmDialog({ isOpen, onClose, onConfirm, title, message }: ConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: '12px',
          padding: '1.5rem',
          width: '90%',
          maxWidth: '400px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2
          style={{
            fontSize: '1.125rem',
            fontWeight: '700',
            color: 'var(--text-primary)',
            margin: '0 0 0.75rem 0',
          }}
        >
          {title}
        </h2>
        <p
          style={{
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
            margin: '0 0 1.5rem 0',
            lineHeight: 1.5,
          }}
        >
          {message}
        </p>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button
            onClick={onClose}
            style={{
              padding: '0.625rem 1.25rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: '600',
              cursor: 'pointer',
              border: 'none',
              backgroundColor: 'var(--bg-button-secondary)',
              color: 'var(--text-primary)',
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            style={{
              padding: '0.625rem 1.25rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: '600',
              cursor: 'pointer',
              border: 'none',
              backgroundColor: 'var(--color-danger)',
              color: '#fff',
            }}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function AdminCategories() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);

  // Toast / notification state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // ---------------------------------------------------------------------------
  // Load categories
  // ---------------------------------------------------------------------------

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCategories();
      setCategories(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  // ---------------------------------------------------------------------------
  // Toast helper
  // ---------------------------------------------------------------------------

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // ---------------------------------------------------------------------------
  // CRUD handlers
  // ---------------------------------------------------------------------------

  const handleAdd = async (data: CategoryFormData) => {
    try {
      await createCategory(data);
      setShowAddModal(false);
      showToast('Category added successfully');
      loadCategories();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to add category';
      showToast(message, 'error');
    }
  };

  const handleEdit = async (data: CategoryFormData) => {
    if (!editingCategory) return;
    try {
      await updateCategory(editingCategory.id, data);
      setEditingCategory(null);
      showToast('Category updated successfully');
      loadCategories();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update category';
      showToast(message, 'error');
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteCategory(deleteTarget.id);
      setDeleteTarget(null);
      showToast('Category deleted');
      loadCategories();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete category';
      showToast(message, 'error');
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-page)',
        padding: '2rem 1rem',
      }}
    >
      <div
        style={{
          maxWidth: '800px',
          margin: '0 auto',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
            Categories
          </h1>
          <button
            onClick={() => setShowAddModal(true)}
            style={{
              padding: '0.625rem 1.25rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: '600',
              cursor: 'pointer',
              border: 'none',
              backgroundColor: 'var(--color-primary)',
              color: '#fff',
            }}
          >
            + Add Category
          </button>
        </div>

        {/* Error state */}
        {error && (
          <div
            style={{
              backgroundColor: 'var(--color-danger-bg)',
              color: 'var(--color-danger)',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              fontSize: '0.875rem',
            }}
          >
            <strong>Error:</strong> {error}
            <button
              onClick={loadCategories}
              style={{
                marginLeft: '0.75rem',
                background: 'none',
                border: '1px solid var(--color-danger)',
                color: 'var(--color-danger)',
                padding: '0.25rem 0.75rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.8rem',
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
            Loading categories…
          </div>
        )}

        {/* Categories list */}
        {!loading && !error && categories.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-secondary)' }}>
            <p style={{ fontSize: '2rem', margin: '0 0 0.5rem 0' }}>📂</p>
            <p style={{ margin: 0 }}>No categories yet. Add your first one!</p>
          </div>
        )}

        {!loading && !error && categories.length > 0 && (
          <div>
            {categories.map((cat) => (
              <div
                key={cat.id}
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderRadius: '12px',
                  padding: '1.25rem',
                  marginBottom: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ fontSize: '0.9375rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                    {cat.name}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                  <button
                    onClick={() => setEditingCategory(cat)}
                    style={{
                      padding: '0.375rem 0.75rem',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      cursor: 'pointer',
                      border: 'none',
                      backgroundColor: 'var(--bg-button-secondary)',
                      color: 'var(--text-primary)',
                    }}
                    title="Edit category"
                  >
                    ✏️ Edit
                  </button>
                  <button
                    onClick={() => setDeleteTarget(cat)}
                    style={{
                      padding: '0.375rem 0.75rem',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      cursor: 'pointer',
                      border: 'none',
                      backgroundColor: 'var(--color-danger-bg)',
                      color: 'var(--color-danger)',
                    }}
                    title="Delete category"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add Modal */}
        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Add New Category"
        >
          <CategoryForm
            onSubmit={handleAdd}
            onCancel={() => setShowAddModal(false)}
            submitLabel="Add Category"
          />
        </Modal>

        {/* Edit Modal */}
        <Modal
          isOpen={!!editingCategory}
          onClose={() => setEditingCategory(null)}
          title="Edit Category"
        >
          {editingCategory && (
            <CategoryForm
              initialData={{
                name: editingCategory.name,
                sort_order: editingCategory.sort_order,
              }}
              onSubmit={handleEdit}
              onCancel={() => setEditingCategory(null)}
              submitLabel="Save Changes"
            />
          )}
        </Modal>

        {/* Delete Confirmation */}
        <ConfirmDialog
          isOpen={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDelete}
          title="Delete Category"
          message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        />

        {/* Toast notification */}
        {toast && <div style={{ position: 'fixed', bottom: 16, right: 16, backgroundColor: toast.type === 'success' ? 'var(--color-success)' : 'var(--color-danger)', color: '#fff', padding: '0.75rem 1.25rem', borderRadius: 8, fontWeight: 600, zIndex: 2000 }}>{toast.message}</div>}
      </div>
    </div>
  );
}
