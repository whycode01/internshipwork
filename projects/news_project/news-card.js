class NewsCard extends HTMLElement {
    connectedCallback() {
        const title = this.getAttribute("title");
        const source = this.getAttribute("source");

        this.innerHTML = `
            <div class="p-5 bg-white rounded-xl shadow hover:shadow-md transition">
                <h2 class="text-lg font-semibold text-gray-800 mb-2">${title}</h2>
                <p class="text-sm text-gray-600">${source}</p>
            </div>
        `;
    }
}
customElements.define("news-card", NewsCard);
