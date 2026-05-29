# PRD: Pop-Up Food Cart Ordering App

**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** Draft  

---

## Overview

A lightweight web app for a solo operator running a pop-up restaurant or food cart. Customers scan a QR code at the cart, browse the menu on their phone, and place an order. The operator sees orders come in on their tablet or laptop in real time and marks them complete when ready.

No app install required. No payment processing. Just a clean, fast ordering flow that works on any device.

---

## Target User

**The operator:** One person. Running a food cart, pop-up stall, or small event food booth. Not technical. Needs something that works out of the box — update the menu, see orders, mark them done. That's it.

**The customer:** Anyone with a phone. Scans a QR code at the cart. Browses the menu. Taps what they want. Places their order with a name. Done.

---

## Core User Flows

### Customer Flow
1. Scan QR code → land on menu page
2. Browse categories and items with photos and descriptions
3. Tap items to add to cart (quantity selector)
4. Review cart — see items, quantities, total
5. Enter name for pickup, place order
6. See confirmation screen with order number and estimated wait

### Operator Flow
1. Open admin panel (no auth for MVP — single operator, trusted device)
2. See incoming orders in real time — order number, customer name, items
3. Tap order to expand details
4. Mark order "Ready" → customer confirmation screen updates
5. Manage menu: add/edit/remove items, toggle availability (86'd items)
6. Set cart name, tagline, and hours shown on customer menu page

---

## Pages & Screens

### Customer Side
| Screen | Description |
|---|---|
| Menu | Category tabs, item cards with photo/name/price/description, Add button |
| Item Detail | Full photo, description, add to cart with quantity |
| Cart | Item list with quantities, subtotal, clear + checkout |
| Checkout | Name entry, order summary, Place Order button |
| Confirmation | Order number, items ordered, "We'll call your name when it's ready" |
| Order Status | Live status: Received → In Progress → Ready (updates in real time) |

### Operator Side (Admin)
| Screen | Description |
|---|---|
| Orders Dashboard | Live feed of active orders, newest first, with status badges |
| Order Detail | Expand order: items, quantities, customer name, time placed |
| Menu Manager | List of all menu items with toggle, edit, delete; add new item form |
| Item Form | Name, description, price, category, photo URL, available toggle |
| Settings | Cart name, tagline, open/closed toggle (closes ordering when off) |

---

## Data Model

### Menu Items
- `id`, `name`, `description`, `price` (cents), `category`, `photo_url`, `available` (bool), `sort_order`

### Categories
- `id`, `name`, `sort_order`

### Orders
- `id`, `order_number` (human-readable: #001), `customer_name`, `status` (received / in_progress / ready), `created_at`, `updated_at`

### Order Items
- `id`, `order_id`, `item_id`, `item_name` (snapshot), `item_price` (snapshot), `quantity`

### Settings
- `cart_name`, `tagline`, `is_open` (bool), `estimated_wait_minutes`

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | React + TypeScript + Vite | Consistent with swarm; Lemonade knows it well |
| Styling | Tailwind CSS | Fast, mobile-first, no custom CSS complexity |
| Backend | FastAPI (Python) | Consistent with swarm; simple REST + WebSocket |
| Database | SQLite | Zero setup, perfect for single-operator scale |
| Real-time | WebSockets (FastAPI) | Order status updates without polling |
| Hosting | Local / any simple host | No cloud dependencies |

---

## Phases

### Phase 1 — Foundation
Project scaffold, routing, DB schema, seed data, shared layout components.

Tickets:
- P1-001: Project scaffold (Vite + React + TS + Tailwind, FastAPI backend, SQLite init)
- P1-002: DB schema + seed data (categories, 8–10 menu items with photos, settings)
- P1-003: API layer — menu endpoints (`GET /menu`, `GET /menu/:id`, `GET /categories`)
- P1-004: Shared layout (header with cart badge, footer, page wrapper, routing shell)

### Phase 2 — Customer Menu & Cart
Full customer-facing browse and cart experience.

Tickets:
- P2-001: Menu page — category tabs, item grid, photo cards, add to cart
- P2-002: Item detail page — full view, quantity selector, add to cart
- P2-003: Cart context — global cart state, item count badge, persist on refresh
- P2-004: Cart page — item list, quantity adjust, remove, subtotal
- P2-005: Checkout page — name entry, order summary, place order (POST /orders)

### Phase 3 — Order Flow & Real-Time Status
Order placement, confirmation, and live status updates.

Tickets:
- P3-001: Order API — `POST /orders`, `GET /orders/:id`, `PATCH /orders/:id/status`
- P3-002: Confirmation screen — order number, items, wait time estimate
- P3-003: Order status page — live status display (Received → In Progress → Ready)
- P3-004: WebSocket server — broadcast status updates when operator marks order ready
- P3-005: WebSocket client — status page subscribes, updates in real time without refresh

### Phase 4 — Operator Admin
Order management dashboard and menu editing.

Tickets:
- P4-001: Admin layout — sidebar nav, orders/menu/settings routes
- P4-002: Orders dashboard — live order feed, status badges, newest first
- P4-003: Order detail — expand order, mark In Progress / Ready buttons
- P4-004: Admin WebSocket — push new orders to dashboard in real time
- P4-005: Menu manager — item list with availability toggle, edit/delete actions
- P4-006: Item form — add/edit item: name, description, price, category, photo URL, available

### Phase 5 — Polish & Operator Settings
Mobile responsiveness, settings, open/closed toggle, finishing touches.

Tickets:
- P5-001: Settings page — cart name, tagline, open/closed toggle, wait time estimate
- P5-002: Closed state — when `is_open=false`, show "We're closed" on menu page, block ordering
- P5-003: Mobile polish — responsive audit across all customer screens (menu, cart, checkout, confirmation)
- P5-004: Empty states + error handling — empty cart, no menu items, order not found
- P5-005: Seed photo content — finalize seed menu with real food photo URLs, realistic item names/descriptions

---

## Scope Boundaries (MVP)

**In scope:**
- Menu browse, cart, order placement, confirmation, live status
- Operator order management and menu editing
- Real-time updates via WebSocket
- Open/closed toggle
- Mobile-friendly customer UI

**Explicitly out of scope:**
- Payment processing (orders are pay-at-cart)
- Customer accounts or login
- Order history for customers
- Push notifications
- Multi-location support
- Printer integration
- Inventory tracking

---

## Demo Story

> "This is a complete ordering app for a food cart — menu, cart, checkout, real-time kitchen view, menu management. Built entirely by a local AI model running on one machine. No cloud API. No per-token cost. $0.00."

Side-by-side demo: cloud AI builds the same app → cost ticker climbs. Local AI builds it → $0.00 the whole time. Audience sees food photos and a cart. No code required.

---

## File Count Estimate

| Phase | Tickets | Estimated Files |
|---|---|---|
| Phase 1 | 4 | 8–12 |
| Phase 2 | 5 | 12–16 |
| Phase 3 | 5 | 10–14 |
| Phase 4 | 6 | 12–16 |
| Phase 5 | 5 | 6–10 |
| **Total** | **25** | **48–68 files** |

Target: ~55 files across 25 tickets — enough complexity to make the cost comparison meaningful, tight enough that Lemonade can execute ticket-by-ticket without losing the thread.

---

## Decisions

| Question | Decision | Notes |
|---|---|---|
| Admin auth | PIN: `1234` | Simple hardcoded PIN on admin entry page; no session/JWT needed for MVP |
| Photos | File upload | Operator uploads from device; FastAPI serves static files from `/uploads`; multipart form |
| Demo format | Live build | Lemonade builds during presentation; stock tracker took ~2 min so 2x is acceptable |
| Order numbers | 3-digit sequential | Format: `#001`, `#002`, etc. Zero-padded, human-readable on screen |
