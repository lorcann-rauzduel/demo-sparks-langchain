-- Les tickets du support, rejoués à la création de data/tickets.db
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('open', 'closed')),
    priority TEXT NOT NULL CHECK (priority IN ('low', 'high')),
    created_on TEXT NOT NULL
);
INSERT INTO tickets VALUES
    (1, 'VPN error ERR-4012', 'open', 'high', '2026-11-18'),
    (2, 'Printer offline on floor 2', 'open', 'low', '2026-11-19'),
    (3, 'Password reset', 'closed', 'low', '2026-11-10'),
    (4, 'Laptop stolen', 'open', 'high', '2026-11-20'),
    (5, 'Expense tool slow', 'closed', 'low', '2026-11-12');
