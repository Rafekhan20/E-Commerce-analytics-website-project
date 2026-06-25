// E-Commerce Dashboard Javascript Integration

document.addEventListener("DOMContentLoaded", () => {
    // Initialize icons
    lucide.createIcons();

    // Global references to charts to destroy them on update if needed
    let revenueTrendChart = null;
    let categoryShareChart = null;
    let revenueMarginDetailChart = null;
    let channelRevenueChart = null;
    let topProductsChart = null;

    // --- TAB SYSTEM ---
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");

    const tabConfig = {
        "overview": { title: "Overview Dashboard", subtitle: "Real-time business performance overview" },
        "revenue": { title: "Revenue & Margin Analysis", subtitle: "Deep dive into monthly sales and profit channels" },
        "products": { title: "Product Performance", subtitle: "Analyze sales distributions, categories and stock turnovers" },
        "behavior": { title: "Customer Behavior Analysis", subtitle: "Analyze shopping funnels and customer cohorts retention" },
        "sql-playground": { title: "SQL Playpen", subtitle: "Write custom queries directly against the database" },
        "power-bi": { title: "Power BI Integration", subtitle: "Detailed guide and dataset tools for Power BI Desktop" }
    };

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute("data-tab");

            // Update nav active state
            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");

            // Update tab panes visibility
            tabPanes.forEach(pane => {
                pane.classList.remove("active");
                if (pane.id === `${targetTab}-tab`) {
                    pane.classList.add("active");
                }
            });

            // Update Header text
            if (tabConfig[targetTab]) {
                pageTitle.textContent = tabConfig[targetTab].title;
                pageSubtitle.textContent = tabConfig[targetTab].subtitle;
            }

            // Load relevant tab data on demand to optimize performance
            loadTabData(targetTab);
        });
    });

    // --- DATA LOADING TRIGGER ---
    function loadTabData(tabName) {
        switch (tabName) {
            case "overview":
                fetchKPIs();
                fetchOverviewCharts();
                break;
            case "revenue":
                fetchRevenueAnalysis();
                break;
            case "products":
                fetchProductPerformance();
                break;
            case "behavior":
                fetchCustomerBehavior();
                break;
            case "sql-playground":
                // Set initial sample query if editor is empty
                const sqlInput = document.getElementById("sql-input");
                if (!sqlInput.value.trim()) {
                    sqlInput.value = sqlPresets["q1"];
                }
                break;
        }
    }

    // --- 1. OVERVIEW DATA ---
    function fetchKPIs() {
        fetch("/api/kpis")
            .then(res => res.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                
                document.getElementById("kpi-revenue").textContent = formatCurrency(data.total_revenue);
                document.getElementById("kpi-orders").textContent = formatNumber(data.total_orders);
                document.getElementById("kpi-conversion").textContent = `${data.conversion_rate.toFixed(2)}%`;
                document.getElementById("kpi-aov").textContent = formatCurrency(data.average_order_value);
            })
            .catch(err => console.error("Error fetching KPIs:", err));
    }

    function fetchOverviewCharts() {
        // Fetch revenue trends
        fetch("/api/revenue-trends")
            .then(res => res.json())
            .then(data => {
                const labels = data.map(item => item.order_month);
                const revenues = data.map(item => item.monthly_revenue);
                const profits = data.map(item => item.monthly_profit);

                if (revenueTrendChart) revenueTrendChart.destroy();

                const ctx = document.getElementById("revenueTrendChart").getContext("2d");
                revenueTrendChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Monthly Revenue',
                                data: revenues,
                                borderColor: '#3b82f6',
                                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                fill: true,
                                tension: 0.3,
                                borderWidth: 3
                            },
                            {
                                label: 'Gross Profit',
                                data: profits,
                                borderColor: '#10b981',
                                backgroundColor: 'transparent',
                                tension: 0.3,
                                borderWidth: 3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#f3f4f6' }
                            }
                        },
                        scales: {
                            y: {
                                grid: { color: '#374151' },
                                ticks: { color: '#9ca3af' }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: '#9ca3af' }
                            }
                        }
                    }
                });
            });

        // Fetch categories for share chart
        fetch("/api/category-performance")
            .then(res => res.json())
            .then(data => {
                const labels = data.map(item => item.category);
                const revenues = data.map(item => item.revenue);

                if (categoryShareChart) categoryShareChart.destroy();

                const ctx = document.getElementById("categoryShareChart").getContext("2d");
                categoryShareChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: revenues,
                            backgroundColor: [
                                '#6366f1', // Indigo
                                '#10b981', // Emerald
                                '#ec4899', // Pink
                                '#f59e0b', // Amber
                                '#3b82f6', // Blue
                                '#a855f7'  // Purple
                            ],
                            borderWidth: 2,
                            borderColor: '#1f2937'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: { color: '#f3f4f6', boxWidth: 15 }
                            }
                        }
                    }
                });
            });
    }

    // --- 2. REVENUE ANALYSIS DATA ---
    function fetchRevenueAnalysis() {
        // Detailed revenue margins chart
        fetch("/api/revenue-trends")
            .then(res => res.json())
            .then(data => {
                const labels = data.map(item => item.order_month);
                const margins = data.map(item => item.profit_margin_percent);
                const revenues = data.map(item => item.monthly_revenue);

                if (revenueMarginDetailChart) revenueMarginDetailChart.destroy();

                const ctx = document.getElementById("revenueMarginDetailChart").getContext("2d");
                revenueMarginDetailChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                type: 'bar',
                                label: 'Revenue ($)',
                                data: revenues,
                                backgroundColor: 'rgba(99, 102, 241, 0.7)',
                                yAxisID: 'y'
                            },
                            {
                                type: 'line',
                                label: 'Margin %',
                                data: margins,
                                borderColor: '#ec4899',
                                borderWidth: 3,
                                fill: false,
                                tension: 0.2,
                                yAxisID: 'y1'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { labels: { color: '#f3f4f6' } }
                        },
                        scales: {
                            y: {
                                position: 'left',
                                grid: { color: '#374151' },
                                ticks: { color: '#9ca3af' }
                            },
                            y1: {
                                position: 'right',
                                grid: { display: false },
                                ticks: { color: '#9ca3af', callback: val => `${val}%` }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: '#9ca3af' }
                            }
                        }
                    }
                });
            });

        // Revenue by acquisition channels
        fetch("/api/channels")
            .then(res => res.json())
            .then(data => {
                const labels = data.map(item => item.acquisition_channel);
                const revenues = data.map(item => item.total_revenue);

                if (channelRevenueChart) channelRevenueChart.destroy();

                const ctx = document.getElementById("channelRevenueChart").getContext("2d");
                channelRevenueChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Total Revenue ($)',
                            data: revenues,
                            backgroundColor: [
                                '#3b82f6', '#10b981', '#a855f7', '#f59e0b', '#ec4899', '#6b7280'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                grid: { color: '#374151' },
                                ticks: { color: '#9ca3af' }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: '#9ca3af' }
                            }
                        }
                    }
                });

                // Populate channels table
                const tbody = document.querySelector("#channels-table tbody");
                tbody.innerHTML = "";
                data.forEach(row => {
                    const tr = document.createElement("tr");
                    const aov = row.total_orders > 0 ? (row.total_revenue / row.total_orders).toFixed(2) : "0.00";
                    tr.innerHTML = `
                        <td><strong>${row.acquisition_channel}</strong></td>
                        <td>${formatNumber(row.total_users)}</td>
                        <td>${formatNumber(row.total_orders)}</td>
                        <td>${formatCurrency(row.total_revenue)}</td>
                        <td>${formatCurrency(aov)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            });
    }

    // --- 3. PRODUCT PERFORMANCE DATA ---
    function fetchProductPerformance() {
        // Top 10 products chart
        fetch("/api/top-products")
            .then(res => res.json())
            .then(data => {
                const labels = data.map(item => item.product_name);
                const revenues = data.map(item => item.total_revenue);

                if (topProductsChart) topProductsChart.destroy();

                const ctx = document.getElementById("topProductsChart").getContext("2d");
                topProductsChart = new Chart(ctx, {
                    type: 'run_horizontal_bar', // Standard horizontal bar configuration
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Revenue ($)',
                            data: revenues,
                            backgroundColor: 'rgba(16, 185, 129, 0.8)',
                            borderColor: '#10b981',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        indexAxis: 'y', // Makes it a horizontal bar
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            x: {
                                grid: { color: '#374151' },
                                ticks: { color: '#9ca3af' }
                            },
                            y: {
                                grid: { display: false },
                                ticks: { color: '#9ca3af' }
                            }
                        }
                    }
                });

                // Populate Top Products table
                const tbody = document.querySelector("#top-products-table tbody");
                tbody.innerHTML = "";
                data.forEach(row => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>${row.product_name}</strong></td>
                        <td><span class="category-tag">${row.category}</span></td>
                        <td>${row.units_sold}</td>
                        <td>${formatCurrency(row.total_revenue)}</td>
                        <td>${formatCurrency(row.total_profit)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            });

        // Category breakdown table
        fetch("/api/category-performance")
            .then(res => res.json())
            .then(data => {
                const tbody = document.querySelector("#category-summary-table tbody");
                tbody.innerHTML = "";
                data.forEach(row => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>${row.category}</strong></td>
                        <td>${formatNumber(row.orders_count)}</td>
                        <td>${formatNumber(row.units_sold)}</td>
                        <td>${formatCurrency(row.revenue)}</td>
                        <td>${formatCurrency(row.gross_profit)}</td>
                        <td>${row.margin_percent.toFixed(1)}%</td>
                    `;
                    tbody.appendChild(tr);
                });
            });
    }

    // --- 4. CUSTOMER BEHAVIOR DATA ---
    function fetchCustomerBehavior() {
        // Funnel fetch
        fetch("/api/funnel")
            .then(res => res.json())
            .then(data => {
                const container = document.getElementById("funnel-visual");
                container.innerHTML = "";

                const stages = [
                    { name: "Total Sessions", count: data.total_sessions, base: data.total_sessions },
                    { name: "Product Views", count: data.sessions_with_product_view, base: data.total_sessions },
                    { name: "Add to Cart", count: data.sessions_with_cart_add, base: data.total_sessions },
                    { name: "Purchases", count: data.sessions_with_purchase, base: data.total_sessions }
                ];

                stages.forEach((stage, idx) => {
                    const conversionVal = stage.base > 0 ? (stage.count / stage.base * 100).toFixed(1) : "0.0";
                    const stagePercentOfPrev = idx === 0 ? "100.0" : stages[idx-1].count > 0 ? (stage.count / stages[idx-1].count * 100).toFixed(1) : "0.0";
                    
                    const div = document.createElement("div");
                    div.className = "funnel-stage";
                    div.innerHTML = `
                        <div class="funnel-fill" style="width: ${conversionVal}%"></div>
                        <div class="funnel-stage-content">
                            <span>${stage.name}</span>
                            <div>
                                <strong style="margin-right: 15px;">${formatNumber(stage.count)}</strong>
                                <span class="funnel-meta">${idx === 0 ? 'Base' : `${stagePercentOfPrev}% step conversion`}</span>
                            </div>
                        </div>
                    `;
                    container.appendChild(div);
                });
            });

        // Cohort table fetch
        fetch("/api/cohorts")
            .then(res => res.json())
            .then(data => {
                const tbody = document.querySelector("#cohort-table tbody");
                tbody.innerHTML = "";

                data.forEach(row => {
                    const tr = document.createElement("tr");
                    
                    // Cohort headers
                    let html = `
                        <td><strong>${row.cohort_month}</strong></td>
                        <td>${formatNumber(row.size)}</td>
                    `;

                    // Generate months 0 to 6
                    for (let m = 0; m <= 6; m++) {
                        const val = row.retention[m];
                        if (val !== undefined) {
                            const opacity = (val / 100).toFixed(2);
                            // Heatmap color: Purple overlay on white/slate text
                            const bgStyle = `style="background-color: rgba(99, 102, 241, ${opacity});"`;
                            html += `<td class="heatmap-cell" ${bgStyle}>${val.toFixed(1)}%</td>`;
                        } else {
                            html += `<td class="heatmap-cell text-muted">-</td>`;
                        }
                    }

                    tr.innerHTML = html;
                    tbody.appendChild(tr);
                });
            });
    }

    // --- 5. SQL PLAYGROUND ---
    const sqlPresets = {
        "q1": `-- Pre-filled Sample: Quick user lookup\nSELECT user_id, signup_date, first_name, last_name, state, acquisition_channel \nFROM users \nLIMIT 10;`,
        "q2": `-- Pre-filled Sample: Product performance metrics\nSELECT p.product_name, p.category, SUM(oi.quantity) as total_units_sold, ROUND(SUM(oi.quantity * oi.unit_price), 2) as revenue\nFROM order_items oi\nJOIN products p ON oi.product_id = p.product_id\nGROUP BY p.product_id\nORDER BY revenue DESC\nLIMIT 5;`,
        "q3": `-- Pre-filled Sample: Shopping Conversion Funnel analysis\nWITH session_events AS (\n    SELECT session_id,\n           MAX(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) AS home,\n           MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS view,\n           MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS cart,\n           MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS buy\n    FROM web_events\n    GROUP BY session_id\n)\nSELECT COUNT(*) as total_sessions, SUM(view) as views, SUM(cart) as cart_adds, SUM(buy) as orders\nFROM session_events;`,
        "q4": `-- Pre-filled Sample: RFM customer segmentation\nSELECT user_id, first_name || ' ' || last_name as name, age, state, acquisition_channel\nFROM users\nORDER BY user_id DESC\nLIMIT 10;`
    };

    const qSelector = document.getElementById("sample-queries");
    const sqlInput = document.getElementById("sql-input");
    const runSqlBtn = document.getElementById("btn-run-sql");
    const outputContainer = document.getElementById("sql-output-container");
    const sqlMeta = document.getElementById("sql-meta");

    // Swap preset queries
    qSelector.addEventListener("change", () => {
        const val = qSelector.value;
        if (sqlPresets[val]) {
            sqlInput.value = sqlPresets[val];
        }
    });

    // Execute SQL
    runSqlBtn.addEventListener("click", () => {
        const queryText = sqlInput.value.trim();
        if (!queryText) return;

        sqlMeta.textContent = "Running query...";
        runSqlBtn.disabled = true;

        fetch("/api/sql", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: queryText })
        })
        .then(res => res.json())
        .then(data => {
            runSqlBtn.disabled = false;
            if (data.error) {
                renderSqlError(data.error);
                sqlMeta.textContent = "Error occurred";
            } else {
                renderSqlTable(data);
                sqlMeta.textContent = `Returned ${data.row_count} rows ${data.has_more ? '(capped at 100)' : ''}`;
            }
        })
        .catch(err => {
            runSqlBtn.disabled = false;
            renderSqlError(err.message || err);
            sqlMeta.textContent = "Request failed";
        });
    });

    function renderSqlTable(data) {
        if (!data.columns || data.columns.length === 0) {
            outputContainer.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="check-circle" style="color: #10b981;"></i>
                    <p>Query executed successfully. (No results returned)</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        let tableHtml = `
            <div class="table-container" style="max-height: 100%;">
                <table class="data-table">
                    <thead>
                        <tr>
                            ${data.columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.rows.map(row => `
                            <tr>
                                ${row.map(val => `<td>${val !== null ? val : '<span class="text-muted">null</span>'}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        outputContainer.innerHTML = tableHtml;
    }

    function renderSqlError(errorMsg) {
        outputContainer.innerHTML = `
            <div class="error-panel" style="padding: 20px; border: 1px solid #ef4444; border-radius: 8px; background-color: rgba(239, 68, 68, 0.05); color: #fca5a5; font-family: monospace; white-space: pre-wrap;">
                <strong>SQL Error:</strong><br><br>${errorMsg}
            </div>
        `;
    }

    // --- 6. POWER BI CSV EXPORTER ---
    const btnExportCsv = document.getElementById("btn-export-csv");
    
    btnExportCsv.addEventListener("click", () => {
        btnExportCsv.disabled = true;
        btnExportCsv.textContent = "Exporting Data...";

        fetch("/api/export-csv", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                btnExportCsv.disabled = false;
                btnExportCsv.innerHTML = `<i data-lucide="check"></i> Export Completed!`;
                setTimeout(() => {
                    btnExportCsv.innerHTML = `<i data-lucide="download"></i> Export CSV Dataset`;
                    lucide.createIcons();
                }, 4000);
                alert(`Success! Generated dataset tables successfully inside "power_bi/data/" directory.`);
            })
            .catch(err => {
                btnExportCsv.disabled = false;
                btnExportCsv.innerHTML = `<i data-lucide="alert-triangle"></i> Export Failed`;
                console.error("Export error:", err);
                alert(`Error running exporter: ${err.message || err}`);
            });
    });

    // --- HELPERS ---
    function formatCurrency(val) {
        if (val === null || val === undefined) return "$0.00";
        return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);
    }

    function formatNumber(val) {
        if (val === null || val === undefined) return "0";
        return new Intl.NumberFormat("en-US").format(val);
    }

    // Trigger initial data load
    loadTabData("overview");
});
