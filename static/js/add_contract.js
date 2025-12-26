document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       SERVICE TYPE TOGGLE (SAFE FOR DJANGO FORMSET)
    ===================================================== */
    const serviceTypeSelect = document.getElementById("id_service_type");

    const serviceBlocks = {
        nhanhieu: document.getElementById("nhanhieu_form"),
        banquyen: document.getElementById("banquyen_form"),
        dkkd: document.getElementById("dkkd_form"),
        dautu: document.getElementById("dautu_form"),
        khac: document.getElementById("khac_form"),
    };

    function hideAllServices() {
        Object.values(serviceBlocks).forEach(block => {
            if (!block) return;

            block.style.display = "none";

            // ❌ KHÔNG disable input
            // ✅ chỉ bỏ required để tránh HTML chặn submit
            block.querySelectorAll("[required]").forEach(input => {
                input.dataset.wasRequired = "true";
                input.removeAttribute("required");
            });
        });
    }

    function showService(type) {
        hideAllServices();

        const block = serviceBlocks[type];
        if (!block) return;

        block.style.display = "block";

        // khôi phục required
        block.querySelectorAll("[data-was-required='true']").forEach(input => {
            input.setAttribute("required", "required");
        });
    }

    if (serviceTypeSelect) {
        showService(serviceTypeSelect.value);
        serviceTypeSelect.addEventListener("change", function () {
            showService(this.value);
        });
    }

    /* =====================================================
       PAYMENT TYPE – INSTALLMENT TOGGLE
    ===================================================== */
    const paymentType = document.getElementById("id_payment_type");
    const installmentField = document.getElementById("id_installment_count");

    if (paymentType && installmentField) {
        const wrapper = installmentField.closest("p");

        function toggleInstallment() {
            if (paymentType.value === "installment") {
                wrapper.style.display = "block";
                installmentField.setAttribute("required", "required");
            } else {
                wrapper.style.display = "none";
                installmentField.value = "";
                installmentField.removeAttribute("required");
            }
        }

        toggleInstallment();
        paymentType.addEventListener("change", toggleInstallment);
    }

    /* =====================================================
       CUSTOMER SEARCH (AJAX)
    ===================================================== */
    const searchInput = document.getElementById("customer_search");
    const searchResults = document.getElementById("search_results");
    const selectedCustomer = document.getElementById("selected_customer");
    const customerField = document.getElementById("id_customer");

    let searchTimeout;

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const query = this.value.trim();
            clearTimeout(searchTimeout);

            if (query.length < 2) {
                searchResults.style.display = "none";
                return;
            }

            searchTimeout = setTimeout(() => {
                fetch(`/api/search-customer/?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => renderSearchResults(data))
                    .catch(() => {
                        searchResults.innerHTML =
                            "<div class='error'>❌ Lỗi tìm kiếm</div>";
                        searchResults.style.display = "block";
                    });
            }, 300);
        });
    }

    function renderSearchResults(customers) {
        if (!customers.length) {
            searchResults.innerHTML =
                "<div class='no-results'>Không tìm thấy khách hàng</div>";
            searchResults.style.display = "block";
            return;
        }

        searchResults.innerHTML = customers.map(c => `
            <div class="search-result-item"
                 data-id="${c.id}"
                 data-code="${c.code}"
                 data-name="${c.name}">
                <strong>${c.code}</strong> – ${c.name}
            </div>
        `).join("");

        searchResults.style.display = "block";

        document.querySelectorAll(".search-result-item").forEach(item => {
            item.addEventListener("click", function () {
                selectCustomer(this.dataset.id, this.dataset.code, this.dataset.name);
            });
        });
    }

    function selectCustomer(id, code, name) {
        selectedCustomer.innerHTML = `
            <div class="selected-customer-card">
                <strong>${code}</strong> – ${name}
                <button type="button" class="btn-remove-customer">❌</button>
            </div>
        `;
        selectedCustomer.style.display = "block";
        customerField.value = id;
        searchResults.style.display = "none";
        searchInput.value = "";

        selectedCustomer
            .querySelector(".btn-remove-customer")
            .addEventListener("click", removeCustomer);
    }

    function removeCustomer() {
        selectedCustomer.innerHTML = "";
        selectedCustomer.style.display = "none";
        customerField.value = "";
    }

    /* =====================================================
       FORM VALIDATION BEFORE SUBMIT
    ===================================================== */
    const contractForm = document.querySelector(".contract-form");

    if (contractForm) {
        contractForm.addEventListener("submit", function (e) {

            if (!customerField || !customerField.value) {
                e.preventDefault();
                alert("⚠️ Vui lòng chọn khách hàng!");
                return false;
            }

            if (serviceTypeSelect && !serviceTypeSelect.value) {
                e.preventDefault();
                alert("⚠️ Vui lòng chọn loại dịch vụ!");
                return false;
            }

            console.log("✅ Form OK – submitting");
        });
    }
});

/* =====================================================
   FORMSET ADD
===================================================== */
window.addForm = function (prefix) {
    const totalForms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    const formset = document.getElementById(`${prefix}-formset`);
    const emptyForm = document.getElementById(`${prefix}-empty-form`);

    if (!totalForms || !formset || !emptyForm) return;

    const index = parseInt(totalForms.value, 10);
    const template = emptyForm.querySelector(".formset-item");
    const newForm = template.cloneNode(true);

    newForm.innerHTML = newForm.innerHTML.replace(/__prefix__/g, index);

    newForm.querySelectorAll("input, select, textarea").forEach(field => {
        if (field.type !== "hidden") field.value = "";
    });

    formset.appendChild(newForm);
    totalForms.value = index + 1;
};

/* =====================================================
   FORMSET REMOVE
===================================================== */
window.removeItem = function (btn) {
    const item = btn.closest(".formset-item");
    if (!item) return;

    const delInput = item.querySelector('input[name$="DELETE"]');
    if (delInput) {
        delInput.checked = true;
        item.style.display = "none";
    } else {
        item.remove();
    }
};

console.log("✅ add_contract.js (SAFE FOR DJANGO) loaded");
