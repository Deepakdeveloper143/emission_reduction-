document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = 'https://emission-reduction-model.onrender.com';

    const form = document.getElementById('prediction-form');
    const predictBtn = document.getElementById('predict-btn');
    const btnText = predictBtn.querySelector('span');
    const btnIcon = predictBtn.querySelector('i');
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-text');
    const errorMessage = document.getElementById('error-message');
    const toast = document.getElementById('toast');

    // Values Elements
    const valAnnualReduction = document.getElementById('val-annual-reduction');
    const valLifetimeReduction = document.getElementById('val-lifetime-reduction');
    const valCostTonne = document.getElementById('val-cost-tonne');
    const valCostSavings = document.getElementById('val-cost-savings');
    const valAdoption = document.getElementById('val-adoption');
    const adoptionProgress = document.getElementById('adoption-progress');

    // Chart instances
    let metricsChart = null;
    let adoptionChart = null;
    let scenarioChart = null;
    let historyChart = null;

    // ========== Chart.js Global Config ==========
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
    Chart.defaults.font.family = "'Inter', sans-serif";

    // ========== Number Animation ==========
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = progress * (end - start) + start;
            obj.innerHTML = current.toFixed(2);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    function showToast() {
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.classList.add('hidden'), 300);
        }, 4000);
    }

    // ========== Update Dashboard Cards ==========
    function updateDashboard(data) {
        document.querySelectorAll('.value').forEach(el => {
            el.classList.remove('updating');
            void el.offsetWidth;
            el.classList.add('updating');
        });

        const curAnnual = parseFloat(valAnnualReduction.innerText) || 0;
        const curLifetime = parseFloat(valLifetimeReduction.innerText) || 0;
        const curCostTonne = parseFloat(valCostTonne.innerText) || 0;
        const curCostSavings = parseFloat(valCostSavings.innerText) || 0;
        const curAdoption = parseFloat(valAdoption.innerText) || 0;

        animateValue(valAnnualReduction, curAnnual, data.annual_reduction, 1000);
        animateValue(valLifetimeReduction, curLifetime, data.lifetime_reduction, 1000);
        animateValue(valCostTonne, curCostTonne, data.cost_per_tonne, 1000);
        animateValue(valCostSavings, curCostSavings, data.cost_savings, 1000);
        animateValue(valAdoption, curAdoption, data.adoption, 1000);

        adoptionProgress.style.width = `${Math.min(data.adoption, 100)}%`;
        
        // Update charts
        updateMetricsChart(data);
        updateAdoptionChart(data.adoption);
        
        showToast();
    }

    // ========== CHART 1: Metrics Bar Chart ==========
    function createMetricsChart() {
        const ctx = document.getElementById('metricsBarChart').getContext('2d');
        metricsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Annual Reduction', 'Lifetime Reduction', 'Cost/Tonne', 'Cost Savings'],
                datasets: [{
                    label: 'Predicted Values',
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(139, 92, 246, 0.7)',
                        'rgba(245, 158, 11, 0.7)'
                    ],
                    borderColor: [
                        'rgba(16, 185, 129, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(139, 92, 246, 1)',
                        'rgba(245, 158, 11, 1)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 1200, easing: 'easeOutQuart' },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f8fafc',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.04)' },
                        ticks: { color: '#64748b' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', font: { size: 11 } }
                    }
                }
            }
        });
    }

    function updateMetricsChart(data) {
        if (!metricsChart) return;
        metricsChart.data.datasets[0].data = [
            data.annual_reduction,
            data.lifetime_reduction,
            data.cost_per_tonne,
            data.cost_savings
        ];
        metricsChart.update('active');
    }

    // ========== CHART 2: Adoption Doughnut ==========
    function createAdoptionChart() {
        const ctx = document.getElementById('adoptionDoughnut').getContext('2d');
        adoptionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Adoption', 'Remaining'],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: [
                        'rgba(249, 115, 22, 0.85)',
                        'rgba(255, 255, 255, 0.05)'
                    ],
                    borderColor: [
                        'rgba(249, 115, 22, 1)',
                        'rgba(255, 255, 255, 0.1)'
                    ],
                    borderWidth: 2,
                    cutout: '75%',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 1500, easing: 'easeOutBounce' },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        callbacks: {
                            label: (ctx) => `${ctx.label}: ${ctx.parsed.toFixed(1)}%`
                        }
                    }
                }
            }
        });
    }

    function updateAdoptionChart(adoption) {
        if (!adoptionChart) return;
        const val = Math.min(Math.max(adoption, 0), 100);
        adoptionChart.data.datasets[0].data = [val, 100 - val];
        
        // Dynamic color based on adoption
        let color;
        if (val >= 70) color = 'rgba(16, 185, 129, 0.85)';
        else if (val >= 40) color = 'rgba(245, 158, 11, 0.85)';
        else color = 'rgba(239, 68, 68, 0.85)';
        
        adoptionChart.data.datasets[0].backgroundColor[0] = color;
        adoptionChart.update('active');
        
        document.getElementById('doughnut-label').textContent = `${val.toFixed(0)}%`;
    }

    // ========== CHART 3: Scenario Comparison ==========
    function createScenarioChart() {
        const ctx = document.getElementById('scenarioChart').getContext('2d');
        scenarioChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Annual Reduction', 'Lifetime Reduction', 'Cost/Tonne', 'Cost Savings', 'Adoption (%)'],
                datasets: [
                    {
                        label: 'Low Scenario',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(59, 130, 246, 0.6)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'Medium Scenario',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(245, 158, 11, 0.6)',
                        borderColor: 'rgba(245, 158, 11, 1)',
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'High Scenario',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(16, 185, 129, 0.6)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 1000, easing: 'easeOutQuart' },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#94a3b8', usePointStyle: true, pointStyle: 'circle', padding: 20 }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f8fafc',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.04)' },
                        ticks: { color: '#64748b' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', font: { size: 11 } }
                    }
                }
            }
        });
    }

    async function fetchScenarioComparison() {
        const formData = new FormData(form);
        const params = new URLSearchParams({
            category: formData.get('category'),
            phase: formData.get('phase'),
            implementation_cost: formData.get('implementation_cost'),
            time: formData.get('time'),
            feasibility: formData.get('feasibility'),
            delivery: formData.get('delivery'),
            action: formData.get('action')
        });

        try {
            const res = await fetch(`${API_BASE}/compare-scenarios?${params}`);
            const result = await res.json();
            if (result.status === 'success') {
                const c = result.comparison;
                const toArray = (s) => [
                    c[s].annual_reduction,
                    c[s].lifetime_reduction,
                    c[s].cost_per_tonne,
                    c[s].cost_savings,
                    c[s].adoption
                ];
                scenarioChart.data.datasets[0].data = toArray('Low');
                scenarioChart.data.datasets[1].data = toArray('Medium');
                scenarioChart.data.datasets[2].data = toArray('High');
                scenarioChart.update('active');
            }
        } catch (err) {
            console.error('Scenario comparison failed:', err);
        }
    }

    // ========== CHART 4: History Line Chart ==========
    function createHistoryChart() {
        const ctx = document.getElementById('historyChart').getContext('2d');
        historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Annual Reduction (tCO2e/yr)',
                        data: [],
                        borderColor: 'rgba(16, 185, 129, 1)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 2
                    },
                    {
                        label: 'Cost Savings (£/yr)',
                        data: [],
                        borderColor: 'rgba(245, 158, 11, 1)',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: 'rgba(245, 158, 11, 1)',
                        borderWidth: 2
                    },
                    {
                        label: 'Adoption (%)',
                        data: [],
                        borderColor: 'rgba(139, 92, 246, 1)',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: 'rgba(139, 92, 246, 1)',
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 1200, easing: 'easeOutQuart' },
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#94a3b8', usePointStyle: true, pointStyle: 'circle', padding: 20 }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f8fafc',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.04)' },
                        ticks: { color: '#64748b' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', maxRotation: 45, font: { size: 10 } }
                    }
                }
            }
        });
    }

    async function fetchHistory() {
        try {
            const res = await fetch(`${API_BASE}/history?limit=20`);
            const result = await res.json();
            if (result.status === 'success' && result.records.length > 0) {
                const records = result.records.reverse(); // oldest first
                const labels = records.map((r, i) => {
                    const d = new Date(r.created_at);
                    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) + ' #' + (i + 1);
                });
                
                historyChart.data.labels = labels;
                historyChart.data.datasets[0].data = records.map(r => r.annual_reduction);
                historyChart.data.datasets[1].data = records.map(r => r.cost_savings);
                historyChart.data.datasets[2].data = records.map(r => r.adoption);
                historyChart.update('active');
            }
        } catch (err) {
            console.error('History fetch failed:', err);
        }
    }

    // ========== Initialize All Charts ==========
    createMetricsChart();
    createAdoptionChart();
    createScenarioChart();
    createHistoryChart();

    // Load history on startup
    fetchHistory();

    // Refresh history button
    document.getElementById('refresh-history-btn').addEventListener('click', fetchHistory);

    // ========== Form Submit ==========
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        predictBtn.disabled = true;
        btnText.innerText = 'Processing...';
        btnIcon.className = 'fa-solid fa-spinner fa-spin';
        statusIndicator.classList.add('processing');
        statusText.innerText = 'Analyzing Model...';
        errorMessage.style.display = 'none';

        const formData = new FormData(form);
        const payload = {
            category: formData.get('category'),
            phase: formData.get('phase'),
            scenario: formData.get('scenario'),
            implementation_cost: parseFloat(formData.get('implementation_cost')),
            time: formData.get('time'),
            feasibility: formData.get('feasibility'),
            delivery: formData.get('delivery'),
            action: formData.get('action')
        };

        try {
            const response = await fetch(`${API_BASE}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.status === 'success') {
                updateDashboard(result.predictions);
                // Also refresh scenario comparison and history
                fetchScenarioComparison();
                setTimeout(fetchHistory, 500);

                // Scroll charts into view
                document.getElementById('charts-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                throw new Error(result.message || 'Unknown error occurred');
            }

        } catch (error) {
            console.error('Prediction failed:', error);
            errorMessage.innerText = `Error: ${error.message}. Make sure the backend server is running.`;
            errorMessage.style.display = 'block';
        } finally {
            predictBtn.disabled = false;
            btnText.innerText = 'Run Simulation';
            btnIcon.className = 'fa-solid fa-bolt';
            statusIndicator.classList.remove('processing');
            statusText.innerText = 'Ready';
        }
    });

    // Initialize values
    setTimeout(() => {
        document.querySelectorAll('.value').forEach(el => el.innerText = "0.00");
    }, 100);
});
