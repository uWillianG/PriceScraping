const chartCanvas = document.querySelector("#priceChart");

if (chartCanvas) {
  fetch(chartCanvas.dataset.historyUrl)
    .then((response) => response.json())
    .then((history) => {
      new Chart(chartCanvas, {
        type: "line",
        data: {
          labels: history.labels,
          datasets: [
            {
              label: "Price",
              data: history.prices,
              borderColor: "#0b5cad",
              backgroundColor: "rgba(11, 92, 173, 0.12)",
              tension: 0.25,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: false,
            },
          },
        },
      });
    });
}
