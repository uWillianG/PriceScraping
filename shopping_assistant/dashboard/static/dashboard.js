const chartCanvas = document.querySelector("#priceChart");

const renderFallbackChart = (canvas, history, currency, dateTime) => {
  const context = canvas.getContext("2d");
  const bounds = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(bounds.width, 320);
  const height = Math.max(bounds.height, 280);
  const prices = history.prices || [];
  const labels = history.labels || [];

  canvas.width = width * ratio;
  canvas.height = height * ratio;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);

  const padding = { bottom: 44, left: 68, right: 24, top: 26 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  if (!prices.length) {
    context.fillStyle = "#6a7280";
    context.font = "700 15px Inter, system-ui, sans-serif";
    context.textAlign = "center";
    context.fillText("Sem histórico suficiente para desenhar o gráfico.", width / 2, height / 2);
    return;
  }

  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const range = maxPrice === minPrice ? Math.max(maxPrice * 0.12, 1) : maxPrice - minPrice;
  const low = maxPrice === minPrice ? minPrice - range / 2 : minPrice;
  const high = maxPrice === minPrice ? maxPrice + range / 2 : maxPrice;

  const pointFor = (price, index) => {
    const x =
      padding.left +
      (prices.length === 1 ? chartWidth / 2 : (index / (prices.length - 1)) * chartWidth);
    const y = padding.top + ((high - price) / (high - low)) * chartHeight;
    return { x, y };
  };

  context.strokeStyle = "rgba(106, 114, 128, 0.18)";
  context.lineWidth = 1;
  for (let index = 0; index <= 4; index += 1) {
    const y = padding.top + (index / 4) * chartHeight;
    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();
  }

  context.fillStyle = "#6a7280";
  context.font = "700 12px Inter, system-ui, sans-serif";
  context.textAlign = "right";
  context.fillText(currency.format(high), padding.left - 10, padding.top + 4);
  context.fillText(currency.format(low), padding.left - 10, padding.top + chartHeight);

  context.textAlign = "left";
  context.fillText(dateTime.format(new Date(labels[0])), padding.left, height - 14);
  if (labels.length > 1) {
    context.textAlign = "right";
    context.fillText(
      dateTime.format(new Date(labels[labels.length - 1])),
      width - padding.right,
      height - 14,
    );
  }

  const points = prices.map(pointFor);
  context.beginPath();
  points.forEach((point, index) => {
    if (index === 0) {
      context.moveTo(point.x, point.y);
    } else {
      context.lineTo(point.x, point.y);
    }
  });
  context.lineTo(points[points.length - 1].x, padding.top + chartHeight);
  context.lineTo(points[0].x, padding.top + chartHeight);
  context.closePath();
  context.fillStyle = "rgba(15, 118, 110, 0.10)";
  context.fill();

  context.beginPath();
  points.forEach((point, index) => {
    if (index === 0) {
      context.moveTo(point.x, point.y);
    } else {
      context.lineTo(point.x, point.y);
    }
  });
  context.strokeStyle = "#0f766e";
  context.lineWidth = 3;
  context.stroke();

  points.forEach((point) => {
    context.beginPath();
    context.arc(point.x, point.y, 4, 0, Math.PI * 2);
    context.fillStyle = "#ffffff";
    context.fill();
    context.strokeStyle = "#0f766e";
    context.lineWidth = 2;
    context.stroke();
  });
};

if (chartCanvas) {
  fetch(chartCanvas.dataset.historyUrl)
    .then((response) => response.json())
    .then((history) => {
      const currency = new Intl.NumberFormat("pt-BR", {
        currency: "BRL",
        style: "currency",
      });
      const dateTime = new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
      });

      if (!window.Chart) {
        renderFallbackChart(chartCanvas, history, currency, dateTime);
        window.addEventListener("resize", () => {
          renderFallbackChart(chartCanvas, history, currency, dateTime);
        });
        return;
      }

      new Chart(chartCanvas, {
        type: "line",
        data: {
          labels: history.labels.map((label) => dateTime.format(new Date(label))),
          datasets: [
            {
              label: "Preço",
              data: history.prices,
              borderColor: "#0f766e",
              backgroundColor: "rgba(15, 118, 110, 0.12)",
              borderWidth: 3,
              fill: true,
              pointBackgroundColor: "#ffffff",
              pointBorderColor: "#0f766e",
              pointBorderWidth: 2,
              pointRadius: 4,
              tension: 0.32,
            },
          ],
        },
        options: {
          interaction: {
            intersect: false,
            mode: "index",
          },
          plugins: {
            legend: {
              labels: {
                boxWidth: 10,
                color: "#3f4752",
                font: {
                  weight: 700,
                },
                usePointStyle: true,
              },
            },
            tooltip: {
              callbacks: {
                label: (context) => ` ${currency.format(context.parsed.y)}`,
              },
            },
          },
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              grid: {
                color: "rgba(106, 114, 128, 0.12)",
              },
              ticks: {
                color: "#6a7280",
              },
            },
            y: {
              beginAtZero: false,
              grid: {
                color: "rgba(106, 114, 128, 0.16)",
              },
              ticks: {
                callback: (value) => currency.format(value),
                color: "#6a7280",
              },
            },
          },
        },
      });
    });
}
