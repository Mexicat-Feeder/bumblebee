import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react';
import { CartItem, MenuItem } from '../types';

interface CartContextValue {
  items: CartItem[];
  addItem: (item: MenuItem, quantity?: number) => void;
  updateQuantity: (itemId: number, quantity: number) => void;
  removeItem: (itemId: number) => void;
  clearCart: () => void;
  itemCount: number;
  subtotal: number;
}

const CartContext = createContext<CartContextValue | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(() => {
    const raw = localStorage.getItem('food-cart-items');
    return raw ? JSON.parse(raw) : [];
  });

  useEffect(() => {
    localStorage.setItem('food-cart-items', JSON.stringify(items));
  }, [items]);

  const addItem = (item: MenuItem, quantity = 1) => {
    setItems((current) => {
      const existing = current.find((entry) => entry.item.id === item.id);
      if (existing) {
        return current.map((entry) =>
          entry.item.id === item.id ? { ...entry, quantity: entry.quantity + quantity } : entry
        );
      }
      return [...current, { item, quantity }];
    });
  };

  const updateQuantity = (itemId: number, quantity: number) => {
    if (quantity <= 0) {
      removeItem(itemId);
      return;
    }
    setItems((current) =>
      current.map((entry) => (entry.item.id === itemId ? { ...entry, quantity } : entry))
    );
  };

  const removeItem = (itemId: number) => {
    setItems((current) => current.filter((entry) => entry.item.id !== itemId));
  };

  const clearCart = () => setItems([]);

  const itemCount = useMemo(
    () => items.reduce((sum, entry) => sum + entry.quantity, 0),
    [items]
  );

  const subtotal = useMemo(
    () => items.reduce((sum, entry) => sum + entry.item.price * entry.quantity, 0),
    [items]
  );

  return (
    <CartContext.Provider value={{ items, addItem, updateQuantity, removeItem, clearCart, itemCount, subtotal }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
}
