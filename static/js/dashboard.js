// Dashboard API Handler
class DashboardAPI {
    static async getDashboardStats() {
        try {
            this.showLoading();
            const response = await fetch('/api/dashboard/stats');
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            }
            throw new Error(data.message);
        } catch (error) {
            console.error('Error fetching dashboard stats:', error);
            this.showError('Failed to load dashboard data. Please try again.');
            return null;
        } finally {
            this.hideLoading();
        }
    }

    static async searchDashboard(query) {
        try {
            this.showLoading();
            const response = await fetch(`/api/dashboard/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            }
            throw new Error(data.message);
        } catch (error) {
            console.error('Error searching dashboard:', error);
            this.showError('Search failed. Please try again.');
            return [];
        } finally {
            this.hideLoading();
        }
    }

    static showLoading() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) spinner.classList.remove('hidden');
    }

    static hideLoading() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) spinner.classList.add('hidden');
    }

    static showError(message) {
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.querySelector('span').textContent = message;
            errorElement.classList.remove('hidden');
            setTimeout(() => {
                errorElement.classList.add('hidden');
            }, 5000);
        }
    }
}

// Dashboard Display Handler
class DashboardDisplay {
    static async initialize() {
        try {
            const stats = await DashboardAPI.getDashboardStats();
            if (!stats) return;

            // Clear any existing charts
            this.clearCharts();

            // Display all sections
            this.displayOverview(stats);
            this.displayBrandDistribution(stats.brands);
            this.displayPriceDistribution(stats.price_ranges);
            this.displayFuelTypeDistribution(stats.fuel_types);
            this.displayTransmissionDistribution(stats.transmissions);
            this.displayTopPerformers(stats.top_power, stats.top_mileage);
            this.setupSearch();
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            DashboardAPI.showError('Failed to initialize dashboard. Please refresh the page.');
        }
    }

    static clearCharts() {
        const chartIds = ['brandChart', 'priceChart', 'fuelChart', 'transmissionChart'];
        chartIds.forEach(id => {
            const canvas = document.getElementById(id);
            if (canvas) {
                const chart = Chart.getChart(canvas);
                if (chart) chart.destroy();
            }
        });
    }

    static displayOverview(stats) {
        const overviewContainer = document.getElementById('overviewContainer');
        if (!overviewContainer) return;

        overviewContainer.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Total Cars</h3>
                    <p class="text-3xl font-bold text-blue-600">${stats.total_cars}</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Total Brands</h3>
                    <p class="text-3xl font-bold text-green-600">${stats.brands.length}</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Average Price</h3>
                    <p class="text-3xl font-bold text-purple-600">₹${(stats.avg_prices[0]?.avg_price || 0).toLocaleString()}</p>
                </div>
            </div>
        `;
    }

    static displayBrandDistribution(brands) {
        const ctx = document.getElementById('brandChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: brands.map(b => b._id),
                datasets: [{
                    label: 'Number of Cars',
                    data: brands.map(b => b.count),
                    backgroundColor: 'rgba(59, 130, 246, 0.5)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Car Distribution by Brand'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    static displayPriceDistribution(priceRanges) {
        const ctx = document.getElementById('priceChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: priceRanges.map(r => r._id),
                datasets: [{
                    data: priceRanges.map(r => r.count),
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.5)',
                        'rgba(16, 185, 129, 0.5)',
                        'rgba(245, 158, 11, 0.5)',
                        'rgba(239, 68, 68, 0.5)',
                        'rgba(139, 92, 246, 0.5)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Price Range Distribution'
                    }
                }
            }
        });
    }

    static displayFuelTypeDistribution(fuelTypes) {
        const ctx = document.getElementById('fuelChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: fuelTypes.map(f => f._id),
                datasets: [{
                    data: fuelTypes.map(f => f.count),
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.5)',
                        'rgba(16, 185, 129, 0.5)',
                        'rgba(245, 158, 11, 0.5)',
                        'rgba(239, 68, 68, 0.5)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Fuel Type Distribution'
                    }
                }
            }
        });
    }

    static displayTransmissionDistribution(transmissions) {
        const ctx = document.getElementById('transmissionChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: transmissions.map(t => t._id),
                datasets: [{
                    label: 'Number of Cars',
                    data: transmissions.map(t => t.count),
                    backgroundColor: 'rgba(139, 92, 246, 0.5)',
                    borderColor: 'rgb(139, 92, 246)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Transmission Type Distribution'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    static displayTopPerformers(topPower, topMileage) {
        const powerContainer = document.getElementById('topPowerContainer');
        const mileageContainer = document.getElementById('topMileageContainer');
        
        if (powerContainer) {
            powerContainer.innerHTML = `
                <h3 class="text-lg font-semibold text-gray-800 mb-4">Top Power Cars</h3>
                <div class="space-y-4">
                    ${topPower.map(car => `
                        <div class="bg-white rounded-lg shadow p-4">
                            <div class="flex justify-between items-center">
                                <div>
                                    <h4 class="font-semibold text-gray-800">${car.car_company} ${car.car_model}</h4>
                                    <p class="text-sm text-gray-600">${car.year}</p>
                                </div>
                                <span class="text-lg font-bold text-blue-600">${car.max_power}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        if (mileageContainer) {
            mileageContainer.innerHTML = `
                <h3 class="text-lg font-semibold text-gray-800 mb-4">Top Mileage Cars</h3>
                <div class="space-y-4">
                    ${topMileage.map(car => `
                        <div class="bg-white rounded-lg shadow p-4">
                            <div class="flex justify-between items-center">
                                <div>
                                    <h4 class="font-semibold text-gray-800">${car.car_company} ${car.car_model}</h4>
                                    <p class="text-sm text-gray-600">${car.year}</p>
                                </div>
                                <span class="text-lg font-bold text-green-600">${car.mileage} kmpl</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }

    static setupSearch() {
        const searchInput = document.getElementById('dashboardSearch');
        if (!searchInput) return;

        searchInput.addEventListener('input', async (e) => {
            const query = e.target.value;
            if (query.length >= 2) {
                const results = await DashboardAPI.searchDashboard(query);
                this.displaySearchResults(results);
            }
        });
    }

    static displaySearchResults(results) {
        const searchContainer = document.getElementById('searchResults');
        if (!searchContainer) return;

        if (results.length === 0) {
            searchContainer.innerHTML = '<p class="text-gray-500">No results found</p>';
            return;
        }

        searchContainer.innerHTML = results.map(car => `
            <div class="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow cursor-pointer">
                <div class="flex justify-between items-center">
                    <div>
                        <h4 class="font-semibold text-gray-800">${car.car_company} ${car.car_model}</h4>
                        <p class="text-sm text-gray-600">${car.year}</p>
                    </div>
                    <span class="text-lg font-bold text-blue-600">₹${car.selling_price}</span>
                </div>
                <div class="mt-2 flex items-center gap-4 text-sm text-gray-500">
                    <span><i class="fas fa-engine mr-1"></i>${car.engine}</span>
                    <span><i class="fas fa-gas-pump mr-1"></i>${car.mileage}</span>
                    <span><i class="fas fa-bolt mr-1"></i>${car.max_power}</span>
                </div>
            </div>
        `).join('');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    DashboardDisplay.initialize();
}); 