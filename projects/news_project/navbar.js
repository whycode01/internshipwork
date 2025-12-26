class CustomNavbar extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `
        <nav class="bg-white shadow p-4 mb-4">
            <div class="container mx-auto flex justify-between items-center">
                <h1 class="text-xl font-bold text-gray-800">Newsy McSpeaky</h1>
            </div>
        </nav>`;
    }
}
customElements.define("custom-navbar", CustomNavbar);
