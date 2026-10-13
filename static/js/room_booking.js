document.addEventListener("DOMContentLoaded", function () {
    const toastEls = document.querySelectorAll('.toast');
    toastEls.forEach(function (toastEl) {
        if (toastEl.dataset.bootstrapInit === 'true') return;

        const toast = new bootstrap.Toast(toastEl, {
            delay: 4800,
            autohide: true,
        });

        toast.show();
        toastEl.dataset.bootstrapInit = 'true';
    });

    document.querySelectorAll('.booking-time-input').forEach(function (timeInput) {
        if (!timeInput.placeholder) {
            timeInput.placeholder = timeInput.name.includes('start') ? 'Start Time' : 'End Time';
        }
    });

    const addSlotBtn = document.getElementById("addSlot");
    const slotsContainer = document.getElementById("booking-slots");

    if (!addSlotBtn || !slotsContainer) return;

    addSlotBtn.addEventListener("click", function () {
        const newSlot = document.createElement("div");
        newSlot.classList.add("booking-slot", "border", "rounded", "p-2", "mb-2");

        newSlot.innerHTML = `
            <div class="mb-2">
                <input type="date" name="conference_date[]" class="form-control" required>
            </div>
            <div class="mb-2">
                <label class="form-label small text-muted mb-1">Start Time</label>
                <input type="time" name="start_time[]" class="form-control booking-time-input" placeholder="Start Time" required>
            </div>
            <div class="mb-2">
                <label class="form-label small text-muted mb-1">End Time</label>
                <input type="time" name="end_time[]" class="form-control booking-time-input" placeholder="End Time" required>
            </div>
            <div class="text-end">
                <button type="button" class="btn btn-outline-danger btn-sm remove-slot">
                    <i class="fa fa-trash"></i> Remove
                </button>
            </div>
        `;

        slotsContainer.appendChild(newSlot);

        newSlot.querySelector(".remove-slot").addEventListener("click", function () {
            newSlot.remove();
        });
    });

    const filterBtn = document.getElementById("filterArchived");
    const resultsDiv = document.getElementById("archivedResults");

    if (!filterBtn || !resultsDiv) return;

    filterBtn.addEventListener("click", () => {
        const from = document.getElementById("fromDate").value;
        const to = document.getElementById("toDate").value;
        resultsDiv.textContent = "Loading...";

        const url = new URL(filterBtn.dataset.url, window.location.origin);
        if (from) url.searchParams.set("from", from);
        if (to) url.searchParams.set("to", to);

        fetch(url)
            .then(res => res.json().then(data => ({ status: res.status, body: data })))
            .then(obj => {
                const status = obj.status;
                const data = obj.body;

                if (status !== 200) {
                    resultsDiv.textContent = data.error || "Error loading data.";
                    return;
                }

                if (!data.bookings || data.bookings.length === 0) {
                    resultsDiv.textContent = "No archived bookings found in this range.";
                    return;
                }

                const wrapper = document.createElement("div");
                wrapper.className = "table-responsive";
                const table = document.createElement("table");
                table.className = "table table-striped table-bordered align-middle";
                table.innerHTML = "<thead class=\"table-light\"><tr><th>Title</th><th>Booked By</th><th>Date</th><th>Start</th><th>End</th><th>Organization</th><th>Booked For</th><th>Notes</th></tr></thead>";
                const tbody = document.createElement("tbody");

                data.bookings.forEach(booking => {
                    const row = document.createElement("tr");
                    [booking.title, booking.user, booking.date, booking.start, booking.end,
                        booking.organization, booking.booked_for, booking.notes || "N/A"].forEach(value => {
                            const cell = document.createElement("td");
                            cell.textContent = value;
                            row.appendChild(cell);
                        });
                    tbody.appendChild(row);
                });

                table.appendChild(tbody);
                wrapper.appendChild(table);
                resultsDiv.replaceChildren(wrapper);
            })
            .catch(() => {
                resultsDiv.textContent = "Error loading data.";
            });
    });
});
