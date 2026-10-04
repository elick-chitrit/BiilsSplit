# Part A — Project Proposal

## 1. Project Name and One-Sentence Description
**BillsSplit** is a restaurant dine-in ordering and bill-splitting platform where diners join a table session through its QR code, browse the restaurant menu in the app, order items, and settle their share based on the items they consumed or shared.

## 2. Business Need / Problem
Group meals create friction when shared dishes make individual bills difficult to calculate. Manual allocation can leave diners paying for items they did not consume or share, causing unfair charges, disputes, and delays, while additional orders depend on staff availability. Restaurants need a consistent view of orders and outstanding balances throughout the meal.

## 3. Main Users and Roles
**Diners** join a table, browse the restaurant menu, view all current ordered items, identify their participation, place orders, and make mock payments with optional tips. **Restaurant staff** receive orders and update item/order status. **Shift managers** monitor table activity, outstanding balances, and readiness for closure.

## 4. Main Business Process: Trigger, Flow, and Result
**Trigger:** Staff open a table session and diners join through the table's QR code. **Flow:** Diners review existing items, associate themselves only with items they consumed or shared, and place additional orders from the restaurant menu in the app. An individual item is charged only to the diner who consumed it; a shared item is divided equally only among the diners who shared it. Each diner owes the sum of these shares, with no charge for items they did not consume or share. At payment, diners select **10%, 12%, 15%, 20%, Other (manual amount), or None**; percentages apply to their personal item subtotal. Payment is simulated using synthetic mock cards only, with no real card data or payment provider/API. **Result:** Mock payments update outstanding balances, and staff close the session once all items are allocated and the bill is settled. Business rules require positive prices and quantities, available menu items, valid table membership, unique diner participation per item, and nonnegative payment/tip amounts. Unallocated items block settlement, and paid allocations cannot be changed.

## 5. Information Flow
The restaurant supplies table information and the menu displayed in the app; diners supply orders, item participation, and tip choices; staff update fulfillment status. BillsSplit produces the shared item list, personal amounts owed, mock payment status, and current table state. **Tabit is the external POS integration target**, intended to reflect new orders, item/payment status, and live table state on the restaurant's main computers. Stage 1 models this synchronization locally; it does not connect to Tabit or claim a real API integration. All demonstration data are synthetic.

## 6. Expected Business Value
Enable fair, transparent payment for actual consumption, avoiding charges for other diners' items. Reduce ordering and checkout time, improve accuracy of individual shares, and reduce staff effort in reconciling group bills. A shared table view supports timely order handling and informed closure decisions.

## 7. Core Entities and Initial Relationships
A **Restaurant** has **Tables** and **Menu Items**. Each **Table Session** belongs to a table and contains **Diners** and **Orders**. An order contains **Order Items**, each referring to a menu item and associated with one or more diners who consumed it. A diner's **Mock Payment Method** supports **Mock Payments** linked to that diner and session; each payment records the settled share and optional tip separately. Tabit is an external business system.

## 8. Two Central Use Cases / Decisions Supported
1. **Allocate and settle a shared bill:** Three diners associate themselves with a shared dish, each owes one-third of its price while diners who did not share it owe nothing for that dish, and each participant selects a tip and completes a mock payment.
2. **Place and track an additional order:** A diner selects an available item from the restaurant menu in the app; staff receive it, update its status, and all session participants see the updated order and locally simulated POS state.

## 9. One Future Extension
Replace the local POS synchronization simulation with an authorized Tabit integration in a later course stage, subject to access and supported capabilities, so restaurant computers and BillsSplit share current order, item/payment, and table information; payments remain mock-only.
