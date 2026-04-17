const containerEl = document.querySelector("[data-container]");
const loadingEl = containerEl.querySelector("[data-loading]");
const errorEl = containerEl.querySelector("[data-error]");
const appEl = containerEl.querySelector("[data-app]");
const summaryEl = containerEl.querySelector("[data-summary]");

const metadataUrls = {
  medications: containerEl.dataset.medicationsUrl,
  dmd: containerEl.dataset.dmdUrl,
  bnf: containerEl.dataset.bnfUrl,
};

const metadata = {};

const loadMetadata = async () => {
  try {
    const [medications, dmd, bnf] = await Promise.all(
      Object.values(metadataUrls).map(async (url) => {
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        return response.json();
      }),
    );

    metadata.medications = medications;
    metadata.dmd = dmd;
    metadata.bnf = bnf;

    renderSummary(metadata);
    loadingEl.hidden = true;
    appEl.hidden = false;
  } catch (error) {
    loadingEl.hidden = true;
    errorEl.textContent = `Unable to load metadata: ${error.message}`;
    errorEl.hidden = false;
  }
};

const renderSummary = (metadata) => {
  const fragment = document.createDocumentFragment();

  Object.entries(metadata).forEach(([endpoint, type]) => {
    const sectionEl = document.createElement("section");
    const headingEl = document.createElement("h2");
    const listEl = document.createElement("ul");

    headingEl.textContent = endpoint;

    Object.entries(type).forEach(([key, value]) => {
      const itemEl = document.createElement("li");
      itemEl.textContent = `${key}: ${value.length}`;
      listEl.appendChild(itemEl);
    });

    sectionEl.append(headingEl, listEl);
    fragment.appendChild(sectionEl);
  });

  summaryEl.replaceChildren(fragment);
};

loadMetadata();
