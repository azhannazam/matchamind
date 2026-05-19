-- Sample data for testing

-- Insert test user (replace with actual UUID from auth.users)
INSERT INTO profiles (id, email, full_name, monthly_budget, savings_goal)
VALUES 
    ('test-user-123', 'demo@matchamind.com', 'Demo User', 500.00, 1000.00)
ON CONFLICT (id) DO NOTHING;

-- Insert sample transactions
INSERT INTO transactions (user_id, amount, merchant, category_id, raw_text, transaction_date, parsed_by_ai)
SELECT 
    'test-user-123',
    amount,
    merchant,
    (SELECT id FROM categories WHERE user_id = 'test-user-123' AND name = category_name LIMIT 1),
    raw_text,
    transaction_date,
    TRUE
FROM (VALUES
    (32.50, 'Tealive', 'Matcha/Tea', 'RM 32.50 - Tealive (Matcha Latte + Boba)', '2024-01-15'),
    (45.90, 'Tealive', 'Matcha/Tea', 'RM 45.90 - Tealive Midvalley (Matcha Frappe)', '2024-01-18'),
    (18.50, 'Nasi Kandar Pelita', 'Mamak', 'Nasi Kandar Pelita - RM 18.50 (Roti Canai + Teh Tarik)', '2024-01-20'),
    (32.40, 'KFC', 'Fried Chicken', 'KFC: RM 32.40 2pc combo meal', '2024-01-22'),
    (15.00, 'Chatime', 'Matcha/Tea', 'Chatime - Matcha Milk Tea RM15', '2024-01-25'),
    (129.00, 'Shopee', 'Matcha/Tea', 'Paid RM129 for Matcha powder from Shopee', '2024-01-28'),
    (22.50, 'Zus Coffee', 'Coffee', 'Zus Coffee - Latte + Croissant RM22.50', '2024-02-01'),
    (45.00, 'Texas Chicken', 'Fried Chicken', 'Texas Chicken - 4pc meal RM45', '2024-02-03'),
    (12.00, 'Mamak Stall', 'Mamak', 'Mamak stall - Roti Canai x2 + Teh O RM12', '2024-02-05'),
    (28.00, 'Starbucks', 'Coffee', 'Starbucks - Matcha Latte Grande RM28', '2024-02-07')
) AS t(amount, merchant, category_name, raw_text, transaction_date);

-- Insert sample alerts
INSERT INTO alerts (user_id, type, message, severity, created_at)
VALUES
    ('test-user-123', 'spike', '🍵 Your matcha spending is up 45% this week (RM45 → RM65). Try brewing at home twice this week to save RM20!', 'warning', NOW() - INTERVAL '2 days'),
    ('test-user-123', 'budget_warning', '⚠️ You''ve used 80% of your monthly budget with 10 days left. Consider reducing indulgences by 15% this week.', 'warning', NOW() - INTERVAL '5 days'),
    ('test-user-123', 'savings_milestone', '🎉 Amazing! You''ve saved RM250 this month by cutting back on weekday matcha runs. Keep it up!', 'success', NOW() - INTERVAL '3 days');