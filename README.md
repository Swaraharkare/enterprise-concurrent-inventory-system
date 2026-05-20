# Enterprise Inventory & Concurrent Order Processing System

A clean-architecture, production-grade backend engine designed to manage high-volume product inventories and handle simultaneous checkout requests safely. This solution implements strict transactional boundaries, thread-safe memory handling, and localized file data persistence to eliminate race conditions in a multithreaded environment.

## 🚀 Key Technical Architecture Highlights

* **Thread Safety & Mutual Exclusion:** Employs threading `Lock` mechanisms to securely synchronize shared system resources during asynchronous order calculations, preventing inventory overselling (race conditions).
* **All-or-Nothing Transactional Strategy:** Implemented a decoupled two-stage order loop—**Pre-Validation** and **Commitment**. This ensures that an entire order is rejected safely if any individual item fails validation or falls short on available stock.
* **Encapsulated Domain Logic:** Leveraged core Object-Oriented Programming (OOP) principles and Python `dataclasses` to strictly encapsulate property states (e.g., controlling stock reduction directly within the domain entity boundary).
* **Robust Enterprise Auditing:** Configured a thread-safe, structured console tracking pipeline utilizing Python's native `logging` framework to trace operations across worker instances.
* **Data Resilience & Persistence:** Features an automated local JSON database file management system layer capable of handling read/write lifecycles cleanly with fault-tolerant exception handling.

## 🛠️ Technology Stack & Concepts
* **Language:** Python 3.10+
* **Concurrency Model:** `concurrent.futures.ThreadPoolExecutor` (Worker Pool pattern)
* **Resource Synchronization:** `threading.Lock`
* **Data Layer:** Localized Structured File-System JSON Storage

---

## 📈 Technical Execution & Runtime Verification

When the simulation runs, the order processing engine initializes worker threads to process incoming batches concurrently. The following live production trace log highlights the thread safety behavior, showing asynchronous operations and robust defensive bounds-checking:

```text
2026-05-20 20:36:30 [WARNING] (MainThread) Data file data\inventory.json not found. Initializing mock database.
2026-05-20 20:36:30 [INFO] (MainThread) Mock database populated and initialized.
2026-05-20 20:36:30 [INFO] (MainThread) --- Booting Multithreaded Order Processing Engine ---
2026-05-20 20:36:30 [INFO] (OrderWorker_0) Initiating processing for Order System Ref: ORD-2026-001
2026-05-20 20:36:30 [INFO] (OrderWorker_1) Initiating processing for Order System Ref: ORD-2026-002
2026-05-20 20:36:30 [INFO] (OrderWorker_2) Initiating processing for Order System Ref: ORD-2026-003
2026-05-20 20:36:30 [INFO] (OrderWorker_0) Order ORD-2026-001 APPROVED. Total: $3,152.50
2026-05-20 20:36:30 [INFO] (OrderWorker_1) Order ORD-2026-002 APPROVED. Total: $4,500.00
2026-05-20 20:36:30 [INFO] (OrderWorker_2) Order ORD-2026-003 APPROVED. Total: $9,000.00
2026-05-20 20:36:31 [INFO] (OrderWorker_0) Order ORD-2026-004 APPROVED. Total: $1,505.00
2026-05-20 20:36:31 [INFO] (MainThread) --- Session Terminated. Final state persisted to disk. ---

Process finished with exit code 0
