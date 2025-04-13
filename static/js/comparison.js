// Comparison functionality
let engineChart, powerChart, mileageChart;
let carCount = 1;
let carModels = {};
let carVariants = {};

// Initialize the page
function initializePage() {
    // Load car data asynchronously
    loadCarData();
    
    // Create first car selection card
    $("#carSelectionContainer").append(createCarSelectionCard(1));
    
    // Set up event listeners
    setupEventListeners();
}

// Load car data asynchronously
function loadCarData() {
    let retryCount = 0;
    const maxRetries = 3;
    const retryDelay = 2000; // 2 seconds
    const loadingIndicator = $("#loadingIndicator");
    const errorMessage = $("#errorMessage");

    function attemptLoad() {
        loadingIndicator.show();
        errorMessage.hide();
        
        $.ajax({
            url: '/get_car_data',
            method: 'GET',
            timeout: 30000, // Increased timeout to 30 seconds
            success: function(data) {
                if (data.error) {
                    showMessage(data.error, "error");
                    return;
                }
                try {
                    // Process data in chunks to prevent UI freezing
                    processDataInChunks(data);
                } catch (e) {
                    console.error("Error processing car data:", e);
                    showMessage("Error processing car data. Please try again.", "error");
                }
            },
            error: function(xhr, status, error) {
                console.error("Error loading car data:", error);
                if (retryCount < maxRetries) {
                    retryCount++;
                    console.log(`Retrying... Attempt ${retryCount} of ${maxRetries}`);
                    setTimeout(attemptLoad, retryDelay * retryCount); // Exponential backoff
                } else {
                    errorMessage.text("Failed to load car data. Please refresh the page.").show();
                }
            },
            complete: function() {
                loadingIndicator.hide();
            }
        });
    }

    function processDataInChunks(data) {
        // Process companies in chunks
        const companies = Object.keys(data.car_models);
        const chunkSize = 5;
        
        function processChunk(startIndex) {
            const endIndex = Math.min(startIndex + chunkSize, companies.length);
            const chunk = companies.slice(startIndex, endIndex);
            
            chunk.forEach(company => {
                carModels[company] = data.car_models[company];
                // Process variants for this company's models
                data.car_models[company].forEach(model => {
                    carVariants[model] = data.car_variants[model] || [];
                });
            });
            
            // Update UI progress
            const progress = Math.min(100, Math.round((endIndex / companies.length) * 100));
            loadingIndicator.text(`Loading data... ${progress}%`);
            
            if (endIndex < companies.length) {
                // Process next chunk after a short delay
                setTimeout(() => processChunk(endIndex), 100);
            } else {
                // All data processed, initialize UI
                console.log("Car data loaded successfully");
                $("#carSelectionContainer").append(createCarSelectionCard(1));
                populateCompanyDropdowns();
            }
        }
        
        processChunk(0);
    }

    attemptLoad();
}

// Populate company dropdowns
function populateCompanyDropdowns() {
    $('.car-company-select').each(function() {
        const $select = $(this);
        $select.empty().append('<option value="">Select Car Company</option>');
        Object.keys(carModels).sort().forEach(company => {
            $select.append(`<option value="${company}">${company}</option>`);
        });
    });
}

// Create car selection card
function createCarSelectionCard(index) {
    return `
    <div class="card bg-gray-100 p-4 rounded-lg shadow-md car-selection-card" data-index="${index}">
        <div class="flex justify-between items-center mb-2">
            <h2 class="text-xl font-semibold">Select Car ${index}</h2>
            ${index > 1 ? `<button class="remove-car-btn text-red-500 hover:text-red-700">
                <i class="fas fa-minus-circle"></i>
            </button>` : ''}
        </div>
        <select class="car-company-select w-full p-2 border rounded mt-2">
            <option value="">Select Car Company</option>
        </select>
        <select class="car-model-select w-full p-2 border rounded mt-2" disabled>
            <option value="">Select Car Model</option>
        </select>
        <select class="car-variant-select w-full p-2 border rounded mt-2" disabled>
            <option value="">Select Car Variant</option>
        </select>
    </div>`;
}

// Set up event listeners
function setupEventListeners() {
    // Company select change
    $(document).on('change', '.car-company-select', function() {
        handleCompanyChange($(this));
    });

    // Model select change
    $(document).on('change', '.car-model-select', function() {
        handleModelChange($(this));
    });

    // Add car button
    $("#addCarBtn").click(function() {
        if (carCount < 4) {
            carCount++;
            $("#carSelectionContainer").append(createCarSelectionCard(carCount));
            if (carCount === 4) {
                $("#addCarBtn").prop('disabled', true);
            }
        }
    });

    // Remove car button
    $(document).on('click', '.remove-car-btn', function() {
        $(this).closest('.car-selection-card').remove();
        carCount--;
        $("#addCarBtn").prop('disabled', false);
        reindexCards();
    });

    // Compare button
    $("#compareBtn").click(handleCompare);

    // Save button
    $("#saveBtn").click(handleSave);
}

// Handle company selection change
function handleCompanyChange(selectElement) {
    const selectedCompany = selectElement.val();
    const modelDropdown = selectElement.closest('.car-selection-card').find('.car-model-select');
    
    modelDropdown.html('<option value="">Select Car Model</option>');
    
    if (selectedCompany && carModels[selectedCompany]) {
        modelDropdown.prop('disabled', false);
        carModels[selectedCompany].forEach(model => {
            modelDropdown.append(`<option value="${model}">${model}</option>`);
        });
    } else {
        modelDropdown.prop('disabled', true);
    }
    
    const variantDropdown = selectElement.closest('.car-selection-card').find('.car-variant-select');
    variantDropdown.prop('disabled', true).html('<option value="">Select Car Variant</option>');
}

// Handle model selection change
function handleModelChange(selectElement) {
    const selectedModel = selectElement.val();
    const variantDropdown = selectElement.closest('.car-selection-card').find('.car-variant-select');
    
    variantDropdown.html('<option value="">Select Car Variant</option>');
    
    if (selectedModel && carVariants[selectedModel]) {
        variantDropdown.prop('disabled', false);
        carVariants[selectedModel].forEach(variant => {
            variantDropdown.append(`<option value="${variant}">${variant}</option>`);
        });
    } else {
        variantDropdown.prop('disabled', true);
    }
}

// Reindex car selection cards
function reindexCards() {
    $('.car-selection-card').each(function(index) {
        $(this).attr('data-index', index + 1);
        $(this).find('h2').text(`Select Car ${index + 1}`);
    });
}

// Format car name
function formatCarName(carName) {
    return carName.split(" ").slice(0, 2).join(" ");
}

// Handle compare button click
function handleCompare() {
    const selectedCars = getSelectedCars();
    
    if (Object.keys(selectedCars).length < 2) {
        showMessage("Please select at least 2 cars to compare", "error");
        return;
    }

    $.ajax({
        url: '/compare_cars',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(selectedCars),
        success: function(response) {
            if (response.error) {
                showMessage(response.error, "error");
                return;
            }
            updateComparisonUI(selectedCars, response);
        },
        error: function(xhr) {
            showMessage("Error comparing cars: " + (xhr.responseJSON?.error || "Unknown error"), "error");
        }
    });
}

// Get selected cars
function getSelectedCars() {
    const selectedCars = {};
    $('.car-selection-card').each(function(index) {
        const carCompany = $(this).find('.car-company-select').val();
        const carModel = $(this).find('.car-model-select').val();
        const carVariant = $(this).find('.car-variant-select').val();
        const carName = getCarName(carCompany, carModel, carVariant);
        
        if (carName) {
            selectedCars[`car${index + 1}`] = carName;
        }
    });
    return selectedCars;
}

// Get car name
function getCarName(company, model, variant) {
    if (!company || !model || !variant) return null;
    return `${company} ${model} ${variant}`;
}

// Update comparison UI
function updateComparisonUI(selectedCars, response) {
    $('.performance').show();
    updateComparisonTable(selectedCars, response);
    updateCharts(Object.values(selectedCars), response);
}

// Update comparison table
function updateComparisonTable(selectedCars, response) {
    const thead = $("#comparisonTable table thead tr");
    const tbody = $("#comparisonTableBody");
    
    thead.find("th:not(:first)").remove();
    tbody.empty();
    
    Object.values(selectedCars).forEach(car => {
        thead.append(`<th class="border p-2">${formatCarName(car)}</th>`);
    });
    
    const specs = [
        { key: 'car_company', label: 'Company' },
        { key: 'car_model', label: 'Model' },
        { key: 'engine', label: 'Engine (CC)' },
        { key: 'mileage', label: 'Mileage (kmpl)' },
        { key: 'max_power', label: 'Max Power (bhp)' },
        { key: 'torque', label: 'Torque' },
        { key: 'seats', label: 'Seats' },
        { key: 'fuel_type', label: 'Fuel Type' },
        { key: 'transmission', label: 'Transmission' },
        { key: 'selling_price', label: 'Price' },
        { key: 'year', label: 'Year' }
    ];
    
    specs.forEach(spec => {
        const row = $('<tr>');
        row.append(`<td class="border p-2 font-semibold">${spec.label}</td>`);
        
        Object.keys(selectedCars).forEach(carKey => {
            const carData = response[carKey];
            row.append(`<td class="border p-2">${carData[spec.key]}</td>`);
        });
        
        tbody.append(row);
    });
}

// Update charts
function updateCharts(cars, response) {
    const ctxEngine = document.getElementById("engineChart").getContext("2d");
    const ctxPower = document.getElementById("powerChart").getContext("2d");
    const ctxMileage = document.getElementById("mileageChart").getContext("2d");
    
    if (engineChart) engineChart.destroy();
    if (mileageChart) mileageChart.destroy();
    if (powerChart) powerChart.destroy();
    
    const carColors = [
        "rgb(59, 130, 246)",
        "rgb(16, 185, 129)",
        "rgb(245, 158, 11)",
        "rgb(239, 68, 68)"
    ];
    
    const datasets = createDatasets(cars, response, carColors, 'engine');
    const mileageDatasets = createDatasets(cars, response, carColors, 'mileage');
    const powerDatasets = createDatasets(cars, response, carColors, 'max_power');
    
    const chartOptions = getChartOptions();
    
    engineChart = createChart(ctxEngine, "Engine Power (CC)", datasets, chartOptions);
    mileageChart = createChart(ctxMileage, "Mileage (kmpl)", mileageDatasets, chartOptions);
    powerChart = createChart(ctxPower, "Max Power (bhp)", powerDatasets, chartOptions);
}

// Create datasets for charts
function createDatasets(cars, response, colors, property) {
    return cars.map((car, index) => {
        const carData = response[`car${index + 1}`];
        if (!carData) return null;
        return {
            label: formatCarName(car),
            backgroundColor: colors[index],
            borderColor: colors[index],
            borderWidth: 2,
            borderRadius: 8,
            barThickness: 30,
            data: [carData[property]]
        };
    }).filter(dataset => dataset !== null);
}

// Get chart options
function getChartOptions() {
    return {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    padding: 20,
                    font: {
                        size: 12,
                        family: "'Poppins', sans-serif"
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleFont: {
                    size: 14,
                    family: "'Poppins', sans-serif"
                },
                bodyFont: {
                    size: 13,
                    family: "'Poppins', sans-serif"
                },
                padding: 12,
                cornerRadius: 8,
                displayColors: false,
                callbacks: {
                    label: function(context) {
                        return `${context.dataset.label}: ${context.raw}`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    drawBorder: false
                },
                ticks: {
                    font: {
                        family: "'Poppins', sans-serif",
                        size: 12
                    },
                    padding: 10
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: "'Poppins', sans-serif",
                        size: 12
                    },
                    padding: 10
                }
            }
        },
        barPercentage: 0.4,
        categoryPercentage: 0.9,
        animation: {
            duration: 1000,
            easing: 'easeInOutQuart'
        }
    };
}

// Create chart
function createChart(ctx, label, datasets, options) {
    return new Chart(ctx, {
        type: "bar",
        data: {
            labels: [label],
            datasets: datasets
        },
        options: options
    });
}

// Handle save button click
function handleSave() {
    const selectedCars = getSelectedCars();
    const specs = getComparisonSpecs();
    
    const saveData = {
        cars: selectedCars,
        details: {
            specifications: specs,
            timestamp: new Date().toISOString()
        }
    };
    
    $.ajax({
        url: "/save_comparison",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(saveData),
        success: function() {
            showMessage("Comparison saved successfully!", "success");
        },
        error: function() {
            showMessage("Error saving comparison. Please try again.", "error");
        }
    });
}

// Get comparison specifications
function getComparisonSpecs() {
    const specs = {};
    $("#comparisonTableBody tr").each(function() {
        const specName = $(this).find('td:first').text();
        const values = {};
        $(this).find('td:not(:first)').each(function(index) {
            values[`car${index + 1}`] = $(this).text();
        });
        specs[specName] = values;
    });
    return specs;
}

// Show message
function showMessage(message, type) {
    const alertBox = $("#alertBox");
    alertBox.text(message);
    alertBox.attr('class', 'alert ' + type);
    alertBox.show();
    
    setTimeout(() => {
        alertBox.hide();
    }, 3000);
}

// Initialize page when document is ready
$(document).ready(function() {
    initializePage();
    
    // Handle flash messages
    const messages = JSON.parse($('#flash-messages').text());
    messages.forEach(([category, message]) => {
        showMessage(message, category);
    });
    
    // Scroll progress functionality
    window.addEventListener('scroll', () => {
        const scrollProgress = document.getElementById('scrollProgress');
        const scrollPercent = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        scrollProgress.style.transform = `scaleX(${scrollPercent / 100})`;
    });
    
    // Show/hide floating action button
    const floatingButton = document.querySelector('.floating-action-button');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            floatingButton.style.opacity = '1';
            floatingButton.style.transform = 'translateY(0)';
        } else {
            floatingButton.style.opacity = '0';
            floatingButton.style.transform = 'translateY(20px)';
        }
    });
}); 