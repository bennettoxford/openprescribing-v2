const updateChart = () => {
    const chartContainer = document.querySelector('#prescribing-chart');
    const { prescribingApiUrl } = chartContainer.dataset;

    fetch(prescribingApiUrl)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Failed to fetch chart data: ${response.status}`);
            }
            return response.json();
        })
        .then((chartSpec) => {
            chartContainer.textContent = '';
            return vegaEmbed('#prescribing-chart', chartSpec);
        })
        .catch((error) => {
            console.error('Unable to render prescribing chart', error);
            chartContainer.textContent = 'Unable to load chart data. Please try again later.';
        });
}

document.addEventListener('DOMContentLoaded', updateChart);
