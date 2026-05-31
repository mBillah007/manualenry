// static/js/billing/invoice-submit.js

$(document).on("submit", "#invoiceForm", function(e) {
    e.preventDefault();
    syncExistingPayments(); // সাবমিটের আগে পেমেন্ট সিঙ্ক করে নিন

    let form = $(this);
    let submitBtn = $('button[type="submit"]');
    const originalBtnText = submitBtn.html();

    submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> Saving...');

    $.ajax({
        url: form.attr('action'),
        type: 'POST',
        data: form.serialize(),
        success: function(response) {
            if (response.success) {
                showToast(response.message, "success");
                setTimeout(() => { location.reload(); }, 1000);
            } else {
                showToast("Error: " + (response.error || "Failed"), "danger");
                submitBtn.prop('disabled', false).html(originalBtnText);
            }
        },
        error: function() {
            showToast("Server Error!", "danger");
            submitBtn.prop('disabled', false).html(originalBtnText);
        }
    });
});