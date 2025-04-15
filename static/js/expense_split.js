function toggleSplitOptions() {
    const splitCheckbox = document.getElementById('is_split');
    const splitOptions = document.getElementById('splitOptions');
    splitOptions.style.display = splitCheckbox.checked ? 'block' : 'none';
    if (splitCheckbox.checked) {
        updatePaymentFields();
    }
}

function updatePaymentFields() {
    const numPeople = document.getElementById('split_with').value;
    const paymentFields = document.getElementById('paymentFields');
    const groupSelect = document.getElementById('groupSelect');
    const selectedGroup = groupSelect.value;

    // Clear existing fields
    paymentFields.innerHTML = '';

    // Add payment fields for each person
    for (let i = 0; i < numPeople; i++) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'payment-field mb-3';
        fieldDiv.innerHTML = `
            <h4>Person ${i + 1}</h4>
            <div class="form-group">
                <label>User ID</label>
                <input type="number" name="payments-${i}-user_id" class="form-control" required>
            </div>
            <div class="form-group">
                <label>Amount Paid</label>
                <input type="number" step="0.01" name="payments-${i}-amount_paid" class="form-control" required>
            </div>
        `;
        paymentFields.appendChild(fieldDiv);
    }
}

// Initialize split options on page load
document.addEventListener('DOMContentLoaded', function() {
    toggleSplitOptions();
});