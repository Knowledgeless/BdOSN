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
        const roomId = filterBtn.dataset.roomId; // pass room id via data attribute

        if (!roomId) {
            resultsDiv.innerHTML = `<p class="text-danger">Room ID not found.</p>`;
            return;
        }

        resultsDiv.innerHTML = `<p class="text-muted">Loading...</p>`;

        fetch(`/filter_archived/${roomId}/?from=${from}&to=${to}`)
            .then(res => res.json().then(data => ({ status: res.status, body: data })))
            .then(obj => {
                const status = obj.status;
                const data = obj.body;

                if (status !== 200) {
                    resultsDiv.innerHTML = `<p class="text-danger">${data.error || 'Unknown error occurred'}</p>`;
                    return;
                }

                if (!data.bookings || data.bookings.length === 0) {
                    resultsDiv.innerHTML = `<p class="text-muted">No archived bookings found in this range.</p>`;
                    return;
                }

                let table = `
                <div class="table-responsive">
                    <table class="table table-striped table-bordered align-middle">
                        <thead class="table-light">
                            <tr>
                                <th>Title</th>
                                <th>Booked By</th>
                                <th>Date</th>
                                <th>Start</th>
                                <th>End</th>
                                <th>Organization</th>
                                <th>Booked For</th>
                                <th>Notes</th>
                            </tr>
                        </thead>
                        <tbody>`;

                data.bookings.forEach(b => {
                    table += `
                        <tr>
                            <td>${b.title}</td>
                            <td>${b.user}</td>
                            <td>${b.date}</td>
                            <td>${b.start}</td>
                            <td>${b.end}</td>
                            <td>${b.organization}</td>
                            <td>${b.booked_for}</td>
                            <td>${b.notes || 'N/A'}</td>
                        </tr>`;
                });

                table += `</tbody></table></div>`;
                resultsDiv.innerHTML = table;
            })
            .catch(err => {
                resultsDiv.innerHTML = `<p class="text-danger">Error loading data: ${err}</p>`;
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
