// Car Details API Handler
class CarDetailsAPI {
    static async getAllCars() {
        try {
            const response = await fetch('/api/cars');
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            }
            throw new Error(data.message);
        } catch (error) {
            console.error('Error fetching cars:', error);
            return [];
        }
    }

    static async getCarById(carId) {
        try {
            const response = await fetch(`/api/cars/${carId}`);
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            }
            throw new Error(data.message);
        } catch (error) {
            console.error('Error fetching car details:', error);
            return null;
        }
    }

    static async getCarsByBrand(brand) {
        try {
            const response = await fetch(`/api/cars/brand/${brand}`);
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            }
            throw new Error(data.message);
        } catch (error) {
            console.error('Error fetching cars by brand:', error);
            return [];
        }
    }

    static async searchCars(query) {
        try {
            const response = await fetch(`/api/cars/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            }
            throw new Error(data.message);
        } catch (error) {
            console.error('Error searching cars:', error);
            return [];
        }
    }

    static async getCarStats() {
        try {
            const response = await fetch('/api/cars/stats');
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            }
            throw new Error(data.message);
        } catch (error) {
            console.error('Error fetching car stats:', error);
            return null;
        }
    }
}

// Car Details Display Handler
class CarDetailsDisplay {
    static displayCarDetails(car) {
        const detailsContainer = document.getElementById('carDetailsContainer');
        if (!detailsContainer) return;

        detailsContainer.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg p-6">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-2xl font-bold text-gray-800">${car.brand} ${car.model}</h2>
                    <span class="text-lg text-gray-600">${car.year}</span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="space-y-4">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-engine text-blue-500"></i>
                            <span class="text-gray-700">Engine: ${car.engine}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <i class="fas fa-gas-pump text-green-500"></i>
                            <span class="text-gray-700">Mileage: ${car.mileage}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <i class="fas fa-bolt text-yellow-500"></i>
                            <span class="text-gray-700">Power: ${car.power}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <i class="fas fa-tachometer-alt text-red-500"></i>
                            <span class="text-gray-700">Max Speed: ${car.maxSpeed}</span>
                        </div>
                    </div>
                    
                    <div class="space-y-4">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-cog text-purple-500"></i>
                            <span class="text-gray-700">Transmission: ${car.transmission}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <i class="fas fa-gas-pump text-orange-500"></i>
                            <span class="text-gray-700">Fuel Type: ${car.fuelType}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <i class="fas fa-weight text-indigo-500"></i>
                            <span class="text-gray-700">Weight: ${car.weight}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <i class="fas fa-dollar-sign text-green-500"></i>
                            <span class="text-gray-700">Price: ${car.price}</span>
                        </div>
                    </div>
                </div>

                <div class="mt-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Features</h3>
                    <div class="flex flex-wrap gap-2">
                        ${car.features.map(feature => `
                            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                                ${feature}
                            </span>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    static displayCarList(cars) {
        const listContainer = document.getElementById('carListContainer');
        if (!listContainer) return;

        listContainer.innerHTML = cars.map(car => `
            <div class="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer"
                 onclick="CarDetailsDisplay.loadCarDetails('${car._id}')">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-800">${car.brand} ${car.model}</h3>
                        <p class="text-gray-600">${car.year}</p>
                    </div>
                    <span class="text-lg font-bold text-blue-600">${car.price}</span>
                </div>
                <div class="mt-2 flex items-center gap-4 text-sm text-gray-500">
                    <span><i class="fas fa-engine mr-1"></i>${car.engine}</span>
                    <span><i class="fas fa-gas-pump mr-1"></i>${car.mileage}</span>
                    <span><i class="fas fa-bolt mr-1"></i>${car.power}</span>
                </div>
            </div>
        `).join('');
    }

    static async loadCarDetails(carId) {
        const car = await CarDetailsAPI.getCarById(carId);
        if (car) {
            this.displayCarDetails(car);
        }
    }

    static async initialize() {
        // Load initial car list
        const cars = await CarDetailsAPI.getAllCars();
        this.displayCarList(cars);

        // Setup search functionality
        const searchInput = document.getElementById('carSearch');
        if (searchInput) {
            searchInput.addEventListener('input', async (e) => {
                const query = e.target.value;
                if (query.length >= 2) {
                    const searchResults = await CarDetailsAPI.searchCars(query);
                    this.displayCarList(searchResults);
                }
            });
        }

        // Setup brand filter
        const brandFilter = document.getElementById('brandFilter');
        if (brandFilter) {
            const stats = await CarDetailsAPI.getCarStats();
            if (stats) {
                brandFilter.innerHTML = `
                    <option value="">All Brands</option>
                    ${stats.brands.map(brand => `
                        <option value="${brand}">${brand}</option>
                    `).join('')}
                `;

                brandFilter.addEventListener('change', async (e) => {
                    const brand = e.target.value;
                    if (brand) {
                        const cars = await CarDetailsAPI.getCarsByBrand(brand);
                        this.displayCarList(cars);
                    } else {
                        const allCars = await CarDetailsAPI.getAllCars();
                        this.displayCarList(allCars);
                    }
                });
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    CarDetailsDisplay.initialize();
}); 