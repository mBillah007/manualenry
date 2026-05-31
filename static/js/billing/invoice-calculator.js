// static/js/billing/invoice-calculator.js

function updateAllSummary() {
    let adviceTotal = 0, accessoryTotal = 0, referrerAmount = 0;

    // Advice Table
    $('#adviceTable tr').each(function() {
        let row = $(this);
        if (row.find('input[name="advice_cancelled[]"]').val() === "true" || row.hasClass('cancelled')) return;
        let price = parseFloat(row.find('.price').text()) || parseFloat(row.find('input[name="advice_prices[]"]').val()) || 0;
        let rowDiscPerc = parseFloat(row.find('.discount').val()) || 0;
        let discAmt = (price * rowDiscPerc) / 100;
        adviceTotal += price;
        referrerAmount += discAmt;
        row.find('input[name="advice_final_prices[]"]').val((price - discAmt).toFixed(2));
        row.find('input[name="advice_discounts[]"]').val(discAmt.toFixed(2));
    });

    // Accessory Table
    $('#accessoryTable tr').each(function() {
        let row = $(this);
        if (row.find('input[name="accessory_cancelled[]"]').val() === "true" || row.hasClass('cancelled')) return;
        let rate = parseFloat(row.find('.price').text()) || 0;
        let qty = parseInt(row.find('.qty').val()) || 0;
        let total = rate * qty;
        accessoryTotal += total;
        row.find('.total').text(total.toFixed(2));
        row.find('input[name="accessory_totals[]"]').val(total.toFixed(2));
    });

    // Main Discount & Net
    let sDiscPercent = parseFloat($('input[name="discount_percent"]').val()) || 0;
    let sDiscAmount = parseFloat($('input[name="discount_amount"]').val()) || 0;
    
    if ($('input[name="discount_percent"]').is(':focus')) {
        sDiscAmount = (adviceTotal * sDiscPercent) / 100;
    } else if ($('input[name="discount_amount"]').is(':focus')) {
        sDiscPercent = adviceTotal > 0 ? (sDiscAmount / adviceTotal) * 100 : 0;
    }

    let net = (adviceTotal - sDiscAmount) + accessoryTotal;
    let totalPaid = 0;
    $('.paymentAmount').each(function() {
        if (!$(this).closest('tr').hasClass('cancelled')) totalPaid += parseFloat($(this).val()) || 0;
    });

    // UI Inputs Update
    $('input[name="advice_total"]').val(adviceTotal.toFixed(2));
    $('input[name="accessory_total"]').val(accessoryTotal.toFixed(2));
    $('input[name="discount_percent"]').val(sDiscPercent.toFixed(2));
    $('input[name="discount_amount"]').val(sDiscAmount.toFixed(2));
    $('input[name="net_amount"]').val(net.toFixed(2));
    $('input[name="paid_amount"]').val(totalPaid.toFixed(2));
    $('input[name="due_amount"]').val((net - totalPaid).toFixed(2));
}

// Row Actions
$(document).on('click', '.cancelRow, .removeRow', function() {
    let row = $(this).closest('tr');
    row.addClass('cancelled table-secondary');
    row.find('input[name*="cancelled"]').val("true");
    if ($(this).hasClass('removeRow')) row.remove();
    updateAllSummary();
});

$(document).on('input', '.qty, .discount, .paymentAmount, input[name*="discount"]', updateAllSummary);