# Part A — Project Proposal

## 1. Project Name and One-Sentence Description
**BillsSplit** lets restaurant diners join a table by QR code, browse its menu, order, and pay only for items they consumed or shared.

## 2. Business Need / Problem
Manual group-bill splitting causes delays, disputes, and charges for other diners' items; ordering also depends on staff availability. Restaurants need a clear, current table view.

## 3. Main Users and Roles
**Diners:** browse the menu, view ordered items, identify participation, order, and make mock payments with tips. **Staff:** receive orders and update fulfillment. **Shift managers:** monitor activity, balances, and table closure.

## 4. Main Business Process: Trigger, Flow, and Result
**Trigger:** Staff open a table session; diners join through its QR code. **Flow:** Diners view existing items, associate themselves only with items consumed or shared, and order from the in-app menu. Personal items belong to their consumer; shared costs split equally among participants, with indivisible cents allocated consistently. Each diner settles their shares using synthetic mock cards and selects **10%, 12%, 15%, 20%, Other (manual amount), or None** as a tip. Percentage tips apply to the personal item amount being settled. **Result:** Payments update item and diner balances; staff close a fully allocated, settled session. Rules require positive prices/quantities, available menu items, valid membership, unique participation, nonnegative payment/tip amounts, and unchanged paid allocations.

## 5. Information Flow
Restaurants supply tables and menus; diners create orders, participation, and tip choices; staff update fulfillment. Outputs include items, individual amounts, payment status, and table state. **Tabit is the external POS integration target** for reflecting new orders, item/payment status, and live table state on restaurant computers. Stage 1 simulates synchronization locally; no real Tabit API integration is implemented. All demonstration data and payments are synthetic: no real card data, payment provider, or payment API.

## 6. Expected Business Value
Fair, transparent payment prevents diners funding others' consumption, reduces disputes and calculation errors, accelerates ordering/checkout, and reduces staff reconciliation effort.

## 7. Core Entities and Initial Relationships
A **Restaurant** has **Tables** and **Menu Items**. A table's **Table Session** contains **Diners** and **Orders**; orders contain **Order Items** linked to menu items and participating diners. A diner's **Mock Payment Method** supports **Mock Payments** recording settled item shares and tips separately. Tabit remains external.

## 8. Two Central Use Cases / Decisions Supported
1. **Shared bill settlement:** Three participants each pay one-third of a shared dish, subject to cent rounding; nonparticipants owe nothing for it.
2. **Additional ordering:** A diner orders from the menu; staff update fulfillment, and participants see the order and locally simulated POS state.

## 9. One Future Extension
Add authorized Tabit synchronization in a later course stage, subject to access and supported capabilities; payments remain mock-only.
