-- Generated from shop.db — subset for Supabase demo.
-- Run after schema.sql. Resets IDs to match SQLite sample.

truncate table public.orders, public.customers restart identity cascade;

INSERT INTO public.customers (customer_id, full_name, email, gender, birthdate, created_at, city, state, zip_code, customer_segment, loyalty_tier, is_active) VALUES
(1, 'Patricia Diallo', 'patriciadiallo0@example.com', 'Female', '2005-06-08', '2025-10-11T16:37:40'::timestamptz, 'Clayton', 'CO', '28289', 'standard', 'silver', 1),
(2, 'Juan Flores', 'juanflores1@example.com', 'Male', '1995-05-29', '2025-10-11T16:37:40'::timestamptz, 'Hudson', 'CO', '88907', 'budget', 'none', 1),
(3, 'Mary González', 'marygonzález2@example.com', 'Female', '2005-06-30', '2025-06-26T16:37:40'::timestamptz, 'Oxford', 'OH', '46421', 'budget', 'gold', 1),
(4, 'Omar Fischer', 'omarfischer3@example.com', 'Male', '2005-08-13', '2025-07-17T16:37:40'::timestamptz, 'Riverton', 'NC', '70217', 'standard', 'gold', 1),
(5, 'Salma Sullivan', 'salmasullivan4@example.com', 'Female', '1971-11-29', '2025-02-14T16:37:40'::timestamptz, 'Franklin', 'AZ', '16006', 'standard', 'silver', 1),
(6, 'Rohan Suzuki', 'rohansuzuki5@example.com', 'Male', '1989-10-19', '2025-02-10T16:37:40'::timestamptz, 'Milton', 'IL', '56566', 'budget', 'none', 1),
(7, 'Yuki González', 'yukigonzález6@example.com', 'Female', '2002-07-29', '2025-10-17T16:37:40'::timestamptz, 'Auburn', 'MI', '45382', 'premium', 'silver', 1),
(8, 'Sarah Gómez', 'sarahgómez7@example.com', 'Female', '1968-08-11', '2025-10-22T16:37:40'::timestamptz, 'Oxford', 'TX', '62581', 'budget', 'none', 1),
(9, 'Giovanni Singh', 'giovannisingh8@example.com', 'Male', '2000-03-18', '2025-10-07T16:37:40'::timestamptz, 'Fairview', 'MI', '44718', 'budget', 'silver', 1),
(10, 'Ravi Suzuki', 'ravisuzuki9@example.com', 'Male', '2003-10-22', '2025-03-02T16:37:40'::timestamptz, 'Fairview', 'CO', '76784', 'standard', 'silver', 1),
(11, 'Pooja Schneider', 'poojaschneider10@example.com', 'Female', '1957-01-17', '2025-05-13T16:37:40'::timestamptz, 'Auburn', 'FL', '60019', 'standard', 'none', 1),
(12, 'Lucia Yousef', 'luciayousef11@example.com', 'Female', '1960-09-09', '2025-01-06T16:37:40'::timestamptz, 'Oxford', 'NC', '24621', 'budget', 'none', 1),
(13, 'Morgan Ahmad', 'morganahmad12@example.com', 'Non-binary', '1978-04-16', '2025-07-15T16:37:40'::timestamptz, 'Ashland', 'NY', '93748', 'standard', 'none', 1),
(14, 'Karin Smith', 'karinsmith13@example.com', 'Female', '2001-09-10', '2025-06-11T16:37:40'::timestamptz, 'Bristol', 'UT', '12552', 'budget', 'none', 1),
(15, 'María Wilson', 'maríawilson14@example.com', 'Female', '1960-10-29', '2025-09-05T16:37:40'::timestamptz, 'Franklin', 'PA', '79822', 'standard', 'none', 1);

SELECT setval(pg_get_serial_sequence('public.customers','customer_id'), (SELECT MAX(customer_id) FROM public.customers));

INSERT INTO public.orders (order_id, customer_id, order_datetime, billing_zip, shipping_zip, shipping_state, payment_method, device_type, ip_country, promo_used, promo_code, order_subtotal, shipping_fee, tax_amount, order_total, risk_score, is_fraud, needs_review, priority_rank, scored_at) VALUES
(1, 1, '2025-11-29T00:51:07'::timestamptz, '28289', '28289', 'CO', 'card', 'mobile', 'US', 0, NULL, 662.95, 15.44, 46.3, 724.69, 38.3, 0, NULL, NULL, NULL),
(2, 1, '2025-09-01T10:25:59'::timestamptz, '28289', '13888', 'NY', 'card', 'desktop', 'US', 1, 'SAVE10', 862.92, 14.74, 66.61, 944.27, 94.9, 0, NULL, NULL, NULL),
(3, 1, '2025-12-15T07:24:41'::timestamptz, '28289', '28289', 'CO', 'card', 'mobile', 'US', 0, NULL, 796.09, 14.04, 40.72, 850.85, 53.8, 1, NULL, NULL, NULL),
(4, 1, '2025-11-06T18:21:19'::timestamptz, '28289', '28289', 'CO', 'bank', 'mobile', 'US', 1, 'WELCOME', 137.6, 6.99, 11.88, 156.47, 4.2, 0, NULL, NULL, NULL),
(5, 1, '2025-11-30T05:34:15'::timestamptz, '28289', '28289', 'CO', 'card', 'mobile', 'CA', 0, NULL, 17.07, 6.99, 1.4, 25.46, 4.9, 0, NULL, NULL, NULL),
(6, 1, '2025-12-11T10:04:54'::timestamptz, '28289', '28289', 'CO', 'paypal', 'tablet', 'NG', 0, NULL, 432.8, 8.39, 30.11, 471.3, 20.7, 0, NULL, NULL, NULL),
(7, 1, '2025-12-05T11:53:08'::timestamptz, '28289', '28289', 'CO', 'paypal', 'desktop', 'GB', 0, NULL, 644.08, 7.34, 57.48, 708.9, 51.1, 0, NULL, NULL, NULL),
(8, 1, '2025-11-13T16:06:51'::timestamptz, '28289', '28289', 'CO', 'card', 'desktop', 'US', 1, 'SAVE10', 721.34, 8.74, 48.0, 778.08, 47.3, 0, NULL, NULL, NULL),
(9, 1, '2025-09-08T01:03:20'::timestamptz, '28289', '80202', 'NY', 'bank', 'tablet', 'US', 0, NULL, 342.78, 6.99, 25.44, 375.21, 28.4, 0, NULL, NULL, NULL),
(10, 1, '2025-08-07T07:40:47'::timestamptz, '28289', '28289', 'CO', 'card', 'desktop', 'US', 0, NULL, 142.09, 8.39, 13.28, 163.76, 7.0, 0, NULL, NULL, NULL),
(11, 1, '2025-12-21T08:55:12'::timestamptz, '28289', '28289', 'CO', 'paypal', 'desktop', 'US', 0, NULL, 69.84, 7.69, 6.16, 83.69, 1.4, 0, NULL, NULL, NULL),
(12, 1, '2025-09-23T15:06:50'::timestamptz, '28289', '47098', 'WA', 'paypal', 'mobile', 'US', 0, NULL, 696.48, 7.69, 64.12, 768.29, 83.8, 0, NULL, NULL, NULL),
(13, 1, '2025-11-21T20:00:56'::timestamptz, '28289', '28289', 'CO', 'bank', 'mobile', 'US', 1, 'SAVE10', 555.52, 26.39, 38.45, 620.36, 23.2, 0, NULL, NULL, NULL),
(14, 1, '2025-08-01T11:30:13'::timestamptz, '28289', '28289', 'CO', 'paypal', 'desktop', 'IN', 0, NULL, 121.68, 13.69, 10.33, 145.7, 12.2, 0, NULL, NULL, NULL),
(15, 1, '2025-12-24T15:20:03'::timestamptz, '28289', '28289', 'CO', 'card', 'desktop', 'US', 1, 'SAVE10', 15.29, 6.99, 1.12, 23.4, 2.0, 0, NULL, NULL, NULL),
(16, 1, '2025-09-22T06:00:37'::timestamptz, '28289', '28289', 'CO', 'paypal', 'mobile', 'US', 1, 'SAVE10', 735.85, 8.39, 60.43, 804.67, 73.6, 0, NULL, NULL, NULL),
(17, 1, '2025-08-13T18:35:01'::timestamptz, '28289', '28289', 'CO', 'paypal', 'mobile', 'US', 0, NULL, 42.64, 6.99, 2.3, 51.93, 4.1, 0, NULL, NULL, NULL),
(18, 1, '2025-08-12T00:21:23'::timestamptz, '28289', '28289', 'CO', 'bank', 'mobile', 'US', 0, NULL, 1043.0, 9.09, 62.0, 1114.09, 86.7, 1, NULL, NULL, NULL),
(19, 1, '2025-08-06T04:50:43'::timestamptz, '28289', '28289', 'CO', 'paypal', 'tablet', 'US', 1, 'WELCOME', 102.65, 7.34, 5.89, 115.88, 6.2, 0, NULL, NULL, NULL),
(20, 1, '2025-07-23T09:27:07'::timestamptz, '28289', '28289', 'CO', 'card', 'desktop', 'US', 0, NULL, 431.83, 8.74, 23.1, 463.67, 25.3, 0, NULL, NULL, NULL),
(21, 1, '2025-09-11T15:32:42'::timestamptz, '28289', '28289', 'CO', 'card', 'mobile', 'US', 0, NULL, 1105.66, 7.69, 102.64, 1215.99, 95.2, 0, NULL, NULL, NULL),
(22, 1, '2025-07-28T05:52:44'::timestamptz, '28289', '28289', 'CO', 'paypal', 'desktop', 'US', 0, NULL, 8.68, 12.99, 0.5, 22.17, 2.7, 0, NULL, NULL, NULL),
(23, 1, '2025-10-10T06:57:54'::timestamptz, '28289', '28289', 'CO', 'card', 'desktop', 'US', 0, NULL, 287.76, 13.34, 27.01, 328.11, 14.7, 0, NULL, NULL, NULL),
(24, 1, '2025-12-11T17:45:45'::timestamptz, '28289', '28289', 'CO', 'card', 'tablet', 'US', 0, NULL, 445.0, 8.04, 28.51, 481.55, 14.3, 0, NULL, NULL, NULL),
(25, 1, '2025-08-10T18:06:38'::timestamptz, '28289', '28289', 'CO', 'card', 'mobile', 'CA', 0, NULL, 391.3, 12.99, 21.97, 426.26, 55.8, 0, NULL, NULL, NULL),
(26, 1, '2025-11-06T08:43:53'::timestamptz, '28289', '28289', 'CO', 'paypal', 'mobile', 'US', 0, NULL, 279.22, 8.74, 21.62, 309.58, 7.9, 0, NULL, NULL, NULL),
(27, 1, '2026-01-01T04:38:04'::timestamptz, '28289', '28289', 'CO', 'card', 'desktop', 'US', 0, NULL, 274.23, 15.09, 24.3, 313.62, 5.6, 0, NULL, NULL, NULL),
(28, 1, '2025-08-20T22:04:46'::timestamptz, '28289', '28289', 'CO', 'bank', 'tablet', 'US', 0, NULL, 196.02, 7.69, 16.17, 219.88, 5.2, 0, NULL, NULL, NULL),
(29, 1, '2025-07-26T03:33:44'::timestamptz, '28289', '28289', 'CO', 'bank', 'mobile', 'CA', 1, 'WELCOME', 228.5, 12.99, 16.94, 258.43, 26.7, 0, NULL, NULL, NULL),
(30, 1, '2025-07-10T19:42:19'::timestamptz, '28289', '28289', 'CO', 'bank', 'mobile', 'US', 1, 'STUDENT', 1030.78, 10.14, 74.22, 1115.14, 90.7, 0, NULL, NULL, NULL);

SELECT setval(pg_get_serial_sequence('public.orders','order_id'), (SELECT MAX(order_id) FROM public.orders));
