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
import '../styles/design-tokens.css';

// ---------------------------------------------------------------------------
// Types (mirrors backend CategoryResponse)
// ---------------------------------------------------------------------------

interface Category {
  id: number;
  name: string;
  description: string | null;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface CategoryFormData {
  name: string;
  description: string;
  display_order: number;
  is_active: boolean;
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

async function createCategory(data: Omit<CategoryFormData, 'display_order'>): Promise<Category> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...data, display_order: 0 }),
  });
  if (!res.ok) {
    throw new Error(`Failed to create category: ${res.statusText}`);
  }
  return res.json();
}

async function updateCategory(
  id: number,
  data: Partial<CategoryFormData>,
): Promise<Category> {
  const res = await fetch(`${API_BASE}/${id}`, {
    method: 'PATCH',
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
  onSubmit: (data: Omit<CategoryFormData, 'display_order'>) => void;
  onCancel: () => void;
  submitLabel: string;
}

function CategoryForm({ initialData, onSubmit, onCancel, submitLabel }: CategoryFormProps) {
  const [name, setName] = useState(initialData?.name ?? '');
  const [description, setDescription] = useState(initialData?.description ?? '');
  const [is_active, setIsActive] = useState(initialData?.is_active ?? true);
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
    onSubmit({ name: name.trim(), description: description.trim() || null, is_active });
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

  const checkboxLabelStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    cursor: 'pointer',
    fontSize: '0.875rem',
    color: 'var(--text-primary)',
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
        <label style={labelStyle} htmlFor="cat-desc">
          Description
        </label>
        <textarea
          id="cat-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description…"
          rows={3}
          style={inputStyle}
        />
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label style={checkboxLabelStyle}>
          <input
            type="checkbox"
            checked={is_active}
            onChange={(e) => setIsActive(e.target.checked)}
          />
          Active
        </label>
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

  // Drag and drop state
  const dragItem = useRef<number | null>(null);
  const dragOverItem = useRef<number | null>(null);

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

  const handleAdd = async (data: Omit<CategoryFormData, 'display_order'>) => {
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

  const handleEdit = async (data: Omit<CategoryFormData, 'display_order'>) => {
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
  // Drag and drop reorder
  // ---------------------------------------------------------------------------

  const handleDragStart = (index: number) => {
    dragItem.current = index;
  };

  const handleDragEnter = (index: number) => {
    dragOverItem.current = index;
  };

  const handleDragEnd = () => {
    if (dragItem.current === null || dragOverItem.current === null) return;
    if (dragItem.current === dragOverItem.current) {
      dragItem.current = null;
      dragOverItem.current = null;
      return;
    }

    const updated = [...categories];
    const [removed] = updated.splice(dragItem.current!, 1);
    updated.splice(dragOverItem.current!, 0, removed);

    // Recalculate display_order based on new positions
    const reordered = updated.map((cat, idx) => ({
      ...cat,
      display_order: idx,
    }));

    setCategories(reordered);

    // Persist the new order to the backend
    const promises = reordered.map((cat) =>
      updateCategory(cat.id, { display_order: cat.display_order }).catch(() => null),
    );
    Promise.all(promises).then(() => {
      showToast('Category order updated');
      loadCategories();
    }).catch(() => {
      // If backend update fails, reload to revert
      loadCategories();
    });

    dragItem.current = null;
    dragOverItem.current = null;
  };

  // ---------------------------------------------------------------------------
  // Styles
  // ---------------------------------------------------------------------------

  const cardStyle: React.CSSProperties = {
    backgroundColor: 'var(--bg-card)',
    borderRadius: '12px',
    padding: '1.25rem',
    marginBottom: '0.75rem',
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
    border: '1px solid var(--border-color)',
    cursor: 'grab',
    transition: 'box-shadow 0.15s, transform 0.15s',
  };

  const dragHandleStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    cursor: 'grab',
    padding: '0.25rem',
    opacity: 0.4,
  };

  const dragHandleDot: React.CSSProperties = {
    width: '4px',
    height: '4px',
    borderRadius: '50%',
    backgroundColor: 'var(--text-secondary)',
  };

  const categoryInfoStyle: React.CSSProperties = {
    flex: 1,
    minWidth: 0,
  };

  const badgeStyle = (isActive: boolean): React.CSSProperties => ({
    display: 'inline-block',
    padding: '0.125rem 0.5rem',
    borderRadius: '999px',
    fontSize: '0.7rem',
    fontWeight: '600',
    backgroundColor: isActive ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
    color: isActive ? 'var(--color-success)' : 'var(--color-danger)',
  });

  const actionButtonBase: React.CSSProperties = {
    padding: '0.375rem 0.75rem',
    borderRadius: '6px',
    fontSize: '0.8rem',
    fontWeight: '600',
    cursor: 'pointer',
    border: 'none',
    transition: 'opacity 0.15s',
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  };

  const emptyStyle: React.CSSProperties = {
    textAlign: 'center',
    padding: '3rem 1rem',
    color: 'var(--text-secondary)',
  };

  const toastStyle = (type: 'success' | 'error'): React.CSSProperties => ({
    position: 'fixed',
    bottom: '1.5rem',
    right: '1.5rem',
    padding: '0.75rem 1.25rem',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#fff',
    backgroundColor: type === 'success' ? 'var(--color-success)' : 'var(--color-danger)',
    boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
    zIndex: 2000,
    animation: 'fadeIn 0.2s ease-out',
  });

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
        <div style={headerStyle}>
          <div>
            <h1
              style={{
                fontSize: '1.5rem',
                fontWeight: '700',
                color: 'var(--text-primary)',
                margin: 0,
              }}
            >
              Categories
            </h1>
            <p
              style={{
                fontSize: '0.875rem',
                color: 'var(--text-secondary)',
                margin: '0.25rem 0 0 0',
              }}
            >
              Manage your menu categories. Drag to reorder.
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            style={{
              ...actionButtonBase,
              backgroundColor: 'var(--color-primary)',
              color: '#fff',
              padding: '0.625rem 1.25rem',
              fontSize: '0.875rem',
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
          <div style={emptyStyle}>
            <p style={{ fontSize: '2rem', margin: '0 0 0.5rem 0' }}>📂</p>
            <p style={{ margin: 0 }}>No categories yet. Add your first one!</p>
          </div>
        )}

        {!loading && !error && categories.length > 0 && (
          <div>
            {categories.map((cat, index) => (
              <div
                key={cat.id}
                style={cardStyle}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragEnter={() => handleDragEnter(index)}
                onDragEnd={handleDragEnd}
                onDragOver={(e) => e.preventDefault()}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLDivElement).style.boxShadow =
                    '0 4px 16px rgba(0,0,0,0.12)';
                  (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLDivElement).style.boxShadow =
                    '0 2px 8px rgba(0,0,0,0.06)';
                  (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
                }}
              >
                {/* Drag handle */}
                <div style={dragHandleStyle} title="Drag to reorder">
                  <div style={dragHandleDot} />
                  <div style={dragHandleDot} />
                  <div style={dragHandleDot} />
                  <div style={dragHandleDot} />
                  <div style={dragHandleDot} />
                  <div style={dragHandleDot} />
                </div>

                {/* Order number */}
                <div
                  style={{
                    width: '2rem',
                    height: '2rem',
                    borderRadius: '50%',
                    backgroundColor: 'var(--bg-button-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.8rem',
                    fontWeight: '700',
                    color: 'var(--text-secondary)',
                    flexShrink: 0,
                  }}
                >
                  {index + 1}
                </div>

                {/* Category info */}
                <div style={categoryInfoStyle}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      marginBottom: '0.125rem',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '0.9375rem',
                        fontWeight: '600',
                        color: 'var(--text-primary)',
                      }}
                    >
                      {cat.name}
                    </span>
                    <span style={badgeStyle(cat.is_active)}>
                      {cat.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  {cat.description && (
                    <p
                      style={{
                        fontSize: '0.8rem',
                        color: 'var(--text-secondary)',
                        margin: 0,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {cat.description}
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                  <button
                    onClick={() => setEditingCategory(cat)}
                    style={{
                      ...actionButtonBase,
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
                      ...actionButtonBase,
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

        {/* Back button */}
        <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
          <button
            onClick={() => navigate('/admin/menu')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-primary)',
              fontSize: '0.875rem',
              fontWeight: '600',
              cursor: 'pointer',
              padding: '0.5rem',
            }}
          >
            ← Back to Menu Management
          </button>
        </div>
      </div>

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
              description: editingCategory.description ?? '',
              display_order: editingCategory.display_order,
              is_active: editingCategory.is_active,
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
      {toast && <div style={toastStyle(toast.type)}>{toast.message}</div>}
    </div>
  );
}
