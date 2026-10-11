document.addEventListener("DOMContentLoaded", function () {
    const addSlotBtn = document.getElementById("addSlot");
    const slotsContainer = document.getElementById("booking-slots");

    addSlotBtn.addEventListener("click", function () {
        const newSlot = document.createElement("div");
        newSlot.classList.add("booking-slot", "border", "rounded", "p-2", "mb-2");

        newSlot.innerHTML = `
            <div class="mb-2">
                <input type="date" name="conference_date[]" class="form-control" required>
            </div>
            <div class="d-flex mb-2">
                <input type="time" name="start_time[]" class="form-control" required>
            </div>
            <div class="d-flex mb-2">
                <input type="time" name="end_time[]" class="form-control" required>
            </div>
            <div class="text-end">
                <button type="button" class="btn btn-outline-danger btn-sm remove-slot">
                    <i class="fa fa-trash"></i> Remove
                </button>
            </div>
        `;

        slotsContainer.appendChild(newSlot);

        // remove handler
        newSlot.querySelector(".remove-slot").addEventListener("click", function () {
            newSlot.remove();
        });
    });
});

document.addEventListener("DOMContentLoaded", () => {
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



// fetch(url)
// .then(res => res.json().then(data => ({status: res.status, body: data})))
// .then(obj => {
//     const resStatus = obj.status;
//     const data = obj.body;

//     if (resStatus !== 200) {
//         resultsDiv.innerHTML = `<p class="text-danger">${data.error || 'Unknown error'}</p>`;
//         return;
//     }

//     if (!data.bookings || data.bookings.length === 0) {
//         resultsDiv.innerHTML = `<p class="text-muted">No archived bookings found in this range.</p>`;
//         return;
//     }

//     let table = `<div class="table-responsive">
//         <table class="table table-striped table-bordered align-middle">
//         <thead class="table-light">
//             <tr>
//                 <th>Title</th><th>Booked By</th><th>Date</th>
//                 <th>Start</th><th>End</th><th>Notes</th>
//             </tr>
//         </thead><tbody>`;

//     data.bookings.forEach(b => {
//         table += `<tr>
//             <td>${b.title}</td><td>${b.user}</td><td>${b.date}</td>
//             <td>${b.start}</td><td>${b.end}</td><td>${b.notes || "N/A"}</td>
//         </tr>`;
//     });

//     table += "</tbody></table></div>";
//     resultsDiv.innerHTML = table;
// })
// .catch(err => resultsDiv.innerHTML = `<p class="text-danger">Error loading data: ${err}</p>`);
