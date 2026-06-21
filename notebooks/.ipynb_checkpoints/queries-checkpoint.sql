-- 01_select_limit
SELECT * FROM superstore LIMIT 10;

-- 02_where
SELECT * FROM superstore WHERE Sales > 1000;

-- 03_order_by
SELECT * FROM superstore ORDER BY Sales DESC LIMIT 10;

-- 04_aggregate_functions
SELECT COUNT(*) AS Total_Orders, SUM(Sales) AS Total_Sales, AVG(Sales) AS Average_Sales, MIN(Sales) AS Minimum_Sales, MAX(Sales) AS Maximum_Sales FROM superstore;

-- 05_group_by
SELECT Category, SUM(Sales) AS Total_Sales FROM superstore GROUP BY Category;

-- 06_having
SELECT Category, SUM(Sales) AS Total_Sales FROM superstore GROUP BY Category HAVING SUM(Sales) > 500000;

-- 07_subquery
SELECT * FROM superstore WHERE Sales > (SELECT AVG(Sales) FROM superstore);

-- 08_cte
WITH CategorySales AS (SELECT Category, SUM(Sales) AS Total_Sales FROM superstore GROUP BY Category) SELECT * FROM CategorySales;

-- 09_row_number
SELECT Category, Sales, ROW_NUMBER() OVER(PARTITION BY Category ORDER BY Sales DESC) AS Row_Num FROM superstore;

-- 10_rank
SELECT Category, Sales, RANK() OVER(PARTITION BY Category ORDER BY Sales DESC) AS Sales_Rank FROM superstore;

-- 11a_inner_join
SELECT cs.Category, cs.Total_Sales, ct.Sales_Target FROM (SELECT Category, ROUND(SUM(Sales),2) AS Total_Sales FROM superstore GROUP BY Category) AS cs INNER JOIN category_targets AS ct ON cs.Category = ct.Category;

-- 11b_left_join
SELECT cs.Category, cs.Total_Sales, ct.Sales_Target FROM (SELECT Category, ROUND(SUM(Sales),2) AS Total_Sales FROM superstore GROUP BY Category) AS cs LEFT JOIN category_targets AS ct ON cs.Category = ct.Category;

-- 11c_right_join
SELECT cs.Category, cs.Total_Sales, ct.Sales_Target FROM (SELECT Category, ROUND(SUM(Sales),2) AS Total_Sales FROM superstore GROUP BY Category) AS cs RIGHT JOIN category_targets AS ct ON cs.Category = ct.Category;

-- 11d_full_outer_join
SELECT cs.Category, cs.Total_Sales, ct.Sales_Target FROM (SELECT Category, ROUND(SUM(Sales),2) AS Total_Sales FROM superstore GROUP BY Category) AS cs FULL OUTER JOIN category_targets AS ct ON cs.Category = ct.Category;

-- 12_monthly_sales_trends
SELECT substr([Order Date], 6, 2) AS Month, ROUND(SUM(Sales),2) AS Total_Sales FROM superstore GROUP BY Month ORDER BY Month;

-- 13_top_customers
SELECT [Customer Name], ROUND(SUM(Sales),2) AS Total_Revenue FROM superstore GROUP BY [Customer Name] ORDER BY Total_Revenue DESC LIMIT 10;

-- 14_category_performance
SELECT Category, ROUND(SUM(Sales),2) AS Total_Sales, ROUND(SUM(Profit),2) AS Total_Profit FROM superstore GROUP BY Category ORDER BY Total_Profit DESC;

-- 15a_frequent_buyers
SELECT [Customer Name], COUNT(DISTINCT [Order ID]) AS Total_Orders FROM superstore GROUP BY [Customer Name] HAVING COUNT(DISTINCT [Order ID]) > 5 ORDER BY Total_Orders DESC;

-- 15b_retention_rate
WITH CustomerOrders AS (SELECT [Customer Name], COUNT(DISTINCT [Order ID]) AS Total_Orders FROM superstore GROUP BY [Customer Name]) SELECT COUNT(*) AS Total_Customers, SUM(CASE WHEN Total_Orders > 1 THEN 1 ELSE 0 END) AS Repeat_Customers, ROUND(100.0 * SUM(CASE WHEN Total_Orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS Retention_Rate_Percent FROM CustomerOrders;

-- 16_lag
SELECT [Order Date], Sales, LAG(Sales) OVER(ORDER BY [Order Date]) AS Previous_Sale FROM superstore LIMIT 20;

-- 17_lead
SELECT [Order Date], Sales, LEAD(Sales) OVER(ORDER BY [Order Date]) AS Next_Sale FROM superstore LIMIT 20;

-- 18_moving_avg_cumulative_sum
SELECT [Order Date], Sales, ROUND(AVG(Sales) OVER (ORDER BY [Order Date] ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS Moving_Avg_7, ROUND(SUM(Sales) OVER (ORDER BY [Order Date]), 2) AS Cumulative_Sales FROM superstore LIMIT 20;

-- 19_create_view
CREATE VIEW IF NOT EXISTS CategorySummary AS SELECT Category, SUM(Sales) AS Total_Sales, SUM(Profit) AS Total_Profit FROM superstore GROUP BY Category;

-- 20_explain_query_plan
EXPLAIN QUERY PLAN SELECT * FROM superstore WHERE [Customer Name] = 'Sean Miller';

-- 21_parameterised_query
SELECT * FROM superstore WHERE [Customer Name] = ?

