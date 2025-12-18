document.addEventListener("DOMContentLoaded", function () {
    // Service type toggle logic
    const select = document.getElementById("id_service_type");
    const blocks = document.querySelectorAll(".service-block");

    function toggleForms(type) {
        blocks.forEach(block => {
            const inputs = block.querySelectorAll("input, select, textarea");
            if (block.id === type + "_form") {
                block.style.display = "block";
                inputs.forEach(i => i.disabled = false);
            } else {
                block.style.display = "none";
                inputs.forEach(i => i.disabled = true);
            }
        });
    }

    if (select) {
        toggleForms(select.value);
        select.addEventListener("change", function () {
            toggleForms(this.value);
        });
    }

    // Customer search functionality
    const searchInput = document.getElementById("customer_search");
    const searchResults = document.getElementById("search_results");
    const selectedCustomer = document.getElementById("selected_customer");
    let searchTimeout;

    searchInput.addEventListener("input", function() {
        const query = this.value.trim();

        clearTimeout(searchTimeout);

        if (query.length < 2) {
            searchResults.innerHTML = "";
            searchResults.style.display = "none";
            return;
        }

        searchTimeout = setTimeout(() => {
            // Gọi API tìm kiếm khách hàng
            fetch(`/api/search-customer/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displaySearchResults(data);
                })
                .catch(error => {
                    console.error("Error:", error);
                    searchResults.innerHTML = '<div class="search-result-item error">Có lỗi xảy ra khi tìm kiếm</div>';
                    searchResults.style.display = "block";
                });
        }, 300);
    });

    function displaySearchResults(customers) {
        if (customers.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item no-results">Không tìm thấy khách hàng</div>';
            searchResults.style.display = "block";
            return;
        }

        let html = "";
        customers.forEach(customer => {
            html += `
                <div class="search-result-item" data-id="${customer.id}" data-code="${customer.code}" data-name="${customer.name}">
                    <div class="customer-info">
                        <div class="customer-code">${customer.code}</div>
                        <div class="customer-name">${customer.name}</div>
                        ${customer.phone ? `<div class="customer-detail">${customer.phone}</div>` : ''}
                        ${customer.email ? `<div class="customer-detail">${customer.email}</div>` : ''}
                    </div>
                </div>
            `;
        });

        searchResults.innerHTML = html;
        searchResults.style.display = "block";

        // Add click handlers
        document.querySelectorAll(".search-result-item").forEach(item => {
            item.addEventListener("click", function() {
                selectCustomer(this);
            });
        });
    }

    function selectCustomer(element) {
        if (element.classList.contains('no-results') || element.classList.contains('error')) {
            return;
        }

        const customerId = element.dataset.id;
        const customerCode = element.dataset.code;
        const customerName = element.dataset.name;

        // Hiển thị khách hàng đã chọn
        selectedCustomer.innerHTML = `
            <div class="selected-customer-card">
                <div class="selected-customer-info">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                    <div>
                        <strong>${customerCode}</strong> - ${customerName}
                    </div>
                </div>
                <button type="button" class="remove-customer" onclick="removeCustomer()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;
        selectedCustomer.style.display = "block";

        // Set giá trị vào form field (giả sử có field id_customer)
        const customerField = document.getElementById("id_customer");
        if (customerField) {
            customerField.value = customerId;
        }

        // Clear search
        searchInput.value = "";
        searchResults.innerHTML = "";
        searchResults.style.display = "none";
    }

    // Click outside to close search results
    document.addEventListener("click", function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = "none";
        }
    });
});

function removeCustomer() {
    const selectedCustomer = document.getElementById("selected_customer");
    selectedCustomer.innerHTML = "";
    selectedCustomer.style.display = "none";

    const customerField = document.getElementById("id_customer");
    if (customerField) {
        customerField.value = "";
    }
}
    document.addEventListener("DOMContentLoaded", function () {

    const paymentType = document.getElementById("id_payment_type");
    const installmentField = document.getElementById("id_installment_count");

    if (!paymentType || !installmentField) return;

    const installmentWrapper = installmentField.closest("p")
        || installmentField.closest(".form-group")
        || installmentField.parentElement;

    function toggleInstallment() {
        if (paymentType.value === "installment") {
            installmentWrapper.style.display = "block";
        } else {
            installmentWrapper.style.display = "none";
            installmentField.value = "";
        }
    }

    toggleInstallment();
    paymentType.addEventListener("change", toggleInstallment);
});