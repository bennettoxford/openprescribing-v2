const setupSearch = () => {
    const codes = JSON.parse(document.getElementById('bnf-codes').textContent);
    const levels = Object.fromEntries(JSON.parse(document.getElementById('bnf-levels').textContent));
    const search = document.getElementById('bnf-search');
    const results = document.getElementById('bnf-results');

    search.addEventListener('input', (event) => {
        const query = search.value.trim().toLowerCase();
        if (query.length < 3) {
            results.innerHTML = '';
            results.classList.add('d-none');
            return;
        }
        const matches = codes.filter((c) => c.name.toLowerCase().includes(query))
        results.innerHTML = '';
        const fragment = document.createDocumentFragment();
        matches.forEach((c) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action';
            item.innerHTML = `
            <div class="fw-semibold">${c.name}</div>
            <div class="text-muted small">${c.code} - ${levels[c.level]}</div>
            `;
            item.addEventListener('click', () => {
                const url = new URL(window.location.href);
                url.searchParams.set('code', c.code);
                window.location.href = url.toString();
            });
            fragment.appendChild(item);
        });
        results.appendChild(fragment);
        results.classList.toggle('d-none', matches.length === 0);
    });
}

const updateChart = () => {
    const chartContainer = document.querySelector('#prescribing-chart');
    if (!chartContainer) {
        return;
    }
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


document.addEventListener('DOMContentLoaded', () => {
    setupSearch();
    updateChart();
});
