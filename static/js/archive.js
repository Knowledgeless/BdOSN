
document.addEventListener("DOMContentLoaded", function() {
  const filterBtn = document.getElementById("filterArchived");
  const resultsDiv = document.getElementById("archivedResults");

  filterBtn.addEventListener("click", function() {
    const from = document.getElementById("fromDate").value;
    const to = document.getElementById("toDate").value;

    fetch(`/rooms/{{ room.id }}/archived/filter/?from=${from}&to=${to}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          resultsDiv.innerHTML = `<p class="text-danger">${data.error}</p>`;
          return;
        }

        if (data.bookings.length === 0) {
          resultsDiv.innerHTML = `<p class="text-muted">No archived bookings found in this range.</p>`;
          return;
        }

        let table = `
          <div class="table-responsive">
          <table class="table table-striped table-bordered align-middle">
            <thead class="table-dark">
              <tr>
                <th>Title</th>
                <th>Booked By</th>
                <th>Date</th>
                <th>Start</th>
                <th>End</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
        `;

        data.bookings.forEach(b => {
          table += `
            <tr>
              <td>${b.title}</td>
              <td>${b.user}</td>
              <td>${b.date}</td>
              <td>${b.start}</td>
              <td>${b.end}</td>
              <td>${b.notes || "N/A"}</td>
            </tr>
          `;
        });

        table += "</tbody></table></div>";
        resultsDiv.innerHTML = table;
      })
      .catch(err => {
        resultsDiv.innerHTML = `<p class="text-danger">Error loading data.</p>`;
      });
  });
});


document.addEventListener('DOMContentLoaded', function () {
    var toastElList = [].slice.call(document.querySelectorAll('.toast'))
    toastElList.forEach(function (toastEl) {
      var toast = new bootstrap.Toast(toastEl)
      toast.show()
    })
  })