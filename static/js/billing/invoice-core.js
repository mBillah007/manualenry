// static/js/billing/invoice-core.js

const MODAL_MAIN = $('#invoiceModal');
const MODAL_PAY = $('#paymentModal');

// ইনভয়েস মোডাল লোড করা (Create/Edit)
$(document).on("click", ".openInvoiceModal", function(e) {
    e.preventDefault();
    const url = $(this).data("url") || $(this).attr("href");
    
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.text())
        .then(html => {
            $("#invoiceModalContent").html(html);
            bootstrap.Modal.getOrCreateInstance(MODAL_MAIN[0]).show();
            
            // মোডাল লোড হওয়ার পর ডিপেন্ডেন্সি ইনিশিয়ালাইজ করা
            setTimeout(() => {
                const ctx = $('#invoiceModalContent');
                initializeSelect2(ctx);     // Select2 Loader
                admissionPatientCode(ctx); // IPD Logic
                syncExistingPayments();     // Payment Sync
                updateAllSummary();         // First Calculation
            }, 300);
        });
});

// টোস্ট মেসেজ হেল্পার
function showToast(message, type="info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-bg-${type} border-0 shadow-lg`;
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body"><i class="fas fa-info-circle me-2"></i> ${message} </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    container.appendChild(toastEl);
    new bootstrap.Toast(toastEl, { delay: 3000 }).show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}