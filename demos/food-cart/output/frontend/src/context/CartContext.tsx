import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react';
import { CartLine, MenuItem } from '../types';

type CartContextValue = {
  lines: CartLine[];
  addItem: (item: MenuItem, quantity?: number) => void;
  setQuantity: (itemId: number, quantity: number) => void;
  removeItem: (itemId: number) => void;
  clearCart: () => void;
  itemCount: number;
  subtotal: number;
};

const CartContext = createContext<CartContextValue | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [lines, setLines] = useState<CartLine[]>(() => {
    const raw = localStorage.getItem('foodcart.cart');
    return raw ? JSON.parse(raw) : [];
  });

  useEffect(() => {
    localStorage.setItem('foodcart.cart', JSON.stringify(lines));
  }, [lines]);

  const value = useMemo<CartContextValue>(() => ({
    lines,
    addItem: (item, quantity = 1) => setLines(prev => {
      const found = prev.find(line => line.item.id === item.id);
      if (found) return prev.map(line => line.item.id === item.id ? { ...line, quantity: line.quantity + quantity } : line);
      return [...prev, { item, quantity }];
    }),
    setQuantity: (itemId, quantity) => setLines(prev => prev.map(line => line.item.id === itemId ? { ...line, quantity } : line).filter(line => line.quantity > 0)),
    removeItem: itemId => setLines(prev => prev.filter(line => line.item.id !== itemId)),
    clearCart: () => setLines([]),
    itemCount: lines.reduce((sum, line) => sum + line.quantity, 0),
    subtotal: lines.reduce((sum, line) => sum + line.item.price * line.quantity, 0)
  }), [lines]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used inside CartProvider');
  return ctx;
}

export function formatMoney(cents: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(cents / 100);
}
