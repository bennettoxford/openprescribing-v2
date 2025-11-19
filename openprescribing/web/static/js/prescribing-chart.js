const setupSearch = () => {
    const codes = JSON.parse(document.getElementById('bnf-codes').textContent);
    const levels = Object.fromEntries(JSON.parse(document.getElementById('bnf-levels').textContent));
    const search = document.getElementById('bnf-search');
    const results = document.getElementById('bnf-results');

    const navigateWithParams = (updateFn) => {
        const url = new URL(window.location.href);
        updateFn(url.searchParams);
        window.location.href = url.toString();
    };

    createTypeahead({
        input: search,
        results: results,
        minChars: 3,
        getMatches: (query) => codes.filter((c) => c.name.toLowerCase().includes(query)),
        renderItem: (item) => `
            <div class="fw-semibold">${item.name}</div>
            <div class="text-muted small">${item.code} - ${levels[item.level]}</div>
        `,
        onSelect: (item) => {
            navigateWithParams((params) => {
                params.set('code', item.code);
            });
        },
    });
}

const createTypeahead = ({ input, results, minChars, getMatches, renderItem, onSelect }) => {
    if (!input || !results) {
        return;
    }

    input.addEventListener('input', () => {
        const query = input.value.trim().toLowerCase();
        if (query.length < minChars) {
            results.innerHTML = '';
            results.classList.add('d-none');
            return;
        }

        const matches = getMatches(query);
        results.innerHTML = '';
        if (!matches.length) {
            results.classList.add('d-none');
            return;
        }

        const fragment = document.createDocumentFragment();
        matches.forEach((match) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action';
            item.innerHTML = renderItem(match);
            item.addEventListener('click', () => {
                onSelect(match);
            });
            fragment.appendChild(item);
        });
        results.appendChild(fragment);
        results.classList.remove('d-none');
    });
};

const updateChart = () => {
    const chartContainer = document.querySelector('#prescribing-chart');
    if (!chartContainer) {
        return;
    }

    const prescribingApiUrl = JSON.parse(document.getElementById('prescribing-api-url').textContent);

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
