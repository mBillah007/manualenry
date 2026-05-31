// static/js/billing/invoice-payments.js

// পেমেন্ট মোডাল থেকে মেইন ফর্মে ডাটা সিঙ্ক
function syncExistingPayments() {
    const invoiceForm = $("#invoiceForm");
    invoiceForm.find(".pay-hidden").remove(); // পুরনো গুলো ফেলে দিন

    $("#paymentTable tr:not(.cancelled)").each(function() {
        const m = $(this).find("input[name='payment_methods[]']").val();
        const a = $(this).find(".paymentAmount").val();
        if (m && a) {
            invoiceForm.append(`<input type="hidden" class="pay-hidden" name="payment_methods[]" value="${m}">`);
            invoiceForm.append(`<input type="hidden" class="pay-hidden" name="payment_amounts[]" value="${a}">`);
        }
    });
}

// পেমেন্ট মোডাল ওপেন
$(document).on("click", "#openPayment", function() {
    bootstrap.Modal.getOrCreateInstance(MODAL_PAY[0], { backdrop: false }).show();
});

// পেমেন্ট অ্যাড লজিক
$(document).on("click", "#addPaymentRow", function(e) {
    let method = $("#paymentMethodSelect").val();
    let methodText = $("#paymentMethodSelect option:selected").text();
    let amount = parseFloat($("#paymentAmountInput").val() || 0);

    if (amount <= 0) return;

    $("#paymentTable").append(`<tr>
        <td>${methodText}<input type="hidden" name="payment_methods[]" value="${method}"></td>
        <td><input type="number" name="payment_amounts[]" class="form-control paymentAmount" value="${amount.toFixed(2)}"></td>
        <td><button type="button" class="btn btn-sm btn-danger removeRow">❌</button></td>
    </tr>`);
    $("#paymentAmountInput").val("").focus();
    updateAllSummary();
});

// লিস্ট পেজ থেকে সরাসরি ডিউ কালেকশন (SweetAlert2)
$(document).on('submit', '.due-payment-form', function(e) {
    e.preventDefault();
    const form = $(this);
    const invId = form.data('invoice-id');

    Swal.fire({
        title: 'Confirm Payment?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, Confirm'
    }).then((result) => {
        if (result.isConfirmed) {
            $.post(`/billing/collect-due/${invId}/`, form.serialize(), function(res) {
                if(res.success) Swal.fire('Saved!', res.message, 'success').then(() => location.reload());
                else Swal.fire('Error', res.error, 'error');
            });
        }
    });
});