// static/js/billing/invoice-helpers.js

function initializeInvoiceHelpers(context) {
    const modalParent = $('#invoiceModal');

    // ১. জেনেরিক Select2 হ্যান্ডলার (সব .select2-ajax ক্লাসের জন্য)
    context.find('.select2-ajax').each(function() {
        let $el = $(this);
        $el.select2({
            width: '100%',
            dropdownParent: modalParent,
            placeholder: $el.data('placeholder') || "Search...",
            allowClear: true,
            ajax: { 
                url: $el.data('url'), 
                dataType: 'json', 
                delay: 250,
                data: p => ({ q: p.term }), 
                processResults: d => {
                    let results = d.results ? d.results : d;
                    return {
                        results: results.map(i => ({ 
                            id: i.id, 
                            text: i.code ? (i.code + " - " + i.name) : (i.name || i.text),
                            price: i.price || 0, 
                            disc: i.percent_discount || 0,
                            name: i.name || i.text
                        }))
                    };
                }
            }
        });
    });

    // ২. টেস্ট সিলেক্ট ইভেন্ট (ADVICE)
    context.find('#testGroupSelect').select2({
        width: '100%',
        dropdownParent: modalParent,
        placeholder: "Search Tests...",
        ajax: {
            url: "{% url 'billing:search_testgroup' %}", // অথবা data-url থেকে নিতে পারেন
            dataType: 'json',
            delay: 250,
            data: p => ({ q: p.term }),
            processResults: d => ({
                results: d.map(i => ({
                    id: i.id,
                    text: i.code + " - " + i.name,
                    name: i.name,
                    price: i.price,
                    disc: i.percent_discount
                }))
            })
        }
    }).on('select2:select', function(e) {
        addAdviceRow(e.params.data);
        $(this).val(null).trigger('change');
    });

    // ৩. এক্সেসরিজ সিলেক্ট ইভেন্ট
    context.find('#accessorySelect').select2({
        width: '100%',
        dropdownParent: modalParent,
        placeholder: "Add...",
        ajax: {
            url: "{% url 'billing:search_accessory' %}",
            dataType: 'json',
            data: p => ({ q: p.term }),
            processResults: d => ({
                results: d.map(i => ({ id: i.id, text: i.name, name: i.name, price: i.price }))
            })
        }
    }).on('select2:select', function(e) {
        addAccessoryRow(e.params.data);
        $(this).val(null).trigger('change');
    });

    // ৪. পেমেন্ট মোডাল ওপেন (NET PAYABLE বক্সে ক্লিক)
    context.find('#triggerPayment').on('click', function() {
        const netAmount = parseFloat($('input[name="net_amount"]').val()) || 0;
        const paidAmount = parseFloat($('input[name="paid_amount"]').val()) || 0;
        
        if ($('#paymentModal').length > 0) {
            $('#payment_total_bill').val(netAmount.toFixed(2));
            $('#payment_due_amount').val((netAmount - paidAmount).toFixed(2));
            new bootstrap.Modal(document.getElementById('paymentModal')).show();
        }
    });

    // ৫. Row Action (Cancel/Delete/Undo) - Event Delegation
    context.on('click', '.rowActionBtn', function() {
        let row = $(this).closest('tr');
        let isCancelledInput = row.find('input[name*="_cancelled[]"]');
        
        if (isCancelledInput.val() === "true") {
            // Undo Cancel
            row.removeClass('table-danger cancelled opacity-50');
            isCancelledInput.val("false");
            $(this).text('✕').removeClass('btn-success').addClass('btn-outline-warning');
        } else {
            // Cancel Row
            row.addClass('table-danger cancelled opacity-50');
            isCancelledInput.val("true");
            $(this).text('Undo').removeClass('btn-outline-warning').addClass('btn-success');
        }
        updateAllSummary();
    });

    // ৬. IPD / Admission Logic
    admissionPatientCode(context);
    
    // ৭. ইনপুট লিসেনার্স
    context.find('input[name="discount_percent"], input[name="discount_amount"]').on('input', function() {
        updateAllSummary(this.name); // কোন ফিল্ডে টাইপ হচ্ছে সেটা পাঠানো হচ্ছে
    });

    context.on('input', '.qty', updateAllSummary);

    // ইনিশিয়াল ক্যালকুলেশন
    updateAllSummary();
}

/** * ADVICE ROW যোগ করা
 */
function addAdviceRow(d) {
    if ($('#adviceTable input[name="advice_group_ids[]"][value="' + d.id + '"]').length > 0) {
        return;
    }
    const html = `
        <tr class="border-bottom advice-row">
            <td class="ps-2">
                <div class="fw-bold small">${d.name}</div>
                <input type="hidden" name="advice_ids[]" value="0">
                <input type="hidden" name="advice_group_ids[]" value="${d.id}">
                <input type="hidden" name="advice_prices[]" value="${d.price}">
                <input type="hidden" name="advice_cancelled[]" value="false">
            </td>
            <td class="text-end fw-bold small">৳<span class="price">${d.price}</span></td>
            <td class="text-center">
                <input type="number" class="form-control form-control-sm text-center border-0 bg-light p-0 discount shadow-none" 
                       value="${d.disc || 0}" readonly style="width: 40px; margin: auto;">
            </td>
            <td class="text-center">
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-light border-0 py-0 moveUp">↑</button>
                    <button type="button" class="btn btn-light border-0 py-0 moveDown">↓</button>
                    <button type="button" class="btn btn-outline-warning py-0 border-0 rowActionBtn">✕</button>
                </div>
            </td>
        </tr>`;
    $('#adviceTable').append(html);
    updateAllSummary();
}

/** * ACCESSORY ROW যোগ করা
 */
function addAccessoryRow(d) {
    const html = `
        <tr class="border-bottom accessory-row">
            <td class="ps-2 text-truncate" style="max-width: 90px;">${d.name}</td>
            <td class="text-center">
                <input type="number" name="accessory_qtys[]" class="qty border-0 bg-light text-center rounded shadow-none" style="width: 30px;" value="1">
            </td>
            <td class="text-end pe-1">
                <span class="fw-bold total">${d.price}</span>
                <input type="hidden" name="accessory_prices[]" value="${d.price}">
                <input type="hidden" name="accessory_ids[]" value="0">
                <input type="hidden" name="accessory_item_ids[]" value="${d.id}">
                <input type="hidden" name="accessory_cancelled[]" value="false">
                <button type="button" class="btn btn-link text-danger p-0 ms-1 rowActionBtn shadow-none">✕</button>
            </td>
        </tr>`;
    $('#accessoryTable').append(html);
    updateAllSummary();
}

/** * মাস্টার ক্যালকুলেশন ফাংশন
 */
function updateAllSummary(focusedField = null) {
    let adviceSubtotal = 0;
    let referrerFee = 0;

    // ১. Advice ক্যালকুলেশন
    $('.advice-row').each(function() {
        if ($(this).find('input[name="advice_cancelled[]"]').val() === "true") return;
        
        let price = parseFloat($(this).find('input[name="advice_prices[]"]').val()) || 0;
        let discPercent = parseFloat($(this).find('.discount').val()) || 0;
        
        adviceSubtotal += price;
        referrerFee += (price * discPercent) / 100;
    });

    // ২. Accessory ক্যালকুলেশন
    let accessorySubtotal = 0;
    $('.accessory-row').each(function() {
        if ($(this).find('input[name="accessory_cancelled[]"]').val() === "true") return;
        
        let price = parseFloat($(this).find('input[name="accessory_prices[]"]').val()) || 0;
        let qty = parseFloat($(this).find('.qty').val()) || 0;
        let rowTotal = price * qty;
        
        $(this).find('.total').text(rowTotal.toFixed(2));
        accessorySubtotal += rowTotal;
    });

    // ৩. ডিসকাউন্ট হ্যান্ডলিং (Percent vs Amount)
    let discPercInput = $('input[name="discount_percent"]');
    let discAmtInput = $('input[name="discount_amount"]');
    let sDiscPerc = parseFloat(discPercInput.val()) || 0;
    let sDiscAmt = parseFloat(discAmtInput.val()) || 0;

    if (focusedField === "discount_percent") {
        sDiscAmt = (adviceSubtotal * sDiscPerc) / 100;
        discAmtInput.val(sDiscAmt.toFixed(2));
    } else if (focusedField === "discount_amount") {
        sDiscPerc = adviceSubtotal > 0 ? (sDiscAmt / adviceSubtotal) * 100 : 0;
        discPercInput.val(sDiscPerc.toFixed(2));
    }

    // ৪. ফাইনাল ফিল্ড আপডেট
    let netAmount = (adviceSubtotal - sDiscAmt) + accessorySubtotal;
    let paid = parseFloat($('input[name="paid_amount"]').val()) || 0;

    $('input[name="advice_total"]').val(adviceSubtotal.toFixed(2));
    $('input[name="accessory_total"]').val(accessorySubtotal.toFixed(2));
    $('input[name="net_amount"]').val(netAmount.toFixed(2));
    $('input[name="due_amount"]').val((netAmount - paid).toFixed(2));
    $('input[name="referrer_amount"]').val(referrerFee.toFixed(2));
}
// ২. IPD / Admission Logic
function admissionPatientCode(context) {
    const visitSelect = context.find("#visitTypeSelect");
    const admissionRow = context.find("#admissionCodeRow");
    const admissionSelect = context.find("#admissionSelect");

    function toggle() {
        if (visitSelect.val() === "IPD") {
            admissionRow.removeClass("d-none");
            if (!admissionSelect.hasClass("select2-hidden-accessible")) {
                admissionSelect.select2({
                    width: '100%',
                    dropdownParent: $('#invoiceModal'),
                    ajax: {
                        url: admissionSelect.data("url"),
                        dataType: 'json',
                        processResults: data => ({
                            results: data.results.map(i => ({
                                id: i.id, text: i.text, patient: i.patient 
                            }))
                        })
                    }
                }).on("select2:select", function(e) {
                    const p = e.params.data.patient;
                    if (p) {
                        context.find('input[name="name"]').val(p.name);
                        context.find('input[name="mobile"]').val(p.mobile);
                        context.find('input[name="age_year"]').val(p.age_year);
                        context.find('input[name="age_month"]').val(p.age_month);
                        context.find('input[name="age_day"]').val(p.age_day);
                        context.find('textarea[name="address"]').val(p.address);
                        if(p.gender) context.find('select[name="gender"]').val(p.gender).trigger('change');
                    }
                });
            }
        } else {
            admissionRow.addClass("d-none");
        }
    }
    visitSelect.on("change", toggle);
    toggle();
}
